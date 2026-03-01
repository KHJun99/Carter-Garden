import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
from vision_msgs.msg import Detection2DArray, Detection2D
import cv2
import torch
import numpy as np
from ultralytics import YOLO
from torchreid.utils import FeatureExtractor
# FaceAnalysis는 현재 루프에서 사용하지 않으므로 주석 처리 가능
# from insightface.app import FaceAnalysis

YOLO_MODEL = 'yolo11n.pt'
REID_MODEL = 'osnet_x0_25'
LOOSE_DIST_THRESHOLD = 1.1

class SmartYoloDetector(Node):
    def __init__(self):
        super().__init__('smart_yolo_detector')
        self.device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")
        self.bridge = CvBridge()

        # 1. 모델 로드
        self.yolo = YOLO(YOLO_MODEL)
        self.reid = FeatureExtractor(model_name=REID_MODEL, device=self.device.type, image_size=(256, 128))
        
        # 얼굴 인식 모델을 안 쓴다면 아래 두 줄을 주석 처리하여 VRAM을 절약하세요.
        # self.face_app = FaceAnalysis(providers=['CUDAExecutionProvider' if torch.cuda.is_available() else 'CPUExecutionProvider'])
        # self.face_app.prepare(ctx_id=0, det_size=(320, 320))

        self.owner_gallery = []

        # 3. ROS 통신
        self.sub = self.create_subscription(Image, '/camera/image_raw', self.image_callback, 10)
        self.pub = self.create_publisher(Detection2DArray, '/detections', 10)
        self.result_pub = self.create_publisher(Image, '/yolo_result', 10)

        self.get_logger().info('객체 인식 및 시뮬레이션 최적화 주인 식별 노드가 시작되었습니다.')

    def get_body_embedding(self, frame, box):
        x1, y1, x2, y2 = map(int, box)
        h, w, _ = frame.shape
        x1, y1, x2, y2 = max(0, x1), max(0, y1), min(w, x2), min(h, y2)
        crop = frame[y1:y2, x1:x2]
        if crop.size == 0: return None
        return self.reid(crop).cpu().detach().numpy()

    def image_callback(self, msg):
        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')

        # YOLO 트래킹
        results = self.yolo.track(frame, persist=True, classes=0, verbose=False, imgsz=320)
        boxes = results[0].boxes

        detection_array = Detection2DArray()
        detection_array.header = msg.header

        if boxes:
            for box in boxes:
                if box.id is None: continue

                obj_id = int(box.id)
                xyxy = box.xyxy[0].tolist()
                
                # 1. 일반 인식 표시 (파란색)
                bx1, by1, bx2, by2 = map(int, xyxy)
                cv2.rectangle(frame, (bx1, by1), (bx2, by2), (255, 0, 0), 1)
                cv2.putText(frame, f"Person {obj_id}", (bx1, by1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)

                # 2. 주인 매칭 로직
                curr_body = self.get_body_embedding(frame, xyxy)
                is_owner = False

                if curr_body is not None:
                    curr_body /= np.linalg.norm(curr_body)
                    
                    if len(self.owner_gallery) == 0:
                        self.owner_gallery.append(curr_body)
                        is_owner = True
                        self.get_logger().info("★★★ OWNER REGISTERED ★★★")
                    else:
                        dists = [np.linalg.norm(g - curr_body) for g in self.owner_gallery]
                        min_d = min(dists)

                        if min_d < LOOSE_DIST_THRESHOLD:
                            is_owner = True
                            # 특징 업데이트 (들여쓰기 수정됨)
                            if min_d < 0.5 and len(self.owner_gallery) < 50:
                                self.owner_gallery.append(curr_body)

                # 3. 주인 표시 및 데이터 발행
                if is_owner:
                    cv2.rectangle(frame, (bx1, by1), (bx2, by2), (0, 255, 0), 3)
                    cv2.putText(frame, "OWNER LOCKED", (bx1, by1-25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

                det = Detection2D()
                det.bbox.center.position.x = float(box.xywh[0][0])
                det.bbox.center.position.y = float(box.xywh[0][1])
                det.bbox.size_x = float(box.xywh[0][2])
                det.bbox.size_y = float(box.xywh[0][3])
                # 주인 식별 ID 전송
                det.id = str(obj_id + (1000 if is_owner else 0))
                detection_array.detections.append(det)

        self.pub.publish(detection_array)
        self.result_pub.publish(self.bridge.cv2_to_imgmsg(frame, encoding="bgr8"))

def main():
    rclpy.init()
    node = SmartYoloDetector()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
