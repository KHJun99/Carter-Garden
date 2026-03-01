import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from geometry_msgs.msg import PoseWithCovarianceStamped
from std_msgs.msg import String
from nav2_msgs.action import NavigateToPose
import json
import time

# ===============================================================
# [Smart Cart V3.3]
# ===============================================================

class SmartCartNavigator(Node):
    def __init__(self):
        super().__init__('smart_cart_navigator',
                         allow_undeclared_parameters=True,
                         automatically_declare_parameters_from_overrides=True)

        # 파라미터 및 퍼블리셔 설정
        try:
            self.declare_parameter('use_sim_time', True)
        except: pass
        self.set_parameters([rclpy.parameter.Parameter('use_sim_time', rclpy.Parameter.Type.BOOL, True)])

        self.initial_pose_pub = self.create_publisher(PoseWithCovarianceStamped, '/initialpose', 10)
        # [추가] 상태 알림용 퍼블리셔
        self.status_pub = self.create_publisher(String, '/robot/status', 10)

        # Action Client
        self._action_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')

        # 구독 설정
        self.create_subscription(String, '/robot/destination', self.destination_callback, 10)
        self.create_subscription(String, '/robot/set_init_pose', self.set_init_pose_callback, 10)
        self.create_subscription(String, '/robot/mode', self.mode_callback, 10)

        self.current_goal_handle = None
        self.latest_goal = None # RESUME용 메모장

        print("\n" + "="*50)
        print(" [Smart Cart V3.3] 시스템 가동")
        print(" Nav2 서버 연결 대기 중...")
        self._action_client.wait_for_server()
        print(" 연결 성공! 프론트엔드로부터 초기 위치 수신 대기 중...")
        # [수정] 자동 초기화 제거 -> 프론트 신호 대기
        # time.sleep(1.0)
        # self.set_initial_pose(0.0, 0.0)
        print(" 준비 완료.")
        print("="*50 + "\n")

    # --- 초기 위치 설정 ---
    def set_init_pose_callback(self, msg):
        try:
            data = json.loads(msg.data)
            self.set_initial_pose(float(data.get('x', 0.0)), float(data.get('y', 0.0)))
        except: pass

    def set_initial_pose(self, x, y):
        msg = PoseWithCovarianceStamped()
        msg.header.frame_id = 'map'
        msg.header.stamp = self.get_clock().now().to_msg()

        # [구조 주의] PoseWithCovarianceStamped -> pose -> pose -> position
        msg.pose.pose.position.x = x
        msg.pose.pose.position.y = y
        msg.pose.pose.orientation.w = 1.0 # 방향 (정면)

        # [수정] 공분산(Covariance) 축소: 위치 확신도 높임 (오차 감소)
        msg.pose.covariance = [0.0] * 36
        msg.pose.covariance[0] = 0.1  # X 분산 (너무 작으면 이동 중 보정 안됨)
        msg.pose.covariance[7] = 0.1  # Y 분산
        msg.pose.covariance[35] = 0.05 # 각도 분산

        self.initial_pose_pub.publish(msg)
        print(f"--- [설정] 초기 위치를 ({x}, {y})로 초기화했습니다. ---")

    # --- 목적지 수신 ---
    def destination_callback(self, msg):
        try:
            data = json.loads(msg.data)
            x = float(data.get('pos_x', 0.0))
            y = float(data.get('pos_y', 0.0))
            tag = data.get('tag', 'Unknown')

            # RESUME을 위해 기억해둠
            self.latest_goal = {'x': x, 'y': y, 'tag': tag}

            print(f"\n[목적지 수신] {tag} -> ({x}, {y})")
            self.move_to_goal(x, y)
        except Exception as e:
            print(f"[오류] 데이터 해석 실패: {e}")

    # --- 모드 제어 (STOP / RESUME) ---
    def mode_callback(self, msg):
        command = msg.data.upper()

        if command == 'STOP':
            print("--- 사용자 요청으로 주행을 취소합니다. ---")
            if self.current_goal_handle:
                self.current_goal_handle.cancel_goal_async()
                self.current_goal_handle = None

        elif command == 'RESUME':
            print("--- 이전 목적지로 다시 출발합니다. ---")
            if self.latest_goal:
                x = self.latest_goal['x']
                y = self.latest_goal['y']
                print(f"    --> 기억된 목표: {self.latest_goal['tag']} ({x}, {y})")
                self.move_to_goal(x, y)
            else:
                print("    기억된 목적지가 없습니다.")

    # --- Nav2 액션 전송 (수정된 부분) ---
    def move_to_goal(self, x, y):
        # 기존 주행 취소
        if self.current_goal_handle is not None:
             self.current_goal_handle.cancel_goal_async()

        goal_msg = NavigateToPose.Goal()
        goal_msg.pose.header.frame_id = 'map'
        goal_msg.pose.header.stamp = self.get_clock().now().to_msg()

        # [수정 완료] 계층 구조 정확히 반영
        goal_msg.pose.pose.position.x = x
        goal_msg.pose.pose.position.y = y
        goal_msg.pose.pose.orientation.w = 1.0 # <--- 여기가 문제였음 (.pose 추가)

        print(f"--> Nav2로 요청 전송: ({x}, {y})")

        # 비동기 전송
        future = self._action_client.send_goal_async(goal_msg)
        future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            print("--- Nav2가 목표를 거절했습니다. (초기 위치 미설정 또는 맵 오류) ---")
            return

        print("--- 주행을 시작합니다! ---")
        self.current_goal_handle = goal_handle

        # 결과 대기
        get_result_future = goal_handle.get_result_async()
        get_result_future.add_done_callback(self.get_result_callback)

    def get_result_callback(self, future):
        self.current_goal_handle = None
        status = future.result().status
        # 4: SUCCEEDED, 5: CANCELED, 6: ABORTED
        if status == 4:
            print("--- 목적지에 도착했습니다. ---")
            # [추가] 도착 신호 전송
            msg = String()
            msg.data = "ARRIVED"
            self.status_pub.publish(msg)
        elif status == 5:
            print("--- 주행이 취소되었습니다. ---")
        elif status == 6:
            print("--- [알림] 장애물 등으로 인해 주행이 중단되었습니다. 3초 후 재시도합니다. ---")
            # 3초 후 재시도를 위한 일회성 타이머 생성
            self.retry_timer = self.create_timer(3.0, self.retry_navigation)
        else:
            print(f"--- [종료] 상태 코드: {status} ---")

    def retry_navigation(self):
        # 타이머 중지 (1회성 실행을 위함)
        if hasattr(self, 'retry_timer'):
            self.retry_timer.cancel()
            del self.retry_timer

        if self.latest_goal:
            x = self.latest_goal['x']
            y = self.latest_goal['y']
            tag = self.latest_goal['tag']
            print(f"--- [재시도] 목적지로 다시 출발합니다: {tag} ({x}, {y}) ---")
            self.move_to_goal(x, y)
        else:
            print("--- [경고] 재시도할 마지막 목적지 정보가 없습니다. ---")

def main(args=None):
    rclpy.init(args=args)
    node = SmartCartNavigator()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()