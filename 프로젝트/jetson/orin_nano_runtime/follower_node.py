import rclpy
from rclpy.node import Node
from rclpy.duration import Duration
from rclpy.action import ActionClient
from rclpy.qos import QoSProfile, QoSPresetProfiles
from sensor_msgs.msg import LaserScan
from vision_msgs.msg import Detection2DArray
from geometry_msgs.msg import Twist, PoseStamped, PointStamped
from nav_msgs.msg import OccupancyGrid
from std_msgs.msg import String
from nav2_msgs.action import ComputePathToPose
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from enum import Enum
import math
import numpy as np
from tf2_ros import Buffer, TransformListener, LookupException, ConnectivityException, ExtrapolationException
import tf2_geometry_msgs

# ================= Configuration =================
# 🟢 추적 설정 (팔로워 모드)
TARGET_DISTANCE = 0.5        # 목표 거리 (m) — 낮을수록 더 가까이서 추적 (0.5~1.0)
OBSTACLE_CHECK_DIST = 0.5    # 장애물 감지 시작 거리
CLOSE_PROXIMITY_LIMIT = 0.10 # 비상 정지 거리 (충돌 방지)

# 🟢 직진/회전 속도 조정 (키워드 SLAM/추적에서 조정 가능)
MAX_LINEAR_VEL = 0.35        # 최대 직진 속도 (m/s) — 0.2~0.4 추천 (낮을수록 부드러움)
MAX_ROTATION_SPEED = 0.6     # 최대 회전 속도 (rad/s) — 0.3~0.6 추천 (65cm 통로용 보수적)

# 🟢 PID 제어 (회전 각도 제어)
PID_KP = 0.5                 # P 게인 (0.4~0.7 추천) — 높을수록 빠르게 반응
PID_KI = 0.0                 # I 게인 (적분) — 보통 0
PID_KD = 0.03                # D 게인 (미분) — 진동 억제

# 🟢 안정성 파라미터
ROTATION_DEADBAND = 8.0      # 데드밴드 (±도 이내는 회전 안 함, 직진 중심)
LIDAR_AVOIDANCE_WEIGHT = 0.4 # 장애물 회피 가중치 (0.2~0.6, 낮을수록 우선 추적)
ANGLE_SMOOTHING_ALPHA = 0.4  # 스무딩 (0.2~0.5, 낮을수록 진동 적음)

class FollowState(Enum):
    WAITING = 0
    VISUAL_TRACKING = 1
    BLIND_TRACKING = 2
    RECOVERY = 3
    SEARCHING = 4

class PIDController:
    def __init__(self, kp, ki, kd):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.prev_error = 0.0

    def compute(self, error, dt):
        derivative = (error - self.prev_error) / dt if dt > 0 else 0.0
        self.prev_error = error
        return (self.kp * error) + (self.kd * derivative)

    def reset(self):
        self.prev_error = 0.0

