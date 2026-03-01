import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped
from std_msgs.msg import String
from nav2_msgs.action import NavigateThroughPoses
import yaml

class WaypointNavigator(Node):
    def __init__(self):
        super().__init__('waypoint_navigator')

        # 시뮬레이션 시간 설정
        try:
            self.declare_parameter('use_sim_time', True)
        except:
            pass

        # 초기 위치 및 상태 피드백 퍼블리셔
        self.init_pose_pub = self.create_publisher(PoseWithCovarianceStamped, '/initialpose', 10)
        self.status_pub = self.create_publisher(String, '/robot/status', 10)

        # Nav2 경유지 주행 클라이언트
        self.nav_client = ActionClient(self, NavigateThroughPoses, 'navigate_through_poses')

        # 프론트엔드 통신용 토픽 구독
        self.create_subscription(String, '/robot/destination', self.goal_callback, 10)
        self.create_subscription(String, '/robot/mode', self.mode_callback, 10)
        self.create_subscription(String, '/robot/set_init_pose', self.init_callback, 10)

        self.goal_handle = None
        self.get_logger().info("웨이포인트 내비게이터 가동")

    def init_callback(self, msg):
        # 로봇 초기 위치 셋팅
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

    def goal_callback(self, msg):
        # 경로 명령 데이터 파싱 및 주행 시작
        try:
            payload = yaml.safe_load(msg.data)
            if payload.get('command') != 'navigate_waypoints':
                return

            waypoints = payload.get('waypoints', [])
            
            # [로그] 수신된 경로 상세 출력
            print("\n" + "="*50)
            print(f" [Vue 명령 수신] 총 {len(waypoints)}개의 경유지")
            for i, wp in enumerate(waypoints):
                print(f"  - WP {i+1}: ({wp['x']}, {wp['y']})")
            print("="*50 + "\n")

            self.send_waypoints(waypoints)
        except Exception as e:
            self.get_logger().error(f"명령 데이터 해석 실패: {e}")

    def send_waypoints(self, waypoints):
        # Nav2 액션 서버 연결 및 경유지 전송
        if not self.nav_client.wait_for_server(timeout_sec=5.0):
            self.get_logger().error("Nav2 서버 연결 불가")
            return

        goal_msg = NavigateThroughPoses.Goal()
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
        future.add_done_callback(self.response_callback)

    def response_callback(self, future):
        # 명령 수락 여부 확인
        handle = future.result()
        if not handle.accepted:
            self.get_logger().warn("Nav2에서 주행 명령을 거절함")
            return
        self.goal_handle = handle
        handle.get_result_async().add_done_callback(self.result_callback)

    def result_callback(self, future):
        # 주행 완료 상태 보고
        status = future.result().status
        if status == 4: # SUCCEEDED
            self.get_logger().info("목적지 도착!")
            self.status_pub.publish(String(data="ARRIVED"))
        self.goal_handle = None

    def mode_callback(self, msg):
        # 주행 중지 신호 처리
        if msg.data.upper() == 'STOP' and self.goal_handle:
            self.get_logger().info("주행 중지 요청 수신")
            self.goal_handle.cancel_goal_async()

def main():
    rclpy.init()
    node = WaypointNavigator()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
