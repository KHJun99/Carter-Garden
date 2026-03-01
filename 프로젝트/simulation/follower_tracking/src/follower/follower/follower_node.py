import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist
from vision_msgs.msg import Detection2DArray
from rclpy.duration import Duration
import math
import numpy as np

class CarterFollower(Node):
    def __init__(self):
        super().__init__('carter_follower')

        # --- 설정값 (장애물 회피 최적화) ---
        self.target_dist = 1.0        # 목표 유지 거리
        self.avoid_dist = 0.7         # 장애물 회피 시작 거리
        self.safe_stop_dist = 0.4     # 비상 정지 거리
        self.max_linear_vel = 0.25
        self.max_angular_vel = 1.0
        self.camera_fov = 62.2
        self.img_width = 640
        self.tracking_timeout = Duration(seconds=3.0)

        # --- 상태 변수 ---
        self.target_angle = 0.0
        self.last_dist = 1.0
        self.last_target_time = self.get_clock().now()
        self.is_owner_detected = False

        self.yolo_sub = self.create_subscription(Detection2DArray, '/detections', self.yolo_callback, 10)
        self.scan_sub = self.create_subscription(LaserScan, '/scan', self.scan_callback, 10)
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)

        self.get_logger().info('장애물 회피 지능형 추종 노드가 시작되었습니다.')

    def yolo_callback(self, msg):
        owner_det = next((d for d in msg.detections if int(d.id) >= 1000), None)
        if owner_det:
            px = owner_det.bbox.center.position.x
            self.target_angle = -((px - (self.img_width/2)) / self.img_width) * self.camera_fov
            self.last_target_time = self.get_clock().now()
            self.is_owner_detected = True
        else:
            self.is_owner_detected = False

    def scan_callback(self, msg):
        current_time = self.get_clock().now()
        if (current_time - self.last_target_time) > self.tracking_timeout:
            self.stop_robot()
            return

        # 1. 사람(타겟) 위치 특정
        search_range = 20 if self.is_owner_detected else 45
        target_min_dist = 5.0
        target_idx = int(self.target_angle)
        
        for i in range(target_idx - search_range, target_idx + search_range):
            idx = i % 360
            if 0.1 < msg.ranges[idx] < target_min_dist:
                target_min_dist = msg.ranges[idx]
                target_idx = i
        
        self.target_angle = float(target_idx)
        self.last_dist = target_min_dist

        # 2. 장애물 회피 벡터 계산 (Repulsive Force)
        # 전방 120도 범위를 체크하여 장애물이 있으면 반대 방향으로 회전력 추가
        avoid_steering = 0.0
        for i in range(-60, 61):
            idx = i % 360
            dist = msg.ranges[idx]
            
            # 타겟(사람)이 아닌 물체가 너무 가까이 있으면
            if 0.1 < dist < self.avoid_dist and abs(i - target_idx) > 15:
                # 장애물이 왼쪽에 있으면 오른쪽(-)으로, 오른쪽에 있으면 왼쪽(+)으로
                weight = (self.avoid_dist - dist) / self.avoid_dist
                avoid_steering -= (i / 60.0) * weight * 0.5

        # 3. 최종 제어 명령 생성
        twist = Twist()
        
        # 선속도: 사람과의 거리 + 주변 장애물 유무에 따라 감속
        dist_error = target_min_dist - self.target_dist
        linear_v = dist_error * 0.6
        # 전방에 뭔가 너무 가까우면 감속
        front_dist = min(msg.ranges[0:10] + msg.ranges[350:360])
        if front_dist < self.safe_stop_dist:
            linear_v = min(linear_v, 0.0) # 전진 금지

        twist.linear.x = max(min(linear_v, self.max_linear_vel), -0.2)

        # 각속도: (사람을 향한 회전) + (장애물을 피하기 위한 회전)
        tracking_steering = (self.target_angle * (math.pi / 180.0)) * 1.5
        twist.angular.z = tracking_steering + avoid_steering
        twist.angular.z = max(min(twist.angular.z, self.max_angular_vel), -self.max_angular_vel)

        self.cmd_pub.publish(twist)

    def stop_robot(self):
        self.cmd_pub.publish(Twist())

def main():
    rclpy.init()
    node = CarterFollower()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.stop_robot()
        node.destroy_node()
        rclpy.shutdown()
