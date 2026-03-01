import rclpy
from rclpy.node import Node
from rclpy.duration import Duration
from sensor_msgs.msg import LaserScan
from vision_msgs.msg import Detection2DArray
from geometry_msgs.msg import Twist, PoseStamped, PointStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from enum import Enum
import math
import numpy as np
from tf2_ros import Buffer, TransformListener
import tf2_geometry_msgs

# ================= 설정 (Configuration) =================
TARGET_DISTANCE = 0.8        # 목표 거리 (m)
OBSTACLE_CHECK_DIST = 1.0    # 장애물 감지 시작 거리
GOAL_UPDATE_THRESHOLD = 0.5  # Nav2 목표 업데이트 최소 변화량 (m)
CLOSE_PROXIMITY_LIMIT = 0.15 # 너무 가까우면 정지 (m)
MAX_LINEAR_VEL = 0.3         # 최대 직진 속도

# [NEW] PID 및 회전 제한 설정
MAX_ROTATION_SPEED = 0.6     # 초당 최대 회전 속도 (rad/s)
PID_KP = 0.012               # P: 반응 속도를 낮춤 (0.015 -> 0.012)
PID_KI = 0.000               # I: 오버슈트 방지를 위해 제거
PID_KD = 0.02                # D: 댐핑 조절

LIDAR_AVOIDANCE_WEIGHT = 0.4 # 장애물 회피 가중치
NAV2_UPDATE_INTERVAL = 1.0   # Nav2 목표 업데이트 최소 간격 (초)
ANGLE_SMOOTHING_ALPHA = 0.6  # [핵심] 랙 감소를 위해 필터 강도 완화 (0.3 -> 0.6)

class FollowState(Enum):
    WAITING = 0          
    VISUAL_TRACKING = 1  
    BLIND_TRACKING = 2
    MOVING_TO_LAST_POS = 3 
    SEARCHING = 4          

# [NEW] PID 제어기 클래스 추가
class PIDController:
    def __init__(self, kp, ki, kd):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.prev_error = 0.0
        self.integral = 0.0

    def compute(self, error, dt):
        # 적분 (Integral)
        self.integral += error * dt
        # 적분 누적 제한 (Anti-windup)
        self.integral = max(min(self.integral, 20.0), -20.0)
        
        # 미분 (Derivative)
        derivative = (error - self.prev_error) / dt if dt > 0 else 0.0
        self.prev_error = error
        
        # PID 출력 계산
        output = (self.kp * error) + (self.ki * self.integral) + (self.kd * derivative)
        return output

    def reset(self):
        self.integral = 0.0
        self.prev_error = 0.0

