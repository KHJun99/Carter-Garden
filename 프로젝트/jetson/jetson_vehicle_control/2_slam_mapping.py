# 2_slam_mapping.py - QoS 호환성 수정 완료
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy # <--- 얘네가 추가됨
from sensor_msgs.msg import LaserScan
import numpy as np
import matplotlib.pyplot as plt

class SlamMappingNode(Node):
    def __init__(self):
        super().__init__('slam_mapping')
        self.scan_data = []
        
        # 🛠️ [핵심 수정] 라이다의 성격(Best Effort)에 맞춰주는 설정
        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,  # 라이다가 Best Effort라 맞춰줌
            durability=DurabilityPolicy.VOLATILE,       # 지나간 데이터는 굳이 기억 안 함
            history=HistoryPolicy.KEEP_LAST,
            depth=10
        )

        # qos_profile 적용해서 구독
        self.sub = self.create_subscription(
            LaserScan, 
            '/scan', 
            self.callback, 
            qos_profile  # <--- 여기에 숫자 10 대신 qos_profile을 넣음
        )
            
        print("🗺️ SLAM 매핑 시작 (데이터 100개 모으면 저장)")

    def callback(self, msg):
        # 데이터 처리 (이전과 동일)
        angles = np.arange(msg.angle_min, msg.angle_max, msg.angle_increment)
        ranges = np.array(msg.ranges)
        
        valid_mask = (ranges > 0.1) & (ranges < 10.0)
        
        filtered_angles = angles[valid_mask]
        filtered_ranges = ranges[valid_mask]
        
        if len(filtered_ranges) == 0:
            return

        self.scan_data.append((filtered_angles, filtered_ranges))
        print(f"📍 매핑 진행: {len(self.scan_data)}/100")
        
        if len(self.scan_data) >= 100:
            self.save_map()
            raise SystemExit

    def save_map(self):
        plt.figure(figsize=(10, 8))
        ax = plt.subplot(111, projection='polar')
        
        for angles, ranges in self.scan_data:
            ax.plot(angles, ranges, 'b.', markersize=0.5, alpha=0.3)
            
        ax.set_title("YDLidar Map Result", fontsize=16)
        ax.grid(True)
        plt.savefig('slam_map.png', dpi=300, bbox_inches='tight')
        print("✅ slam_map.png 저장 완료!")

def main():
    rclpy.init()
    node = SlamMappingNode()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        node.destroy_node()
        try:
            rclpy.shutdown()
        except:
            pass

if __name__ == '__main__':
    main()