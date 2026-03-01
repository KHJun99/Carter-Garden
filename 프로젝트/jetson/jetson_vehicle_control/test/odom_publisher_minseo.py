import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from geometry_msgs.msg import TransformStamped
import tf2_ros
import Jetson.GPIO as GPIO
import numpy as np
import math
import smbus
import time

# --- 로봇 하드웨어 설정 ---
WHEEL_DIAMETER = 0.064  # 바퀴 지름 (m)
WHEEL_BASE = 0.16       # 바퀴 간격 (m)
PPR = 11                # 엔코더 펄스 수
GEAR_RATIO = 1         # 기어비 (1:20 등 실제 환경에 맞게 수정 필요)
TICKS_PER_REV = PPR * GEAR_RATIO * 2 

# --- IMU 설정 (MPU6050) ---
BUS_NUMBER = 1
IMU_ADDRESS = 0x68
GYRO_SCALE_FACTOR = 131.0  # FS_SEL=0일 때, LSB/(deg/s)
ALPHA = 0.8                # 필터 상수 (높을수록 이전 값 비중 큼 -> 부드러움)

# --- 핀 설정 ---
L_ENCODER_A = 7
L_ENCODER_B = 31
R_ENCODER_A = 33
R_ENCODER_B = 35

class OdometryPublisher(Node):
    def __init__(self):
        super().__init__('odom_publisher')
        self.odom_pub = self.create_publisher(Odometry, 'odom', 10)
        self.tf_broadcaster = tf2_ros.TransformBroadcaster(self)
        
        # --- 로봇 상태값 ---
        self.x = 0.0
        self.y = 0.0
        self.th = 0.0  # 현재 각도 (Radians)
        
        self.left_ticks = 0
        self.right_ticks = 0
        self.last_time = self.get_clock().now()

        # --- GPIO 설정 ---
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup([L_ENCODER_A, L_ENCODER_B, R_ENCODER_A, R_ENCODER_B], GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(L_ENCODER_A, GPIO.BOTH, callback=self.left_encoder_callback)
        GPIO.add_event_detect(R_ENCODER_A, GPIO.BOTH, callback=self.right_encoder_callback)

        # --- IMU 초기화 및 캘리브레이션 ---
        self.init_imu()
        self.gyro_z_offset = 0.0
        self.last_gyro_z_raw = 0.0
        self.calibrate_imu()  # 시작 시 0점 잡기 (Blocking)

        # 타이머 실행 (20Hz)
        self.timer = self.create_timer(0.05, self.update_odometry) 
        self.get_logger().info(f"✅ High-Performance Odom Node Started! (Encoder + IMU)")

    def init_imu(self):
        """IMU 연결 및 설정"""
        try:
            self.bus = smbus.SMBus(BUS_NUMBER)
            # Sleep 모드 해제
            self.bus.write_byte_data(IMU_ADDRESS, 0x6B, 0)
            self.get_logger().info("✅ IMU Connected.")
        except Exception as e:
            self.get_logger().error(f"❌ IMU Init Failed: {e}")
            self.bus = None

    def read_word_2c(self, reg):
        """16비트 데이터 읽기 및 2의 보수 변환"""
        if self.bus is None: return 0
        try:
            high = self.bus.read_byte_data(IMU_ADDRESS, reg)
            low = self.bus.read_byte_data(IMU_ADDRESS, reg + 1)
            val = (high << 8) | low
            if val >= 0x8000:
                return -((65535 - val) + 1)
            else:
                return val
        except Exception:
            return 0

    def calibrate_imu(self):
        """정지 상태에서 초기 오차(Offset) 계산"""
        if self.bus is None: return

        self.get_logger().info("🚧 Calibrating IMU... Do not move the robot! (2 sec)")
        cal_sum = 0
        count = 100
        
        for _ in range(count):
            cal_sum += self.read_word_2c(0x47) # Gyro Z 레지스터
            time.sleep(0.02)
        
        self.gyro_z_offset = cal_sum / count
        self.get_logger().info(f"✅ Calibration Done. Offset: {self.gyro_z_offset:.2f}")

    def get_imu_angular_velocity(self):
        """필터링 및 단위 변환된 각속도(rad/s) 반환"""
        if self.bus is None: return 0.0

        # 1. Raw 데이터 읽기
        raw_z = self.read_word_2c(0x47)
        
        # 2. 오차 보정 (Calibration)
        curr_z = raw_z - self.gyro_z_offset

        # 3. 로우 패스 필터 (Low Pass Filter) - 튀는 값 억제
        if self.last_gyro_z_raw == 0:
            filtered_z = curr_z
        else:
            filtered_z = (self.last_gyro_z_raw * ALPHA) + (curr_z * (1 - ALPHA))
        self.last_gyro_z_raw = filtered_z

        # 4. 물리 단위 변환 (deg/s -> rad/s)
        # filtered_z는 LSB 단위이므로 Scale Factor로 나눠 deg/s로 변환
        deg_per_sec = filtered_z / GYRO_SCALE_FACTOR
        rad_per_sec = deg_per_sec * (math.pi / 180.0)

        # 5. 정지 노이즈 제거 (Deadzone): 너무 작은 값은 0으로 처리
        if abs(rad_per_sec) < 0.005: 
            rad_per_sec = 0.0
            
        return rad_per_sec

    # --- 엔코더 콜백 (방향 수정됨) ---
    def left_encoder_callback(self, channel):
        if GPIO.input(L_ENCODER_A) == GPIO.input(L_ENCODER_B):
            self.left_ticks -= 1
        else:
            self.left_ticks += 1

    def right_encoder_callback(self, channel):
        if GPIO.input(R_ENCODER_A) == GPIO.input(R_ENCODER_B):
            self.right_ticks += 1
        else:
            self.right_ticks -= 1

    def update_odometry(self):
        current_time = self.get_clock().now()
        dt = (current_time - self.last_time).nanoseconds / 1e9
        if dt == 0: return

        # =========================================================
        # [핵심] 센서 퓨전 (Sensor Fusion)
        # 1. 이동 거리 (Linear Distance) -> 엔코더 사용
        # 2. 회전 각도 (Orientation)     -> IMU 사용 (훨씬 정확함)
        # =========================================================

        # 1. 엔코더 기반 거리 계산
        dist_per_tick = (math.pi * WHEEL_DIAMETER) / TICKS_PER_REV
        d_left = self.left_ticks * dist_per_tick
        d_right = self.right_ticks * dist_per_tick
        
        # 틱 초기화 (상대값 계산용)
        self.left_ticks = 0
        self.right_ticks = 0

        d_center = (d_left + d_right) / 2.0  # 로봇이 이동한 직선 거리

        # 2. IMU 기반 회전각 계산 (d_th)
        # 엔코더로 계산한 회전각: d_th_enc = (d_right - d_left) / WHEEL_BASE (사용 안 함 또는 비교용)
        angular_vel_z = self.get_imu_angular_velocity() # rad/s
        
        # 회전량 적분: 각속도 * 시간 = 각도 변화량
        # *주의* IMU 장착 방향에 따라 부호가 반대일 수 있습니다. 회전 시 각도가 반대로 가면 '-'를 붙이세요.
        d_th_imu = angular_vel_z * dt 

        # 3. 위치 업데이트 (Dead Reckoning)
        # 회전각은 IMU 값을 신뢰하여 업데이트
        self.th += d_th_imu 
        
        # 위치는 엔코더 거리와 IMU 각도를 조합하여 계산
        self.x += d_center * math.cos(self.th)
        self.y += d_center * math.sin(self.th)

        # ---------------------------------------------------------
        # 메시지 발행 (TF & Odom)
        # ---------------------------------------------------------
        # 정규화 (Quaternion 변환)
        q_x = 0.0
        q_y = 0.0
        q_z = math.sin(self.th / 2.0)
        q_w = math.cos(self.th / 2.0)

        # 1. TF 발행
        t = TransformStamped()
        t.header.stamp = current_time.to_msg()
        t.header.frame_id = 'odom'
        t.child_frame_id = 'base_link'
        t.transform.translation.x = self.x
        t.transform.translation.y = self.y
        t.transform.translation.z = 0.0
        t.transform.rotation.z = q_z
        t.transform.rotation.w = q_w
        self.tf_broadcaster.sendTransform(t)

        # 2. Odom 토픽 발행
        odom = Odometry()
        odom.header.stamp = current_time.to_msg()
        odom.header.frame_id = 'odom'
        odom.child_frame_id = 'base_link'
        
        # 포즈
        odom.pose.pose.position.x = self.x
        odom.pose.pose.position.y = self.y
        odom.pose.pose.orientation.z = q_z
        odom.pose.pose.orientation.w = q_w
        
        # 속도 (Twist)
        odom.twist.twist.linear.x = d_center / dt  # 선속도는 엔코더 기준
        odom.twist.twist.angular.z = angular_vel_z # 각속도는 IMU 기준
        
        self.odom_pub.publish(odom)

        self.last_time = current_time

def main():
    rclpy.init()
    node = OdometryPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        GPIO.cleanup()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()