import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped
from std_msgs.msg import String
from nav2_msgs.action import NavigateThroughPoses
import yaml
import subprocess
import os
import signal
import sys
import json

# =============================================================================
# [1] 추적 주행 관리자 (Subprocess Manager)
# =============================================================================
class FollowerManager:
    def __init__(self, logger):
        self.logger = logger
        self.detector_process = None
        self.follower_process = None
        self.base_path = os.path.dirname(os.path.abspath(__file__))

    def start_once(self):
        """시스템 시작 시 노드들을 한 번만 실행 (메모리 상주)"""
        if self.is_running():
            return

        self.logger.info(">>> Loading Follower System into Memory (One-time load)...")
        ros_args = ['--ros-args', '-p', 'use_sim_time:=true']
        
        det_script = os.path.join(self.base_path, 'detector_node.py')
        self.detector_process = subprocess.Popen([sys.executable, det_script] + ros_args, cwd=self.base_path)

        ctrl_script = os.path.join(self.base_path, 'follower_node.py')
        self.follower_process = subprocess.Popen([sys.executable, ctrl_script] + ros_args, cwd=self.base_path)

    def stop_all(self):
        """전체 시스템 종료 시 호출"""
        self.logger.info(">>> Clearing Follower System from Memory...")
        for p in [self.follower_process, self.detector_process]:
            if p:
                p.send_signal(signal.SIGINT)
                try: p.wait(timeout=2)
                except: p.kill()

    def is_running(self):
        return (self.detector_process is not None) or (self.follower_process is not None)


