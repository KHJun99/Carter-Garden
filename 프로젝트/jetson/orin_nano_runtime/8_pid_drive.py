# 8_pid_drive.py - PID 완전체 버전 (I, D 추가)
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
import math
import time
import threading

from motor_hat import MotorDriverHat
from config import MOTOR_SAFE_SPEED

# ==========================================
# ⚙️ 튜닝 구역 (부드러운 주행용)
# ==========================================
TARGET_SPEED = -0.4 

KP = 1.0    # [수정] 1.5 -> 1.0 (힘을 조금 뺍시다)
KI = 0.05   # [유지] 0도로 끝까지 밀어주는 힘은 유지
KD = 0.05   # [핵심] 0.5 -> 0.05 (1/10로 줄임! 진동의 주범)

STRAIGHT_BIAS = 0.0             
MAX_CORRECTION = 0.5            
CONTROL_DT = 0.02               
# ==========================================

class PIDDriveNode(Node):
    def __init__(self):
        super().__init__('pid_drive_node')
        self.subscription = self.create_subscription(
            Odometry, '/odometry/filtered', self.odom_callback, 10)
            
        self.motor = MotorDriverHat()
        self.current_yaw = 0.0
        self.target_yaw = None
        self.running = True
        self.last_odom_time = time.time()

        # [필수 추가] PID 계산을 위한 변수 초기화
        self.prev_error = 0.0
        self.integral = 0.0

        self.drive_thread = threading.Thread(target=self.drive_loop)
        self.drive_thread.start()

        print("🔥 [Real-PID] 완전체 주행 시작 (KP, KI, KD 적용)")

    def odom_callback(self, msg):
        q = msg.pose.pose.orientation
        siny_cosp = 2 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1 - 2 * (q.y * q.y + q.z * q.z)
        self.current_yaw = math.atan2(siny_cosp, cosy_cosp)
        self.last_odom_time = time.time()

        if self.target_yaw is None:
            self.target_yaw = self.current_yaw
            print(f"🎯 [기준점] 목표 방향 고정됨: {math.degrees(self.target_yaw):.2f}°")

    def drive_loop(self):
        while self.target_yaw is None and self.running:
            print("⏳ EKF 데이터 대기 중...")
            time.sleep(1.0)

        while self.running:
            if time.time() - self.last_odom_time > 1.0:
                print("🚨 [경고] 센서 데이터 끊김!")

            # 1. 오차 계산
            error = self.target_yaw - self.current_yaw
            while error > math.pi: error -= 2 * math.pi
            while error < -math.pi: error += 2 * math.pi

            # 2. PID 계산 (완전체 공식 적용!)
            # I (적분): 오차가 계속 있으면 값을 누적함 -> 나중에 큰 힘이 됨
            self.integral += error * CONTROL_DT
            # 적분값이 너무 커지지 않게 제한 (Anti-windup)
            self.integral = max(min(self.integral, 1.0), -1.0)

            # D (미분): 오차가 변하는 속도 (브레이크 역할)
            derivative = (error - self.prev_error) / CONTROL_DT
            self.prev_error = error

            # [핵심] P + I + D 다 더하기
            correction = (KP * error) + (KI * self.integral) + (KD * derivative)
            
            # 최대 보정치 제한
            correction = max(min(correction, MAX_CORRECTION), -MAX_CORRECTION)

            # 3. 속도 분배 (아까 찾은 '반대 부호' 적용 유지)
            # 부호를 반대로 뒤집습니다!
            speed_l = TARGET_SPEED + correction
            speed_r = TARGET_SPEED - correction

            # 속도 제한
            speed_l = max(min(speed_l, MOTOR_SAFE_SPEED), -MOTOR_SAFE_SPEED)
            speed_r = max(min(speed_r, MOTOR_SAFE_SPEED), -MOTOR_SAFE_SPEED)

            try:
                self.motor.drive(speed_l, speed_r)
                # 로그 확인
                print(f"Err:{math.degrees(error):5.1f}° | PID:{correction:5.2f} | L:{speed_l:5.2f} R:{speed_r:5.2f}")
            except Exception as e:
                print(f"모터 에러: {e}")

            time.sleep(CONTROL_DT)

    def stop(self):
        self.running = False
        self.drive_thread.join()
        self.motor.stop()
        print("🛑 정지")

def main(args=None):
    rclpy.init(args=args)
    node = PIDDriveNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.stop()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()