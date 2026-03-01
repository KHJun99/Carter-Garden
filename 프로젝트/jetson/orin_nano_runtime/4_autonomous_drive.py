# 4_autonomous_drive.py - YDLidar + 카메라
import rclpy
from rclpy.node import Node
import cv2
import numpy as np
from ultralytics import YOLO
from sensor_msgs.msg import LaserScan # 수정됨

from config import (
    CAMERA_INDEX, FRAME_CENTER_X, TURN_THRESHOLD, MOTOR_SAFE_SPEED,
    MODEL_PATH, CONFIDENCE_THRESHOLD, OBSTACLE_DISTANCE
)
from motor_hat import MotorDriverHat

class AutonomousDriveNode(Node):
    def __init__(self):
        super().__init__('autonomous_drive')
        self.motor_hat = MotorDriverHat()
        
        try:
            self.model = YOLO(MODEL_PATH)
        except:
            self.model = YOLO("yolov8n.pt")

        self.cap = cv2.VideoCapture(CAMERA_INDEX)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

        self.front_distance = 2.0
        
        # YDLidar 구독
        self.lidar_sub = self.create_subscription(
            LaserScan, '/scan', self.lidar_callback, 10)
            
        print("🤖 자율주행 통합 시스템 시작")

    def lidar_callback(self, msg):
        # 전방 거리 계산 로직 (Navigation과 동일)
        ranges = np.array(msg.ranges)
        index_range = int(np.radians(15) / msg.angle_increment)
        
        front_left = ranges[0:index_range]
        front_right = ranges[-index_range:]
        front_ranges = np.concatenate((front_left, front_right))
        
        valid_front = front_ranges[(front_ranges > 0.1) & (front_ranges < 10.0)]
        
        if len(valid_front) > 0:
            self.front_distance = np.min(valid_front)
        else:
            self.front_distance = 2.0

    def run(self):
        try:
            while rclpy.ok():
                # ROS 메시지 처리 (라이다 콜백 실행을 위해 필요)
                rclpy.spin_once(self, timeout_sec=0.01)
                
                ret, frame = self.cap.read()
                if not ret: continue

                # YOLO
                results = self.model(frame, verbose=False)
                person_detected = False
                turn_dir = 0
                
                for result in results:
                    for box in result.boxes:
                        if int(box.cls[0]) == 0 and box.conf[0] > CONFIDENCE_THRESHOLD:
                            person_detected = True
                            x1, _, x2, _ = box.xyxy[0].tolist()
                            center_x = (x1 + x2) / 2
                            
                            if center_x < FRAME_CENTER_X - TURN_THRESHOLD:
                                turn_dir = -1
                            elif center_x > FRAME_CENTER_X + TURN_THRESHOLD:
                                turn_dir = 1
                            break
                    if person_detected: break

                # 주행 로직
                if self.front_distance < OBSTACLE_DISTANCE:
                    print(f"🚫 [장애물 감지] {self.front_distance:.2f}m")
                    self.motor_hat.turn_left(-0.3)
                
                elif person_detected:
                    speed = MOTOR_SAFE_SPEED
                    if turn_dir == -1:
                        print(f"👤 [추종] 좌회전")
                        self.motor_hat.turn_left(-speed)
                    elif turn_dir == 1:
                        print(f"👤 [추종] 우회전")
                        self.motor_hat.turn_right(-speed)
                    else:
                        print(f"👤 [추종] 직진")
                        self.motor_hat.straight(-speed)
                else:
                    self.motor_hat.stop()

        except KeyboardInterrupt:
            pass
        finally:
            self.cleanup()

    def cleanup(self):
        self.motor_hat.stop()
        self.cap.release()
        cv2.destroyAllWindows()

def main():
    rclpy.init()
    node = AutonomousDriveNode()
    node.run()
    rclpy.shutdown()

if __name__ == '__main__':
    main()