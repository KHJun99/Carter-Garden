# 3_slam_navigation.py - YDLidar 장애물 회피
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
import numpy as np
from config import OBSTACLE_DISTANCE
from motor_hat import MotorDriverHat

class SlamNavigationNode(Node):
    def __init__(self):
        super().__init__('slam_navigation')
        self.motor_hat = MotorDriverHat()
        self.front_distance = 2.0
        
        # 토픽 변경: /scan
        self.sub = self.create_subscription(
            LaserScan, '/scan', self.lidar_callback, 10)
        print("🚀 장애물 회피 주행 시작")

    def lidar_callback(self, msg):
        # 전방 30도(-15도 ~ +15도) 범위의 거리값만 추출
        # 인덱스 계산: 0도가 정면이라고 가정 (YDLidar 설치 방향에 따라 다를 수 있음)
        
        ranges = np.array(msg.ranges)
        angle_increment = msg.angle_increment
        
        # 전체 데이터 개수
        count = len(ranges)
        
        # 전방 30도에 해당하는 데이터 개수 (좌우 15도)
        index_range = int(np.radians(15) / angle_increment)
        
        # 정면 기준 좌우 데이터 가져오기 (배열의 처음과 끝 부분)
        # ranges[0]이 정면이라고 가정할 때:
        front_left = ranges[0:index_range]
        front_right = ranges[-index_range:]
        
        front_ranges = np.concatenate((front_left, front_right))
        
        # 유효하지 않은 값(0.0 또는 inf) 제거
        valid_front = front_ranges[(front_ranges > 0.1) & (front_ranges < 10.0)]
        
        if len(valid_front) > 0:
            self.front_distance = np.min(valid_front)
        else:
            self.front_distance = 2.0 # 데이터 없으면 안전하다고 판단
            
        self.navigate()

    def navigate(self):
        if self.front_distance > OBSTACLE_DISTANCE:
            print(f"🚀 전진: {self.front_distance:.2f}m")
            self.motor_hat.straight(-0.5) # 모터 방향에 따라 - 부호 조절
        else:
            print(f"⚠️ 장애물! {self.front_distance:.2f}m - 회피")
            self.motor_hat.turn_left(-0.3)

def main():
    rclpy.init()
    node = SlamNavigationNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.motor_hat.stop()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()