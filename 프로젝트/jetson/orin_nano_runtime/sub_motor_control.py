import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from motor_hat import MotorDriverHat
import math

# [설정] 속도 보정 계수 (ROS 속도 -> 모터 파워 변환)
# ROS가 0.2m/s라고 하면 모터에 0.2의 파워(20%)를 줄지, 더 세게 줄지 결정
LINEAR_SCALE = 1.0   # 직진 속도 100%
ANGULAR_SCALE = 0.4  # 회전 속도 상향

class MotorSubscriber(Node):
    def __init__(self):
        super().__init__('motor_subscriber')
        
        # 1. 모터 드라이버 연결
        try:
            self.driver = MotorDriverHat()
            self.get_logger().info("✅ 모터 드라이버(다리)가 ROS에 연결되었습니다.")
        except Exception as e:
            self.get_logger().error(f"❌ 모터 연결 실패: {e}")
            return

        # 2. 뇌(CarterFollower)의 명령 듣기 (/cmd_vel)
        self.create_subscription(Twist, '/cmd_vel', self.listener_callback, 10)

    def listener_callback(self, msg):
        # ROS Twist 메시지 분해
        # linear.x : 전진/후진 속도 (m/s)
        # angular.z : 좌/우 회전 속도 (rad/s)
        
        # Forward/backward direction invert
        linear = -msg.linear.x * LINEAR_SCALE
        angular = msg.angular.z * ANGULAR_SCALE

        # [차동 구동 계산] Differential Drive Logic
        # 왼쪽 바퀴 = 전진 - 회전
        # 오른쪽 바퀴 = 전진 + 회전
        left_speed = linear - angular
        right_speed = linear + angular

        # 모터 드라이버에 전달 (drive 함수 사용)
        # MotorDriverHat 내부에서 최대 속도 제한(MOTOR_SAFE_SPEED)이 걸려있으므로 그대로 넣어도 안전함
        self.driver.drive(left_speed, right_speed)

        # 디버깅용 로그 (너무 많이 뜨면 주석 처리)
        # self.get_logger().info(f"L: {left_speed:.2f}, R: {right_speed:.2f}")

    def destroy_node(self):
        self.driver.stop()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = MotorSubscriber()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