class CarterHybridGemini(Node):
    def __init__(self):
        super().__init__('carter_hybrid_gemini')

        # 1. Nav2 & TF
        self.navigator = BasicNavigator()
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        # 2. 파라미터
        self.img_width = 640
        self.camera_fov = 62.2
        self.visual_timeout = 1.0
        self.blind_timeout = 2.0   # [최적화] 시각 소실 후 2초간 라이다 추적 시도 (라이다도 놓치면 즉시 이동)
        
        # 3. 상태 변수
        self.state = FollowState.WAITING
        self.last_visual_time = self.get_clock().now()
        self.last_tracking_time = self.get_clock().now() # [NEW] 시각 or 라이다 추적 성공 시간
        self.target_pos = {'dist': None, 'angle': None} 
        
        # Nav2 제어 변수
        self.last_sent_goal = None 
        self.is_nav2_active = False
        self.last_nav2_req_time = self.get_clock().now()
        
        self.last_known_map_pose = None 

        # [NEW] PID 제어 초기화
        self.pid_controller = PIDController(PID_KP, PID_KI, PID_KD)
        self.last_loop_time = self.get_clock().now()
        self.search_start_time = self.get_clock().now()

        # 4. 통신
        self.create_subscription(Detection2DArray, '/detections', self.yolo_callback, 10)
        self.create_subscription(LaserScan, '/scan', self.scan_callback, 10)
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)

        self.timer = self.create_timer(0.1, self.control_loop)
        self.get_logger().info('>>> [GEMINI Version] PID Controlled Hybrid Tracking Ready')

    def get_robot_pose(self):
        try:
            trans = self.tf_buffer.lookup_transform('map', 'base_link', rclpy.time.Time())
            return trans.transform.translation.x, trans.transform.translation.y
        except: return None, None

    def save_global_target_pose(self):
        dist = self.target_pos['dist']
        angle = self.target_pos['angle']
        if dist is None or angle is None: return

        angle_rad = math.radians(angle)
        x_local = dist * math.cos(angle_rad)
        y_local = dist * math.sin(angle_rad)

        try:
            point_local = PointStamped()
            point_local.header.frame_id = "base_scan"
            point_local.header.stamp = self.get_clock().now().to_msg()
            point_local.point.x = x_local
            point_local.point.y = y_local
            
            # [최적화] TF 타임아웃 단축
            transform = self.tf_buffer.lookup_transform("map", "base_scan", rclpy.time.Time(), rclpy.duration.Duration(seconds=0.05))
            point_map = tf2_geometry_msgs.do_transform_point(point_local, transform)
            
            self.last_known_map_pose = (point_map.point.x, point_map.point.y)
        except Exception:
            pass

    def yolo_callback(self, msg):
        owner_detected = False
        new_angle = 0.0
        
        # YOLO 감지 확인
        for det in msg.detections:
            if int(det.id) >= 1000: # Class ID 확인
                px = det.bbox.center.position.x
                bw = det.bbox.size_x
                new_angle = -((px - (self.img_width / 2)) / self.img_width) * self.camera_fov
                self.target_pos['angle_width'] = (bw / self.img_width) * self.camera_fov
                owner_detected = True
                break
        
        curr_time = self.get_clock().now()
        
        if owner_detected:
            if self.state != FollowState.VISUAL_TRACKING:
                self.pid_controller.reset()
                self.get_logger().info(">>> Owner Re-acquired! PID Reset.")
            
            self.state = FollowState.VISUAL_TRACKING
            self.last_visual_time = curr_time
            self.last_tracking_time = curr_time # [NEW] 추적 성공
            
            # 각도 스무딩 업데이트
            if self.target_pos['angle'] is None:
                self.target_pos['angle'] = new_angle
            else:
                self.target_pos['angle'] = (ANGLE_SMOOTHING_ALPHA * new_angle) + \
                                           ((1.0 - ANGLE_SMOOTHING_ALPHA) * self.target_pos['angle'])
        else:
            if self.state == FollowState.WAITING: return
            
            time_since_visual = (curr_time - self.last_visual_time).nanoseconds / 1e9
            time_since_tracking = (curr_time - self.last_tracking_time).nanoseconds / 1e9
            
            # [로직 변경] 시각 소실 -> 라이다 추적 시도 -> 라이다도 놓치면 이동
            if time_since_visual > self.visual_timeout:
                if self.state == FollowState.VISUAL_TRACKING:
                    self.get_logger().info(">>> 시각 감지 실패. 라이다 추적(Blind) 전환.")
                    self.state = FollowState.BLIND_TRACKING

                # Blind 상태에서도 라이다로 계속 추적 중이면 last_tracking_time이 갱신됨
                # 따라서 last_tracking_time 기준으로 타임아웃을 체크해야 함
                if time_since_tracking > self.blind_timeout:
                    if self.state != FollowState.MOVING_TO_LAST_POS and self.state != FollowState.SEARCHING:
                        self.get_logger().info(">>> 타겟 완전 상실 (Lidar Lost). 마지막 위치로 이동합니다.")
                        self.state = FollowState.MOVING_TO_LAST_POS
                        self.is_nav2_active = False

    def get_lidar_dist_at_angle(self, ranges, angle_deg):
        if angle_deg is None: return None
        idx = int(angle_deg) % 360
        dists = [ranges[i % 360] for i in range(idx-3, idx+4) if 0.1 < ranges[i % 360] < 10.0]
        if dists: return min(dists)
        return None
    
    def get_front_min_dist(self, ranges):
        front_dists = [ranges[i] for i in list(range(0, 20)) + list(range(340, 360)) if 0.1 < ranges[i] < 10.0]
        if front_dists: return min(front_dists)
        return 999.0

    def find_nearest_neighbor(self, ranges):
        last_angle = self.target_pos['angle']
        last_dist = self.target_pos['dist']
        if last_angle is None or last_dist is None: return None, None
        
        search_range = 30 # ±30도 탐색
        best_angle, min_diff = None, 999.0
        
        for i in range(int(last_angle)-search_range, int(last_angle)+search_range):
            d = ranges[i % 360]
            if not (0.1 < d < 10.0): continue
            diff = abs(d - last_dist)
            
            if diff < min_diff and diff < 0.5:
                min_diff = diff
                best_angle = float(i)
                if best_angle > 180: best_angle -= 360
                
        if best_angle is not None:
            return best_angle, ranges[int(best_angle)%360]
        return None, None

    def calculate_potential_field_cmd(self, ranges, target_angle, target_dist):
        # 1. 인력 (Target)
        attract_x = math.cos(math.radians(target_angle))
        attract_y = math.sin(math.radians(target_angle))

        # 2. 척력 (Obstacle)
        repulse_x, repulse_y = 0.0, 0.0
        num_points = 0
        
        for i in range(-60, 61): # 전방 120도 감시
            idx = i % 360
            dist = ranges[idx]
            # [최종 튜닝] 70cm 협소 구간 통과를 위해 감지 범위를 0.6m로 대폭 축소
            # 70cm 길의 중앙으로 가면 기둥과의 거리는 0.35m이므로, 0.6m부터 반응하는 것이 적당함
            if 0.15 < dist < 0.6: 
                force = (0.6 - dist) ** 2
                
                # 정면 장애물은 강하게 피하고, 측면 장애물은 흘려보냄
                angle_weight = max(0.1, 1.0 - (abs(i) / 70.0))
                
                angle_rad = math.radians(i)
                repulse_x -= math.cos(angle_rad) * force * angle_weight
                repulse_y -= math.sin(angle_rad) * force * angle_weight
                num_points += 1
        
        if num_points > 0:
            repulse_x *= LIDAR_AVOIDANCE_WEIGHT
            repulse_y *= LIDAR_AVOIDANCE_WEIGHT

        # 3. 합력
        final_x = attract_x + repulse_x
        final_y = attract_y + repulse_y
        
        desired_angle = math.degrees(math.atan2(final_y, final_x))
        risk_level = math.sqrt(repulse_x**2 + repulse_y**2)
        
        return desired_angle, risk_level

    def scan_callback(self, msg):
        self.current_ranges = msg.ranges
        
        # [최적화] 데이터 튐 방지 및 윈도우 탐색
        if self.state == FollowState.VISUAL_TRACKING:
            angle = self.target_pos.get('angle')
            angle_w = self.target_pos.get('angle_width', 10.0)
            
            if angle is not None:
                # 사람의 전체 폭 내에서 가장 가까운 물체를 찾음
                search_range = max(5, int(angle_w / 2) + 2)
                idx = int(angle) % 360
                
                valid_dists = []
                for i in range(idx - search_range, idx + search_range + 1):
                    d = msg.ranges[i % 360]
                    if 0.15 < d < 5.0:
                        valid_dists.append(d)
                
                if valid_dists:
                    new_dist = min(valid_dists)
                    # 거리 급변 방지 (이동 평균)
                    if self.target_pos['dist'] is None:
                        self.target_pos['dist'] = new_dist
                    else:
                        self.target_pos['dist'] = 0.7 * new_dist + 0.3 * self.target_pos['dist']
                else:
                    # 라이다로 직접 안 잡히면 주변 탐색 시도
                    na, nd = self.find_nearest_neighbor(msg.ranges)
                    if na is not None:
                        self.target_pos['dist'] = nd

        elif self.state == FollowState.BLIND_TRACKING:
            na, nd = self.find_nearest_neighbor(msg.ranges)
            if na is not None:
                self.target_pos['angle'] = na
                self.target_pos['dist'] = nd
                self.last_tracking_time = self.get_clock().now() # [NEW] 라이다 추적 성공 시 시간 갱신

    def drive_to_last_pose_manual(self):
        """Nav2 없이 마지막 위치로 이동 (장애물 회피 + PID)"""
        gx, gy = self.last_known_map_pose
        rx, ry = self.get_robot_pose()
        if rx is None: return False

        dx, dy = gx - rx, gy - ry
        dist = math.sqrt(dx**2 + dy**2)
        
        # 1. 도착 확인
        if dist < 0.5: 
            self.cmd_pub.publish(Twist()) # 정지 (linear=0, angular=0)
            return True

        # 2. 목표 각도 계산 (Map frame -> Robot frame)
        # 로봇의 현재 헤딩(Yaw) 구하기
        try:
            trans = self.tf_buffer.lookup_transform('map', 'base_link', rclpy.time.Time())
            q = trans.transform.rotation
            _, _, ryaw = tf2_geometry_msgs.tf2_geometry_msgs.transformations.euler_from_quaternion([q.x, q.y, q.z, q.w])
        except:
            # TF 실패시 대충 0으로 가정하거나 리턴
            # 여기서는 간단히 atan2(dy, dx)를 바로 쓰기 어려우므로 TF 필수
            # 하지만 get_robot_pose에서 TF를 이미 썼으므로 쿼터니언 변환만 하면 됨.
            # 복잡하면 그냥 atan2(dy, dx) - current_yaw 로 계산해야 함.
            # 일단 약식으로 구현: get_robot_pose를 수정하거나 여기서 다시 TF 조회
            return False 

        # 로봇 Yaw 다시 조회 (정확성을 위해)
        try:
            t = self.tf_buffer.lookup_transform('map', 'base_link', rclpy.time.Time())
            q = t.transform.rotation
            # 쿼터니언 -> 오일러 (Roll, Pitch, Yaw)
            siny_cosp = 2 * (q.w * q.z + q.x * q.y)
            cosy_cosp = 1 - 2 * (q.y * q.y + q.z * q.z)
            curr_yaw = math.atan2(siny_cosp, cosy_cosp)
        except: return False

        target_angle_map = math.atan2(dy, dx)
        angle_diff_rad = target_angle_map - curr_yaw
        
        # -PI ~ PI 정규화
        while angle_diff_rad > math.pi: angle_diff_rad -= 2*math.pi
        while angle_diff_rad < -math.pi: angle_diff_rad += 2*math.pi
        
        target_angle_deg = math.degrees(angle_diff_rad)

        # 3. 장애물 회피 (Potential Field)
        # 현재 Lidar 정보를 이용해서 로컬 장애물 회피
        desired_angle, risk = self.calculate_potential_field_cmd(self.current_ranges, target_angle_deg, dist)
        
        # 4. PID 주행
        twist = Twist()
        now = self.get_clock().now()
        dt = (now - self.last_loop_time).nanoseconds / 1e9
        if dt <= 0: dt = 0.1
        self.last_loop_time = now

        angular_output = self.pid_controller.compute(desired_angle, dt)
        twist.angular.z = max(min(angular_output, MAX_ROTATION_SPEED), -MAX_ROTATION_SPEED)

        # 직진 (장애물/회전 시 감속)
        speed_factor = max(0.2, 1.0 - (abs(desired_angle) / 60.0))
        if risk > 0.5: speed_factor *= 0.5
        
        twist.linear.x = min(0.25, dist * 0.5) * speed_factor # 거리에 비례하여 감속
        
        self.cmd_pub.publish(twist)
        return False

    def drive_smart_direct(self):
        """[핵심] PID가 적용된 직진 및 회피 주행"""
        twist = Twist()
        dist = self.target_pos['dist']
        raw_angle = self.target_pos['angle']
        if dist is None or raw_angle is None: return True

        # Potential Field로 목표 각도 계산 (장애물 회피 포함)
        desired_angle, risk = self.calculate_potential_field_cmd(self.current_ranges, raw_angle, dist)

        # 위험도가 너무 높으면 Nav2에게 넘김 (좁은 통로 통과를 위해 허용치 완화)
        if risk > 2.0: 
            return False 

        # =========================================================
        # [NEW] PID를 이용한 회전 속도 계산 및 제한
        # =========================================================
        # 1. dt 계산
        now = self.get_clock().now()
        dt = (now - self.last_loop_time).nanoseconds / 1e9
        if dt <= 0: dt = 0.1
        self.last_loop_time = now

        # 2. PID 계산 (목표 각도로 가기 위한 회전 속도 산출)
        # [NEW] Deadband (불감대) 확장: 3.0 -> 6.0도
        # 딜레이나 노이즈로 인한 미세 진동을 잡기 위해 중앙 허용 범위를 넓힘
        if abs(desired_angle) < 6.0:
            angular_output = 0.0
            self.pid_controller.reset() # 멈췄을 때 적분항 초기화하여 튀는 것 방지
        else:
            angular_output = self.pid_controller.compute(desired_angle, dt)

        # 3. 속도 제한 (Clamp): 설정된 MAX_ROTATION_SPEED를 넘지 않도록 자름
        twist.angular.z = max(min(angular_output, MAX_ROTATION_SPEED), -MAX_ROTATION_SPEED)

        # 4. 직진 속도 제어
        dist_error = dist - TARGET_DISTANCE
        
        # 회전 중이거나 장애물이 있으면 감속
        speed_factor = max(0.2, 1.0 - (abs(desired_angle) / 60.0))
        if risk > 0.5: speed_factor *= 0.5
        
        if dist_error > 0:
            target_vel = min(dist_error * 0.5, MAX_LINEAR_VEL)
            twist.linear.x = target_vel * speed_factor
        else:
            twist.linear.x = 0.0 
            
        self.cmd_pub.publish(twist)
        return True 

    def drive_nav2(self):
        """Nav2 경로 생성 요청"""
        self.save_global_target_pose() 

        now = self.get_clock().now()
        if (now - self.last_nav2_req_time).nanoseconds / 1e9 < NAV2_UPDATE_INTERVAL:
            return

        dist = self.target_pos['dist']
        angle = self.target_pos['angle']
        if dist is None or angle is None: return
        
        angle_rad = math.radians(angle)
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
            
            px, py = point_map.point.x, point_map.point.y
            rx, ry = self.get_robot_pose()
            if rx is None: return

            dx, dy = px - rx, py - ry
            person_dist = math.sqrt(dx**2 + dy**2)

            if person_dist < TARGET_DISTANCE:
                return 

            ux, uy = dx / person_dist, dy / person_dist
            gx = px - (TARGET_DISTANCE * ux)
            gy = py - (TARGET_DISTANCE * uy)

            should_send = True
            if self.last_sent_goal:
                lx, ly = self.last_sent_goal
                if math.sqrt((gx-lx)**2 + (gy-ly)**2) < GOAL_UPDATE_THRESHOLD:
                    should_send = False
            
            if should_send:
                goal = PoseStamped()
                goal.header.frame_id = 'map'
                goal.header.stamp = self.navigator.get_clock().now().to_msg()
                goal.pose.position.x = gx
                goal.pose.position.y = gy
                yaw = math.atan2(dy, dx)
                goal.pose.orientation.z = math.sin(yaw/2)
                goal.pose.orientation.w = math.cos(yaw/2)
                
                self.navigator.goToPose(goal)
                self.last_sent_goal = (gx, gy)
                self.last_nav2_req_time = now

        except Exception: pass

    def control_loop(self):
        if not hasattr(self, 'current_ranges'): return

        # ============ 1. 추적 모드 (Visual / Blind) ============
        if self.state in [FollowState.VISUAL_TRACKING, FollowState.BLIND_TRACKING]:
            self.save_global_target_pose()

            if self.is_nav2_active:
                # [A] Nav2 활성 상태
                front_min = self.get_front_min_dist(self.current_ranges)
                
                if front_min > 1.5: 
                    self.get_logger().info(">>> 장애물 해소. 수동 모드 전환")
                    self.navigator.cancelTask()
                    self.is_nav2_active = False
                    return # 충돌 방지를 위해 한 턴 쉼
                else:
                    self.drive_nav2()
                    return 

            # [B] 수동 제어 상태 (PID 적용됨)
            if not self.is_nav2_active:
                success = self.drive_smart_direct()
                if not success:
                    self.get_logger().warn(">>> [경로 막힘] Nav2 활성화")
                    self.is_nav2_active = True
                    self.drive_nav2() 

        # ============ 2. 복구 모드 (Target Lost) ============
        elif self.state == FollowState.MOVING_TO_LAST_POS:
            if self.last_known_map_pose is None:
                self.state = FollowState.SEARCHING
                self.search_start_time = self.get_clock().now()
                return

            # [Manual Fallback] Nav2 없이 직접 이동 (장애물 회피 포함)
            arrived = self.drive_to_last_pose_manual()
            if arrived:
                self.get_logger().info(">>> 마지막 위치 도착. 탐색 모드 전환")
                self.state = FollowState.SEARCHING
                self.search_start_time = self.get_clock().now()

        # ============ 3. 탐색 모드 (Searching) ============
        elif self.state == FollowState.SEARCHING:
            if self.is_nav2_active:
                self.navigator.cancelTask()
                self.is_nav2_active = False
            
            # [NEW] 20초간 회전 후 대기 모드 전환
            elapsed = (self.get_clock().now() - self.search_start_time).nanoseconds / 1e9
            if elapsed > 20.0:
                self.get_logger().info(">>> 탐색 시간 초과. 제자리 대기 모드(WAITING)로 전환.")
                self.state = FollowState.WAITING
                self.cmd_pub.publish(Twist()) # 정지
                return

            twist = Twist()
            twist.linear.x = 0.0 # [중요] 제자리 회전을 위해 선속도 0
            twist.angular.z = 0.4 # [최적화] 천천히 돌며 꼼꼼히 탐색
            self.cmd_pub.publish(twist)

        # ============ 4. 대기 모드 (Waiting) ============
        elif self.state == FollowState.WAITING:
            if self.is_nav2_active:
                self.navigator.cancelTask()
                self.is_nav2_active = False
            self.cmd_pub.publish(Twist())

def main():
    rclpy.init()
    node = CarterHybridGemini()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()