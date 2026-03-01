import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
from vision_msgs.msg import Detection2DArray, Detection2D
import cv2
import torch
import numpy as np
from ultralytics import YOLO

# ================= 설정 (Configuration) =================
YOLO_MODEL = 'yolo11n.pt' # 기본 모델 사용 (사람 인식용)
CONFIDENCE_THRESHOLD = 0.5 # 사람 인식 신뢰도 기준

# 이미지 처리
PROCESS_WIDTH = 640
PROCESS_HEIGHT = 360

class SimpleYoloGemini(Node):
    def __init__(self):
        super().__init__('simple_yolo_gemini')
        
        self.device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")
        self.get_logger().info(f">>> Gemini Vision System (Simple Mode): {self.device}")
        self.bridge = CvBridge()

        # 모델 로드 (기본 YOLO 모델 사용)
        self.get_logger().info(f">>> Loading YOLO Model ({YOLO_MODEL})...")
        self.yolo = YOLO(YOLO_MODEL)

        # 통신
        self.sub = self.create_subscription(Image, '/camera/image_raw', self.image_callback, 10)
        self.pub = self.create_publisher(Detection2DArray, '/detections', 10)
        self.result_pub = self.create_publisher(Image, '/yolo_result', 10)

        self.get_logger().info('>>> [준비 완료] 모든 사람(Person)을 추적합니다.')

    def image_callback(self, msg):
        try:
            frame_raw = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except Exception as e:
            return

        # 리사이즈 (연산 속도 향상)
        frame = cv2.resize(frame_raw, (PROCESS_WIDTH, PROCESS_HEIGHT))
        
        # YOLO 추론 (Track 모드 아님, 단순 Detect)
        results = self.yolo(frame, verbose=False, classes=0, conf=CONFIDENCE_THRESHOLD) # classes=0 (Person)
        boxes = results[0].boxes

        detection_array = Detection2DArray()
        detection_array.header = msg.header

        # 시각화용
        annotated_frame = results[0].plot()

        # 가장 큰 사람(가장 가까운 사람) 하나만 골라서 보냄 (PID 추적 대상)
        max_area = 0
        target_box = None

        if boxes:
            for box in boxes:
                xyxy = box.xyxy[0].tolist()
                area = (xyxy[2] - xyxy[0]) * (xyxy[3] - xyxy[1])
                if area > max_area:
                    max_area = area
                    target_box = box

        if target_box:
            # 타겟 박스 정보 추출
            bx, by, bw, bh = target_box.xywh[0].tolist()
            
            # 메시지 생성
            det = Detection2D()
            det.bbox.center.position.x = float(bx)
            det.bbox.center.position.y = float(by)
            det.bbox.size_x = float(bw)
            det.bbox.size_y = float(bh)
            det.id = "1001" # Follower 노드가 인식하도록 1000번대 ID 부여
            
            detection_array.detections.append(det)
            
            # 시각화: 타겟 강조
            x1, y1, x2, y2 = map(int, target_box.xyxy[0].tolist())
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 0, 255), 3)
            cv2.putText(annotated_frame, "TARGET", (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        # 발행
        self.pub.publish(detection_array)
        out_msg = self.bridge.cv2_to_imgmsg(annotated_frame, encoding="bgr8")
        self.result_pub.publish(out_msg)

def main():
    rclpy.init()
    node = SimpleYoloGemini()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()