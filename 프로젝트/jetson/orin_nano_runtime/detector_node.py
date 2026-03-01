import sys
import os
import time
import numpy as np
import cv2
import torch
import gc

# torchreid 라이브러리 경로 추가
sys.path.insert(0, '/root/deep-person-reid')

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from sensor_msgs.msg import Image, CompressedImage 
from std_msgs.msg import String
from cv_bridge import CvBridge
from vision_msgs.msg import Detection2DArray, Detection2D
from ultralytics import YOLO
from torchreid.utils import FeatureExtractor

# [모델 경로] - 사용자가 직접 변환했던 엔진 파일 기준
current_dir = os.path.dirname(os.path.abspath(__file__))
YOLO_MODEL = os.path.join(current_dir, 'models', 'yolo11n.engine')
REID_MODEL = 'osnet_x0_25'

class SmartYoloDetector(Node):
    def __init__(self):
        super().__init__('smart_yolo_detector')

        # 초기 버전의 QoS 설정
        qos_fast = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10
        )

        # 하드웨어 및 모델 초기화
        self.device = torch.device("cuda")
        self.bridge = CvBridge()
        self.yolo = YOLO(YOLO_MODEL)
        self.reid = FeatureExtractor(model_name=REID_MODEL, device='cpu', image_size=(256, 128))

        # 상태 제어 변수
        self.is_active = False
        self.mode = "REGISTER"
        self.frame_count = 0
        
        self.owner_gallery = []
        self.confirmed_yolo_id = -1

        # 통신 설정 (화면이 나왔던 초기 토픽 및 타입 구성)
        self.sub = self.create_subscription(Image, '/image_raw', self.image_callback, qos_fast)
        self.result_pub = self.create_publisher(Image, '/yolo_result', 10) # Compressed가 아닌 일반 Image 방식
        self.pub = self.create_publisher(Detection2DArray, '/detections', 10)
        self.status_pub = self.create_publisher(String, '/robot/status', 10)
        self.mode_sub = self.create_subscription(String, '/robot/mode', self.mode_toggle_callback, 10)

        self.get_logger().info('>>> [복구 완료] 초기 엔진 버전으로 실행됩니다.')

    def image_callback(self, msg):
        if not self.is_active:
            return
        
        try:
            # 1. 이미지 변환
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            
            # 2. YOLO 추론 (끊김의 원인이었으나 화면은 나왔던 방식)
            with torch.no_grad():
                results = self.yolo.track(frame, persist=True, classes=0, verbose=False, imgsz=320, half=True)

            boxes = results[0].boxes
            detection_array = Detection2DArray()
            detection_array.header = msg.header
            
            # 3. 결과 시각화
            annotated_frame = results[0].plot()

            if self.mode == "TRACK" and boxes:
                for box in boxes:
                    if box.id is None: continue
                    obj_id = int(box.id)
                    
                    # ReID 검증 로직
                    xyxy = box.xyxy[0].tolist()
                    curr_body = self.get_body_embedding(frame, xyxy)
                    is_match = False
                    
                    if curr_body is not None:
                        curr_body /= np.linalg.norm(curr_body)
                        dists = [np.linalg.norm(g - curr_body) for g in self.owner_gallery]
                        if dists and min(dists) < 0.5:
                            is_match = True
                            self.confirmed_yolo_id = obj_id

                    det = Detection2D()
                    det.id = str(obj_id + 1000 if is_match else obj_id)
                    detection_array.detections.append(det)

            # 4. 결과 발행 (원본 크기 Image 그대로 전송 -> 끊김의 주요 원인이었음)
            self.pub.publish(detection_array)
            
            out_msg = self.bridge.cv2_to_imgmsg(annotated_frame, encoding="bgr8")
            out_msg.header = msg.header
            self.result_pub.publish(out_msg)

        except Exception as e:
            self.get_logger().error(f"Error: {e}")
        finally:
            self.frame_count += 1

    def get_body_embedding(self, frame, box):
        try:
            x1, y1, x2, y2 = map(int, box)
            crop = frame[max(0,y1):y2, max(0,x1):x2]
            if crop.size == 0: return None
            return self.reid(crop).detach().numpy()
        except:
            return None

    def mode_toggle_callback(self, msg):
        mode = msg.data.upper()
        if mode == "REGISTER":
            self.mode, self.owner_gallery, self.confirmed_yolo_id = "REGISTER", [], -1
            self.is_active = True
        elif mode == "FOLLOW":
            self.is_active, self.mode = True, "TRACK"

def main(args=None):
    rclpy.init(args=args)
    node = SmartYoloDetector()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main(sys.argv)