class CarterFollower(Node):
    def __init__(self):
        super().__init__('carter_follower')

        # 1. Nav2 & TF
        self.navigator = BasicNavigator()
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        # 2. Parameters
        self.img_width = 640
        self.camera_fov = 62.2
        self.visual_timeout = 1.0  # 너무 짧으면 불안정하므로 1.0초로 복구
        self.blind_timeout = 3.0
        # 파라미터 동접 로드 (런치 파일에서 override 가능)
        self.declare_parameter('max_linear_vel', MAX_LINEAR_VEL)
        self.declare_parameter('max_rotation_speed', MAX_ROTATION_SPEED)
        self.declare_parameter('target_distance', TARGET_DISTANCE)

        # 3. State Variables
        self.current_system_mode = "IDLE"  # [이식] 시스템 모드 저장 변수
        self.state = FollowState.WAITING
        self.last_visual_time = self.get_clock().now()
        self.target_pos = {'dist': None, 'angle': None, 'angle_width': 10.0}

        # Map Data
        self.map_data = None
        self.map_info = None

        # Logic Control
        self.pid_controller = PIDController(PID_KP, PID_KI, PID_KD)
        self.last_loop_time = self.get_clock().now()
        self.last_known_map_pose = None
        self.recovery_start_time = None

        # 4. Communication
        # 부드러운 주행을 위해 Reliable도 괜찮지만, 최신성 유지를 위해 SensorData 유지
        qos_policy = QoSPresetProfiles.SENSOR_DATA.value

        self.create_subscription(Detection2DArray, '/detections', self.yolo_callback, qos_policy)
        self.create_subscription(LaserScan, '/scan', self.scan_callback, qos_policy)
        self.create_subscription(OccupancyGrid, '/map', self.map_callback, 10)
        self.create_subscription(String, '/robot/mode', self.mode_callback, 10) # 모드 구독 추가
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)

        self.timer = self.create_timer(0.1, self.control_loop) # 10Hz (너무 빠르면 진동 유발, 20Hz -> 10Hz)
        self.get_logger().info('>>> Carter Hybrid Follower (Smooth & Stable) Ready')
        self.get_logger().info(f'  - MAX_LINEAR_VEL: {MAX_LINEAR_VEL} m/s')
        self.get_logger().info(f'  - MAX_ROTATION_SPEED: {MAX_ROTATION_SPEED} rad/s')
        self.get_logger().info(f'  - PID_KP: {PID_KP}')

        # [추가] 자동 초기 위치 설정 (2D Pose Estimate 자동화)
        # Gazebo에서 스폰한 위치와 동일하게 맞춰주세요!
        # 아까 설정한 값: x=1.4, y=1.46, yaw=-1.57 (남쪽)
        self.set_initial_pose(x=1.4, y=1.46, z=0.01, yaw=-1.57)
    # [추가] 초기 위치 설정 함수
    def set_initial_pose(self, x, y, z, yaw):
        self.get_logger().info(f">>> [Auto-Init] 초기 위치 설정 중... (x={x}, y={y}, yaw={yaw})")
        
        # 1. PoseStamped 메시지 생성
        initial_pose = PoseStamped()
        initial_pose.header.frame_id = 'map'
        initial_pose.header.stamp = self.navigator.get_clock().now().to_msg()
        initial_pose.pose.position.x = x
        initial_pose.pose.position.y = y
        initial_pose.pose.position.z = z
        
        # 2. Yaw(각도)를 Quaternion으로 변환
        # (수학 공식이므로 그대로 복사해서 쓰시면 됩니다)
        cy = math.cos(yaw * 0.5)
        sy = math.sin(yaw * 0.5)
        cp = math.cos(0.0)
        sp = math.sin(0.0)
        cr = math.cos(0.0)
        sr = math.sin(0.0)

        initial_pose.pose.orientation.w = cy * cp * cr + sy * sp * sr
        initial_pose.pose.orientation.x = cy * cp * sr - sy * sp * cr
        initial_pose.pose.orientation.y = sy * cp * sr + cy * sp * cr
        initial_pose.pose.orientation.z = sy * cp * cr - cy * sp * sr

        # 3. Nav2에게 초기 위치 전달 (/initialpose 발행)
        self.navigator.setInitialPose(initial_pose)
        
        # [중요] AMCL이 입자를 뿌릴 시간을 잠깐 줍니다.
        # (바로 다음 명령을 내리면 초기화가 씹힐 수 있음)
        # rclpy.spin_once 등으로 대기하거나, 그냥 타임슬립을 줘도 됩니다.
        # 여기서는 단순히 명령만 보내고 넘어갑니다.
        

    def mode_callback(self, msg):
        mode = msg.data.upper()
        self.current_system_mode = mode # 모드 상태 업데이트

        if mode == "FOLLOW":
            if self.state == FollowState.WAITING:
                self.get_logger().info(">>> Follower Active!")
                self.state = FollowState.SEARCHING # 혹은 주인을 찾기 위해 서칭부터 시작
                self.search_start_time = self.get_clock().now()
        elif mode == "STOP" or mode == "NAV":
            self.state = FollowState.WAITING
            # NAV 모드일 때는 정지 명령을 보내지 않음 (Nav2 충돌 방지)
            if mode == "STOP":
                self.cmd_pub.publish(Twist()) # 즉시 정지

    def map_callback(self, msg):
        self.map_info = msg.info
        self.map_data = np.array(msg.data, dtype=np.int8).reshape((msg.info.height, msg.info.width))

    def is_static_obstacle(self, dist, angle_deg):
        if self.map_data is None or self.map_info is None: return False

        angle_rad = math.radians(angle_deg)
        x_local = dist * math.cos(angle_rad)
        y_local = dist * math.sin(angle_rad)

        try:
            point_local = PointStamped()
            point_local.header.frame_id = "base_scan"
            point_local.header.stamp = self.get_clock().now().to_msg()
            point_local.point.x = x_local
            point_local.point.y = y_local

            transform = self.tf_buffer.lookup_transform("map", "base_scan", rclpy.time.Time(), rclpy.duration.Duration(seconds=0.05))
            point_map = tf2_geometry_msgs.do_transform_point(point_local, transform)

            resolution = self.map_info.resolution
            origin_x = self.map_info.origin.position.x
            origin_y = self.map_info.origin.position.y

            mx = int((point_map.point.x - origin_x) / resolution)
            my = int((point_map.point.y - origin_y) / resolution)

            if 0 <= mx < self.map_info.width and 0 <= my < self.map_info.height:
                if self.map_data[my, mx] > 50: return True
            return False
        except Exception:
            return False

    def yolo_callback(self, msg):

        if self.current_system_mode != "FOLLOW":
            return

        owner_detected = False
        new_angle = 0.0

        for det in msg.detections:
            if int(det.id) >= 1000:
                px = det.bbox.center.position.x
                bw = det.bbox.size_x
                new_angle = -((px - (self.img_width / 2)) / self.img_width) * self.camera_fov
                new_width = (bw / self.img_width) * self.camera_fov
                owner_detected = True
                self.target_pos['angle_width'] = new_width
                break

        curr_time = self.get_clock().now()

        if owner_detected:
            if self.state in [FollowState.RECOVERY, FollowState.SEARCHING, FollowState.WAITING]:
                self.get_logger().info(">>> 타겟 발견! 부드러운 추적 시작.")
                self.navigator.cancelTask()
                self.pid_controller.reset()

            self.state = FollowState.VISUAL_TRACKING
            self.last_visual_time = curr_time

            # [Smooth] 지수 이동 평균(EMA) 필터 적용 (노이즈 제거)
            if self.target_pos['angle'] is None:
                self.target_pos['angle'] = new_angle
            else:
                self.target_pos['angle'] = (ANGLE_SMOOTHING_ALPHA * new_angle) + \
                                           ((1.0 - ANGLE_SMOOTHING_ALPHA) * self.target_pos['angle'])
        else:
            if self.state == FollowState.WAITING: return
            time_diff = (curr_time - self.last_visual_time).nanoseconds / 1e9

            if time_diff > self.blind_timeout:
                if self.state != FollowState.RECOVERY and self.state != FollowState.SEARCHING:
                    self.get_logger().warn(">>> 타겟 소실. Nav2 Recovery 시작.")
                    self.state = FollowState.RECOVERY
                    self.recovery_start_time = curr_time
                    self.navigator.cancelTask()
                    self.execute_recovery_nav2()
            elif time_diff > self.visual_timeout:
                self.state = FollowState.BLIND_TRACKING

    def scan_callback(self, msg):
        self.current_ranges = msg.ranges

        if self.state == FollowState.VISUAL_TRACKING:
            angle = self.target_pos.get('angle')
            angle_w = self.target_pos.get('angle_width', 10.0)

            if angle is not None:
                search_range = max(5, int(angle_w / 2) + 2)
                idx = int(angle) % 360

                valid_dists = []
                for i in range(idx - search_range, idx + search_range + 1):
                    d = msg.ranges[i % 360]
                    if 0.15 < d < 8.0:
                        if not self.is_static_obstacle(d, float(i)):
                            valid_dists.append(d)

                if valid_dists:
                    # 거리값도 부드럽게 필터링
                    raw_dist = min(valid_dists)
                    if self.target_pos['dist'] is None:
                        self.target_pos['dist'] = raw_dist
                    else:
                        self.target_pos['dist'] = 0.7 * raw_dist + 0.3 * self.target_pos['dist']
                else:
                    na, nd = self.find_nearest_neighbor(msg.ranges)
                    if na is not None: self.target_pos['dist'] = nd

        elif self.state == FollowState.BLIND_TRACKING:
            na, nd = self.find_nearest_neighbor(msg.ranges)
            if na is not None:
                self.target_pos['angle'] = na
                self.target_pos['dist'] = nd

    def find_nearest_neighbor(self, ranges):
        last_angle = self.target_pos['angle']
        last_dist = self.target_pos['dist']
        if last_angle is None or last_dist is None: return None, None

        search_range = 30 # 검색 범위 축소 (오인식 방지)
        best_angle, min_diff = None, 999.0

        start = int(last_angle) - search_range
        end = int(last_angle) + search_range

        for i in range(start, end):
            d = ranges[i % 360]
            if not (0.1 < d < 10.0): continue
            if self.is_static_obstacle(d, float(i)): continue

            diff = abs(d - last_dist)
            if diff < min_diff and diff < 0.5: # 0.5m 이내만 인정
                min_diff = diff
                best_angle = float(i)
                if best_angle > 180: best_angle -= 360

        if best_angle is not None:
            return best_angle, ranges[int(best_angle)%360]
        return None, None

    def calculate_potential_field(self, target_angle, target_dist):
        # Attraction
        attract_x = math.cos(math.radians(target_angle)) * 2.0
        attract_y = math.sin(math.radians(target_angle)) * 2.0

        # Repulsion
        repulse_x, repulse_y = 0.0, 0.0
        if hasattr(self, 'current_ranges'):
            for i in range(-50, 51): # 전방 100도
                d = self.current_ranges[i % 360]
                if 0.1 < d < OBSTACLE_CHECK_DIST:
                    force = (OBSTACLE_CHECK_DIST - d) ** 2
                    rad = math.radians(i)
                    repulse_x -= math.cos(rad) * force
                    repulse_y -= math.sin(rad) * force

        total_x = attract_x + (repulse_x * LIDAR_AVOIDANCE_WEIGHT)
        total_y = attract_y + (repulse_y * LIDAR_AVOIDANCE_WEIGHT)

        return math.degrees(math.atan2(total_y, total_x))

    def drive_direct(self):
        if self.target_pos['dist'] is None or self.target_pos['angle'] is None: return

        # 1. 목표 각도 계산
        target_angle_corr = self.calculate_potential_field(self.target_pos['angle'], self.target_pos['dist'])
        
        # [수정] Deadband 삭제 또는 아주 작게 (정밀한 회전을 위해)
        # if abs(target_angle_corr) < ROTATION_DEADBAND: target_angle_corr = 0.0

        now = self.get_clock().now()
        dt = (now - self.last_loop_time).nanoseconds / 1e9
        if dt <= 0: dt = 0.1
        self.last_loop_time = now

        # 2. 회전 속도 (Angular Velocity)
        error_rad = math.radians(target_angle_corr)
        angular_z = self.pid_controller.compute(error_rad, dt)
        
        # [복구] 회전 속도 제한을 0.5 -> 1.0 (또는 1.5)로 늘려서 답답하지 않게
        MAX_ROT_SPEED = 1.0 
        angular_z = max(min(angular_z, MAX_ROT_SPEED), -MAX_ROT_SPEED)

        # 3. 직진 속도 (Linear Velocity) - [여기가 핵심!]
        dist_error = self.target_pos['dist'] - TARGET_DISTANCE
        linear_x = 0.0
        
        # 전방 장애물 확인
        front_min = min([self.current_ranges[i] for i in range(-15, 16) if 0.1 < self.current_ranges[i%360] < 10.0], default=9.9)

        # [핵심 로직] "Pivot Turn" 구현
        # 목표 각도가 20도 이상 틀어져 있으면 -> 직진 금지 (제자리 회전)
        if abs(target_angle_corr) > 20.0:
            linear_x = 0.0 
        elif front_min < 0.28: # 아까 수정한 좁은 길 허용 거리
            linear_x = 0.0
        elif dist_error > 0:
            # 각도가 작을 때만 직진 속도를 냄
            linear_x = min(dist_error * 0.5, MAX_LINEAR_VEL)

        twist = Twist()
        twist.linear.x = linear_x
        twist.angular.z = angular_z
        self.cmd_pub.publish(twist)

    def execute_recovery_nav2(self):
        self.save_global_target_pose()

        if self.last_known_map_pose:
            gx, gy = self.last_known_map_pose
            self.get_logger().info(f">>> [RECOVERY] Nav2 Goal: ({gx:.2f}, {gy:.2f})")

            goal = PoseStamped()
            goal.header.frame_id = 'map'
            goal.header.stamp = self.navigator.get_clock().now().to_msg()
            goal.pose.position.x = gx
            goal.pose.position.y = gy
            goal.pose.orientation.w = 1.0

            self.navigator.goToPose(goal)
        else:
            self.state = FollowState.SEARCHING

    def save_global_target_pose(self):
        dist = self.target_pos['dist']
        angle = self.target_pos['angle']
        if dist is None or angle is None: return

        angle_rad = math.radians(angle)
        x_local = dist * math.cos(angle_rad)
        y_local = dist * math.sin(angle_rad)
        try:
            trans = self.tf_buffer.lookup_transform("map", "base_scan", rclpy.time.Time())
            q = trans.transform.rotation
            siny_cosp = 2 * (q.w * q.z + q.x * q.y)
            cosy_cosp = 1 - 2 * (q.y * q.y + q.z * q.z)
            yaw = math.atan2(siny_cosp, cosy_cosp)

            mx = trans.transform.translation.x + (x_local * math.cos(yaw) - y_local * math.sin(yaw))
            my = trans.transform.translation.y + (x_local * math.sin(yaw) + y_local * math.cos(yaw))

            self.last_known_map_pose = (mx, my)
        except Exception: pass

    def control_loop(self):
        if self.state in [FollowState.VISUAL_TRACKING, FollowState.BLIND_TRACKING]:
            self.save_global_target_pose()
            self.drive_direct()

        elif self.state == FollowState.RECOVERY:
            if self.navigator.isTaskComplete():
                result = self.navigator.getResult()
                if result == TaskResult.SUCCEEDED:
                    self.get_logger().info(">>> 복구 완료. 탐색 시작.")
                elif result == TaskResult.FAILED:
                    self.get_logger().warn(">>> 복구 실패 (경로 막힘). 탐색 시작.")
                self.state = FollowState.SEARCHING

        elif self.state == FollowState.SEARCHING:
            twist = Twist()
            twist.angular.z = 0.0 # 천천히 회전
            self.cmd_pub.publish(twist)

        elif self.state == FollowState.WAITING:
            if self.current_system_mode != "NAV":
                self.cmd_pub.publish(Twist())

def main():
    rclpy.init()
    node = CarterFollower()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
