import math
import time

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Imu, LaserScan
from nav_msgs.msg import Odometry

from motor_hat import MotorDriverHat
from config import MOTOR_SAFE_SPEED, LIDAR_MIN_RANGE, LIDAR_MAX_RANGE

# 각도를 -π에서 π 사이로 유지하는 함수 (정규화)
def normalize_angle(angle):
    while angle > math.pi:
        angle -= 2.0 * math.pi
    while angle < -math.pi:
        angle += 2.0 * math.pi
    return angle

class StraightFusionController(Node):
    def __init__(self):
        super().__init__("straight_fusion_controller")

        # 토픽 설정
        self.declare_parameter("cmd_in_topic", "/cmd_vel")
        self.declare_parameter("imu_topic", "/imu/data")
        self.declare_parameter("odom_topic", "/odometry/filtered")
        self.declare_parameter("scan_topic", "/scan")

        # PID 및 제어 설정
        self.declare_parameter("kp", 3.0)
        self.declare_parameter("ki", 0.0)
        self.declare_parameter("kd", 0.1)
        self.declare_parameter("max_correction", 1.0)
        self.declare_parameter("straight_linear_threshold", 0.05)
        self.declare_parameter("straight_angular_threshold", 0.05)
        self.declare_parameter("cmd_timeout_sec", 0.5)

        # 설정값 읽기
        self.cmd_in_topic = self.get_parameter("cmd_in_topic").value
        self.imu_topic = self.get_parameter("imu_topic").value
        self.odom_topic = self.get_parameter("odom_topic").value
        
        self.kp = self.get_parameter("kp").value
        self.ki = self.get_parameter("ki").value
        self.kd = self.get_parameter("kd").value
        self.max_correction = self.get_parameter("max_correction").value
        self.straight_linear_threshold = self.get_parameter("straight_linear_threshold").value
        self.straight_angular_threshold = self.get_parameter("straight_angular_threshold").value
        self.cmd_timeout_sec = self.get_parameter("cmd_timeout_sec").value

        # 모터 초기화
        self.motor = MotorDriverHat()

        # 데이터 구독
        self.create_subscription(Twist, self.cmd_in_topic, self.cmd_callback, 10)
        self.create_subscription(Imu, self.imu_topic, self.imu_callback, 50)

        # 로봇 상태 변수
        self.last_cmd = Twist()
        self.last_cmd_time = time.time()
        self.yaw_imu = 0.0
        self.last_imu_time = None
        self.has_imu = False

        self.straight_mode = False
        self.desired_yaw = 0.0
        self.integral = 0.0
        self.last_error = 0.0
        self.last_control_time = None

        # 메인 루프 (30Hz)
        self.timer = self.create_timer(1.0 / 30.0, self.control_loop)
        self.get_logger().info("🚀 직진 보정 컨트롤러가 시작되었습니다.")

    def cmd_callback(self, msg):
        self.last_cmd = msg
        self.last_cmd_time = time.time()

    def imu_callback(self, msg):
        """[핵심 수정] EKF가 각도를 못 주므로, 자이로 각속도를 직접 적분하여 각도 계산"""
        t = msg.header.stamp
        now = t.sec + t.nanosec * 1e-9
        
        if self.last_imu_time is None:
            self.last_imu_time = now
            return

        dt = now - self.last_imu_time
        self.last_imu_time = now

        if 0 < dt < 0.5:
            # 각속도(z)를 누적하여 현재 각도(yaw) 계산
            gyro_z = msg.angular_velocity.z 
            self.yaw_imu = normalize_angle(self.yaw_imu + gyro_z * dt)
            self.has_imu = True

    def control_loop(self):
        now = time.time()
        
        # 안전 장치: 명령 끊기면 정지
        if (now - self.last_cmd_time) > self.cmd_timeout_sec:
            self.motor.stop()
            return

        cmd_linear = self.last_cmd.linear.x
        cmd_angular = self.last_cmd.angular.z

        # 직진 상태 판정
        is_straight_cmd = abs(cmd_linear) >= self.straight_linear_threshold and abs(cmd_angular) <= self.straight_angular_threshold

        if not self.has_imu:
            self.apply_motor(cmd_linear, cmd_angular)
            return

        if not is_straight_cmd:
            self.straight_mode = False
            self.apply_motor(cmd_linear, cmd_angular)
            return

        # 직진 보정 로직 활성화
        if not self.straight_mode:
            self.straight_mode = True
            self.desired_yaw = self.yaw_imu
            self.integral = 0.0
            self.last_error = 0.0
            self.get_logger().info(f"보정 타겟 고정: {math.degrees(self.desired_yaw):.2f}°")

        # PID 연산
        t = self.get_clock().now().nanoseconds * 1e-9
        dt = t - (self.last_control_time if self.last_control_time else t)
        self.last_control_time = t

        error = normalize_angle(self.desired_yaw - self.yaw_imu)
        
        if 0 < dt < 1.0:
            self.integral = max(-1.0, min(1.0, self.integral + error * dt))
            derivative = (error - self.last_error) / dt
        else:
            derivative = 0.0
        self.last_error = error

        # 보정치 계산 (휘는 방향 반대로 조향)
        # 만약 더 왼쪽으로 휘면 kp 앞에 -를 붙이거나 뺍니다.
        correction = (self.kp * error + self.ki * self.integral + self.kd * derivative)
        correction = max(-self.max_correction, min(self.max_correction, correction))

        # 로그 출력 (Err가 변하는지 확인 필수!)
        self.get_logger().info(f"Yaw: {math.degrees(self.yaw_imu):.1f}°, Err: {math.degrees(error):.2f}°, Corr: {correction:.3f}")

        self.apply_motor(cmd_linear, cmd_angular + correction)

    def apply_motor(self, linear, angular):
        # 전진/후진 반전 해결 (후진 명령시 직진하도록 수정됨)
        linear = -linear 
        
        left = linear - angular
        right = linear + angular

        # 안전 제한
        left = max(-MOTOR_SAFE_SPEED, min(MOTOR_SAFE_SPEED, left))
        right = max(-MOTOR_SAFE_SPEED, min(MOTOR_SAFE_SPEED, right))

        self.motor.drive(left, right)

def main(args=None):
    rclpy.init(args=args)
    node = StraightFusionController()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.motor.stop()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == "__main__":
    main()