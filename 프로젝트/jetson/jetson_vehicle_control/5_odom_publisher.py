import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from geometry_msgs.msg import TransformStamped
import tf2_ros
import Jetson.GPIO as GPIO
import numpy as np
import math
import threading
import time

# --- [1] 로봇 하드웨어 설정 ---
WHEEL_DIAMETER = 0.064  
WHEEL_BASE = 0.16       
PPR = 11                
GEAR_RATIO = 20         
TICKS_PER_REV = PPR * GEAR_RATIO 

# --- [2] 핀 설정 ---
L_ENCODER_A = 7
L_ENCODER_B = 11
R_ENCODER_A = 13
R_ENCODER_B = 15

class OdometryPublisher(Node):
    def __init__(self):
        super().__init__('odom_publisher')
        self.odom_pub = self.create_publisher(Odometry, 'odom', 10)
        self.tf_broadcaster = tf2_ros.TransformBroadcaster(self)
        
        self.x = 0.0
        self.y = 0.0
        self.th = 0.0
        self.left_ticks = 0
        self.right_ticks = 0
        self.last_time = self.get_clock().now()

        # GPIO 설정
        GPIO.setmode(GPIO.BOARD)
        # 물리 저항 사용 (PUD_OFF)
        GPIO.setup([L_ENCODER_A, L_ENCODER_B, R_ENCODER_A, R_ENCODER_B], GPIO.IN, pull_up_down=GPIO.PUD_OFF)
        
        # [핵심 변경] 인터럽트(add_event_detect) 대신 '폴링 스레드' 시작
        # 아까 성공한 테스트 코드처럼 직접 감시하는 방식입니다.
        self.running = True
        self.poll_thread = threading.Thread(target=self.poll_encoders)
        self.poll_thread.start()

        self.timer = self.create_timer(0.01, self.update_odometry)
        print(f"✅ Odom 노드 (폴링 모드) 시작! 틱수: {TICKS_PER_REV}")
        print("👉 이제 바퀴를 굴리면 반응할 겁니다.")

    def poll_encoders(self):
        """별도의 스레드에서 엔코더 상태를 미친듯이 확인하는 함수"""
        last_left_a = GPIO.input(L_ENCODER_A)
        last_right_a = GPIO.input(R_ENCODER_A)

        while self.running:
            # 1. 왼쪽 바퀴 감시
            curr_left_a = GPIO.input(L_ENCODER_A)
            if curr_left_a != last_left_a: # 상태 변화 감지!
                if curr_left_a == 1: # RISING (0 -> 1)
                    if GPIO.input(L_ENCODER_B) == 0:
                        self.left_ticks += 1
                        print("Left: UP (+)") 
                    else:
                        self.left_ticks -= 1
                        print("Left: DOWN (-)")
                last_left_a = curr_left_a

            # 2. 오른쪽 바퀴 감시
            curr_right_a = GPIO.input(R_ENCODER_A)
            if curr_right_a != last_right_a: # 상태 변화 감지!
                if curr_right_a == 1: # RISING (0 -> 1)
                    if GPIO.input(R_ENCODER_B) == 0:
                        self.right_ticks -= 1
                        print("Right: DOWN (-)")
                    else:
                        self.right_ticks += 1
                        print("Right: UP (+)")
                last_right_a = curr_right_a
            
            # 아주 짧은 대기 (CPU 폭주 방지)
            time.sleep(0.0001)

    def update_odometry(self):
        current_time = self.get_clock().now()
        
        # 거리 계산
        dist_per_tick = (math.pi * WHEEL_DIAMETER) / TICKS_PER_REV
        d_left = self.left_ticks * dist_per_tick
        d_right = self.right_ticks * dist_per_tick
        
        # 계산 후 틱 초기화
        self.left_ticks = 0
        self.right_ticks = 0

        d_center = (d_left + d_right) / 2.0
        d_th = (d_right - d_left) / WHEEL_BASE

        self.x += d_center * math.cos(self.th)
        self.y += d_center * math.sin(self.th)
        self.th += d_th

        q_z = math.sin(self.th / 2.0)
        q_w = math.cos(self.th / 2.0)

        # TF 발행
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

        # Odom 발행
        odom = Odometry()
        odom.header.stamp = current_time.to_msg()
        odom.header.frame_id = 'odom'
        odom.child_frame_id = 'base_link'
        odom.pose.pose.position.x = self.x
        odom.pose.pose.position.y = self.y
        odom.pose.pose.position.z = 0.0
        odom.pose.pose.orientation.z = q_z
        odom.pose.pose.orientation.w = q_w
        odom.pose.covariance = [0.01 if i in [0, 7, 35] else 0.0 for i in range(36)]
        
        self.odom_pub.publish(odom)
        self.last_time = current_time

    def destroy_node(self):
        self.running = False # 스레드 종료 신호
        if self.poll_thread.is_alive():
            self.poll_thread.join()
        super().destroy_node()

def main():
    rclpy.init()
    node = OdometryPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        GPIO.cleanup()
        rclpy.shutdown()

if __name__ == '__main__':
    main()