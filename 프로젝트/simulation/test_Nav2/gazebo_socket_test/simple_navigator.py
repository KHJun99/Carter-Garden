import rclpy
from rclpy.node import Node
from rclpy.exceptions import ParameterAlreadyDeclaredException
from geometry_msgs.msg import PoseStamped
from std_msgs.msg import String
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
import json
import time
import threading

# ===============================================================
# [스레드 데드락 심화 검증기 - 인자 수정본]
# ===============================================================

class DeadlockVerifier(Node):
    def __init__(self):
        super().__init__('deadlock_verifier',
                         allow_undeclared_parameters=True,
                         automatically_declare_parameters_from_overrides=True)

        try:
            self.declare_parameter('use_sim_time', True)
        except ParameterAlreadyDeclaredException:
            pass

        self.set_parameters([
            rclpy.parameter.Parameter('use_sim_time', rclpy.Parameter.Type.BOOL, True)
        ])

        # 1. 문제의 객체 생성
        self.navigator = BasicNavigator()

        self.print_status("초기화(__init__)", "노드 생성 완료")

        # 2. 초기 위치 설정 (여기서 데드락 유도)
        self.set_initial_pose_with_trap()

        # 3. 구독 설정
        self.create_subscription(String, '/robot/destination', self.destination_callback, 10)

        print("\n" + "="*60)
        print(" [생존 신고] __init__을 무사히 통과했습니다. (이 메시지가 보이나요?)")
        print("="*60 + "\n")

    def print_status(self, step, msg):
        tid = threading.get_ident()
        tname = threading.current_thread().name
        print(f"[{step} | {tname}({tid})] {msg}")

    def set_initial_pose_with_trap(self):
        print(f"\n--- [검증 1] 초기 위치 설정 단계 진입 ---")

        self.print_status("검증 1", "Nav2 활성화 대기 시작 (waitUntilNav2Active)")
        print("    >>> 5초 내에 다음 로그가 안 찍히면 '스레드 데드락' 확정입니다. <<<")

        # [수정됨] 인자를 모두 제거했습니다.
        # 이제 이 함수는 Nav2의 모든 노드(amcl, map_server 등)가 켜졌는지 확인하려 시도합니다.
        # 하지만 스레드가 없어서 응답을 못 받으므로 여기서 멈출(Deadlock) 것입니다.

        # 참고: 라이브러리 버전에 따라 타임아웃 없이 영원히 멈출 수도 있습니다.
        result = self.navigator.waitUntilNav2Active()

        if result:
             self.print_status("검증 1", "성공? (이게 뜨면 스레드 문제가 없는 것)")
        else:
             self.print_status("검증 1", "!!! 실패/타임아웃 !!! (예상대로 내부 노드가 먹통임)")

        initial_pose = PoseStamped()
        initial_pose.header.frame_id = 'map'
        initial_pose.header.stamp = self.navigator.get_clock().now().to_msg()
        initial_pose.pose.position.x = 0.0
        initial_pose.pose.position.y = 0.0
        initial_pose.pose.orientation.w = 1.0

        self.navigator.setInitialPose(initial_pose)
        self.print_status("검증 1", "setInitialPose 명령 전송")

    def destination_callback(self, msg):
        self.print_status("콜백", "목적지 수신함")
        try:
            data = json.loads(msg.data)
            x = float(data.get('pos_x', 0.0))
            y = float(data.get('pos_y', 0.0))

            goal_pose = PoseStamped()
            goal_pose.header.frame_id = 'map'
            goal_pose.header.stamp = self.navigator.get_clock().now().to_msg()
            goal_pose.pose.position.x = x
            goal_pose.pose.position.y = y
            goal_pose.pose.orientation.w = 1.0

            self.print_status("검증 2", f"이동 명령 전송 ({x}, {y})")
            self.navigator.goToPose(goal_pose)

            print("\n*** [검증 3] 피드백 루프 진입 ***")
            start_time = time.time()
            while time.time() - start_time < 10.0:
                if self.navigator.isTaskComplete():
                    result = self.navigator.getResult()
                    print(f"!!! 작업 조기 종료 감지됨. 결과 코드: {result} !!!")
                    break

                feedback = self.navigator.getFeedback()
                if feedback:
                    print(f"    [피드백] 남은 거리: {feedback.distance_remaining:.2f}m")
                else:
                    print("    [피드백] 데이터 NULL (내부 노드 기아 상태)")

                time.sleep(1.0)

        except Exception as e:
            print(f"[오류] {e}")

def main(args=None):
    rclpy.init(args=args)
    verifier = DeadlockVerifier()

    try:
        rclpy.spin(verifier)
    except KeyboardInterrupt:
        pass
    finally:
        verifier.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()