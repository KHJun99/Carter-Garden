import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import PoseStamped
from vision_msgs.msg import Detection2DArray
import math

class NavGoalPublisher(Node):
    def __init__(self):
        super().__init__('nav_goal_publisher')

        self.target_dist = 1.2  # 조금 더 여유 있게 설정
        self.camera_fov = 62.2
        self.img_width = 640
        
        # [추가] 마지막으로 보낸 목적지 저장 (너무 자주 보내지 않기 위함)
        self.last_goal_x = 0.0
        self.last_goal_y = 0.0
        self.move_threshold = 0.2 # 사용자가 20cm 이상 움직여야 새 목적지 전송

        self.yolo_sub = self.create_subscription(Detection2DArray, '/detections', self.yolo_callback, 10)
        self.scan_sub = self.create_subscription(LaserScan, '/scan', self.scan_callback, 10)
        self.goal_pub = self.create_publisher(PoseStamped, '/goal_pose', 10)

        self.target_angle = 0.0
        self.is_owner_detected = False

        self.get_logger().info('목적지 전달 노드가 실행 중입니다. (2D Pose Estimate를 먼저 해주세요!)')

    def yolo_callback(self, msg):
        owner = next((d for d in msg.detections if int(d.id) >= 1000), None)
        if owner:
            px = owner.bbox.center.position.x
            self.target_angle = -((px - 320) / 640) * self.camera_fov
            self.is_owner_detected = True
        else:
            self.is_owner_detected = False

    def scan_callback(self, msg):
        if not self.is_owner_detected:
            return

        search_range = 15
        min_dist = 5.0
        center_idx = int(self.target_angle)

        for i in range(center_idx - search_range, center_idx + search_range):
            idx = i % 360
            if 0.15 < msg.ranges[idx] < min_dist:
                min_dist = msg.ranges[idx]

        goal_dist = max(0.0, min_dist - self.target_dist)
        angle_rad = self.target_angle * (math.pi / 180.0)
        
        # 현재 계산된 목적지 좌표
        new_goal_x = goal_dist * math.cos(angle_rad)
        new_goal_y = goal_dist * math.sin(angle_rad)

        # [개선] 이전 목적지와 거리를 비교하여 임계값 이상일 때만 발행
        dist_to_prev_goal = math.sqrt((new_goal_x - self.last_goal_x)**2 + (new_goal_y - self.last_goal_y)**2)

        if dist_to_prev_goal > self.move_threshold:
            goal_msg = PoseStamped()
            goal_msg.header.stamp = self.get_clock().now().to_msg()
            goal_msg.header.frame_id = "base_link" # 로봇 기준
            
            goal_msg.pose.position.x = new_goal_x
            goal_msg.pose.position.y = new_goal_y
            goal_msg.pose.orientation.w = 1.0

            self.goal_pub.publish(goal_msg)
            
            # 마지막 발행 좌표 업데이트
            self.last_goal_x = new_goal_x
            self.last_goal_y = new_goal_y
            self.get_logger().info(f'새로운 목적지 전송: x={new_goal_x:.2f}, y={new_goal_y:.2f}')

def main(args=None):
    rclpy.init(args=args)
    node = NavGoalPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