# =============================================================================
# [2] 통합 컨트롤러 노드 (Main Controller) - waypoint_navigator.py 기반 수정
# =============================================================================
class RobotController(Node):
    def __init__(self):
        super().__init__('robot_master_controller')
        
        # 시뮬레이션 시간 설정 (waypoint_navigator.py와 동일)
        try:
            self.declare_parameter('use_sim_time', True)
        except:
            pass
        
        self.get_logger().info(">>> Robot Master Controller Started")
        
        # 1. 매니저 초기화 및 노드 즉시 로드
        self.follower_manager = FollowerManager(self.get_logger())
        self.follower_manager.start_once() 
        self.current_mode = "IDLE"
        
        # 2. Nav2 설정 (waypoint_navigator.py와 동일)
        self.init_pose_pub = self.create_publisher(PoseWithCovarianceStamped, '/initialpose', 10)
        self.status_pub = self.create_publisher(String, '/robot/status', 10)
        self.nav_client = ActionClient(self, NavigateThroughPoses, 'navigate_through_poses')
        
        # 3. 통신 설정
        self.create_subscription(String, '/robot/destination', self.goal_callback, 10) # destination_callback -> goal_callback 변경
        self.create_subscription(String, '/robot/mode', self.mode_callback, 10)
        self.create_subscription(String, '/robot/set_init_pose', self.init_callback, 10) # init_pose_callback -> init_callback 변경

        # [NEW] 위치 정보 발행 설정
        self.current_pose_pub = self.create_publisher(String, '/robot/current_pose', 10)
        self.create_subscription(PoseWithCovarianceStamped, '/amcl_pose', self.pose_callback, 10)

        self.goal_handle = None # waypoint_navigator.py와 동일

    # -------------------------------------------------------------------------
    # [Callback] 모드 변경 (/robot/mode)
    # -------------------------------------------------------------------------
    def mode_callback(self, msg):
        req_mode = msg.data.upper()
        if req_mode == self.current_mode: return
        self.get_logger().info(f"Mode Switch: {self.current_mode} -> {req_mode}")

        if req_mode == "STOP":
            if self.goal_handle:
                self.get_logger().info("주행 중지 요청 수신")
                self.goal_handle.cancel_goal_async()
            self.status_pub.publish(String(data="ROBOT_STOPPED"))

        self.current_mode = req_mode
        self.status_pub.publish(String(data=f"ACK_{req_mode}"))

    # -------------------------------------------------------------------------
    # [Callback] Nav2 목적지 수신 (/robot/destination) - goal_callback
    # -------------------------------------------------------------------------
    def goal_callback(self, msg):
        # NAV 모드로 자동 전환
        self.current_mode = "NAV"
        try:
            self.get_logger().info(f"[DEBUG] Raw Destination Message: {msg.data}") # [DEBUG] 수신 데이터 원본 확인
            payload = yaml.safe_load(msg.data)
            if payload.get('command') != 'navigate_waypoints':
                self.get_logger().warn(f"[DEBUG] Unknown command: {payload.get('command')}") # [DEBUG] 명령어 불일치 경고
                return

            waypoints = payload.get('waypoints', [])
            
            print("\n" + "="*50)
            print(f" [Vue 명령 수신] 총 {len(waypoints)}개의 경유지")
            for i, wp in enumerate(waypoints):
                print(f"  - WP {i+1}: ({wp['x']}, {wp['y']})")
            print("="*50 + "\n")

            self.send_waypoints(waypoints) # send_nav_goal -> send_waypoints 변경
            
        except Exception as e:
            self.get_logger().error(f"명령 데이터 해석 실패: {e}")

    # -------------------------------------------------------------------------
    # [Callback] 초기 위치 설정 (/robot/set_init_pose) - init_callback
    # -------------------------------------------------------------------------
    def init_callback(self, msg):
        try:
            data = yaml.safe_load(msg.data)
            p = PoseWithCovarianceStamped()
            p.header.frame_id = 'map'
            p.header.stamp = self.get_clock().now().to_msg()
            p.pose.pose.position.x = float(data['x'])
            p.pose.pose.position.y = float(data['y'])
            p.pose.pose.orientation.w = 1.0 
            p.pose.covariance = [0.1] * 36
            
            self.init_pose_pub.publish(p)
            self.get_logger().info(f"초기 위치 수신: ({data['x']}, {data['y']})")
        except Exception as e:
            self.get_logger().error(f"초기화 데이터 오류: {e}")

    # -------------------------------------------------------------------------
    # [Callback] 로봇 현재 위치 수신 (AMCL) - pose_callback [NEW]
    # -------------------------------------------------------------------------
    def pose_callback(self, msg):
        try:
            x = msg.pose.pose.position.x
            y = msg.pose.pose.position.y
            # 프론트엔드 전송용 JSON 문자열 생성
            pose_data = json.dumps({'x': x, 'y': y})
            self.current_pose_pub.publish(String(data=pose_data))
        except Exception as e:
            # 빈번하게 호출되므로 에러 로그는 생략하거나 디버그 레벨로 처리
            pass

    # -------------------------------------------------------------------------
    # [Nav2] 액션 전송 - send_waypoints (waypoint_navigator.py 로직 100% 반영)
    # -------------------------------------------------------------------------
    def send_waypoints(self, waypoints):
        self.get_logger().info(f"[DEBUG] Waiting for Nav2 Action Server...") # [DEBUG] 서버 대기 시작
        if not self.nav_client.wait_for_server(timeout_sec=5.0):
            self.get_logger().error("[DEBUG] Nav2 Action Server Not Available!") # [DEBUG] 서버 연결 실패
            return

        self.get_logger().info(f"[DEBUG] Constructing Goal with {len(waypoints)} waypoints") # [DEBUG] 목표 생성 확인
        goal_msg = NavigateThroughPoses.Goal()
        
        # waypoint_navigator.py와 동일하게 루프 내에서 시간 생성 (Nav2 요구사항일 수 있음)
        for wp in waypoints:
            pose = PoseStamped()
            pose.header.frame_id = 'map'
            pose.header.stamp = self.get_clock().now().to_msg()
            
            pose.pose.position.x = float(wp['x'])
            pose.pose.position.y = float(wp['y'])
            pose.pose.orientation.z = float(wp['z'])
            pose.pose.orientation.w = float(wp['w'])
            
            goal_msg.poses.append(pose)

        self.get_logger().info(f"{len(waypoints)}개의 지점 경유 시작")
        future = self.nav_client.send_goal_async(goal_msg)
        future.add_done_callback(self.response_callback) # nav_response_callback -> response_callback

    def response_callback(self, future):
        self.get_logger().info("[DEBUG] Received Goal Response from Nav2") # [DEBUG] 응답 수신
        handle = future.result()
        if not handle.accepted:
            self.get_logger().warn("[DEBUG] Nav2 Rejected the Goal!") # [DEBUG] 거절 로그
            return
        self.goal_handle = handle
        self.get_logger().info("[DEBUG] Goal Accepted. Moving...") # [DEBUG] 수락 로그
        handle.get_result_async().add_done_callback(self.result_callback) # nav_result_callback -> result_callback

    def result_callback(self, future):
        status = future.result().status
        self.get_logger().info(f"[DEBUG] Navigation Finished with Status: {status}") # [DEBUG] 종료 상태
        if status == 4: # SUCCEEDED
            self.get_logger().info("목적지 도착!")
            self.status_pub.publish(String(data="ARRIVED"))
        self.goal_handle = None

    # -------------------------------------------------------------------------
    # [Cleanup] 종료 시 처리
    # -------------------------------------------------------------------------
    def destroy_node(self):
        self.follower_manager.stop_all()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = RobotController()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()