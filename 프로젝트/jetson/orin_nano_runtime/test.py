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
from sensor_msgs.msg import Image
from std_msgs.msg import String
from cv_bridge import CvBridge
from vision_msgs.msg import Detection2DArray, Detection2D
from ultralytics import YOLO
from torchreid.utils import FeatureExtractor

# [메모리 최적화 설정]
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "max_split_size_mb:32,expandable_segments:True"

# [모델 경로 설정]
current_dir = os.path.dirname(os.path.abspath(__file__))
# nodes/ 폴더 내에 있으므로 모델을 찾으려면 한 단계 위로 올라가야 함
YOLO_MODEL = os.path.abspath(os.path.join(current_dir, 'models', 'yolo11n.engine'))
REID_MODEL = 'osnet_x0_25'

# [하이퍼파라미터]
STRICT_DIST_THRESHOLD = 0.5
LOOSE_DIST_THRESHOLD = 0.70
MIN_HEIGHT_PIXELS = 100
SKIP_FRAMES = 3

MAX_GALLERY_SIZE = 100
GALLERY_UPDATE_INTERVAL = 1.0
REGISTRATION_SIM_THRESHOLD = 0.94
DYNAMIC_ADD_THRESHOLD = 0.94

class SmartYoloDetector(Node):
    def __init__(self):
        super().__init__('smart_yolo_detector')

        try:
            self.declare_parameter('use_sim_time', False)
        except Exception:
            pass

        # 1. 디바이스 설정: TensorRT를 위해 GPU(CUDA) 사용
        self.device = torch.device("cuda")
        self.get_logger().info(f">>> [TensorRT Mode] Device: {self.device}")

        self.bridge = CvBridge()

        # 2. YOLO TensorRT 모델 로드
        self.get_logger().info(f">>> Loading TensorRT Engine ({YOLO_MODEL})...")
        self.yolo = YOLO(YOLO_MODEL)

        # 3. ReID 모델 설정: GPU 메모리 절약을 위해 CPU 유지
        self.reid_device = torch.device("cpu")
        self.get_logger().info(f">>> Loading ReID ({REID_MODEL}) on CPU (Memory Diet Mode)...")

        self.reid = FeatureExtractor(
            model_name=REID_MODEL,
            device='cpu',
            image_size=(256, 128)
        )

        # 상태 변수 초기화
        self.is_active = False
        self.mode = "REGISTER"
        self.last_capture_time = 0
        self.global_id_counter = 1
        self.owner_gallery = []
        self.owner_global_id = None
        self.confirmed_yolo_id = -1
        self.last_gallery_update_time = 0
        self.temp_body_embs = []
        self.frame_count = 0
        self.cached_results = {}

        # ROS 통신 설정
        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10
        )
        self.sub = self.create_subscription(Image, '/image_raw', self.image_callback, qos_profile)
        self.mode_sub = self.create_subscription(String, '/robot/mode', self.mode_toggle_callback, 10)
        self.pub = self.create_publisher(Detection2DArray, '/detections', 10)
        self.result_pub = self.create_publisher(Image, '/yolo_result', 10)
        self.status_pub = self.create_publisher(String, '/robot/status', 10)

        self.get_logger().info('>>> [준비 완료] Smart YOLO Detector (TensorRT GPU Mode)')

    def get_body_embedding(self, frame, box):
        x1, y1, x2, y2 = map(int, box)
        h, w, _ = frame.shape
        if (y2 - y1) < MIN_HEIGHT_PIXELS: return None
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        crop = frame[y1:y2, x1:x2]
        if crop.size == 0: return None
        features = self.reid(crop)
        return features.detach().numpy()

    def update_gallery(self, body_emb):
        current_time = time.time()
        if current_time - self.last_gallery_update_time < GALLERY_UPDATE_INTERVAL:
            return
        norm_emb = body_emb / np.linalg.norm(body_emb)
        if len(self.owner_gallery) > 0:
            sims = [np.dot(g, norm_emb.T).item() for g in self.owner_gallery]
            if max(sims) > DYNAMIC_ADD_THRESHOLD:
                return
        if len(self.owner_gallery) >= MAX_GALLERY_SIZE:
            self.owner_gallery.pop(0)
        self.owner_gallery.append(norm_emb)
        self.last_gallery_update_time = current_time

    def mode_toggle_callback(self, msg):
        mode = msg.data.upper()
        if mode == "REGISTER":
            self.get_logger().info(">>> 사용자 등록 리셋")
            self.is_active = True
            self.mode = "REGISTER"
            self.owner_gallery = []
            self.owner_global_id = None
            self.temp_body_embs = []
            self.confirmed_yolo_id = -1
            gc.collect()
            torch.cuda.empty_cache()
        elif mode == "FOLLOW":
            if not self.is_active:
                self.is_active = True
                self.mode = "TRACK" if self.owner_global_id is not None else "REGISTER"

    def image_callback(self, msg):
        if not self.is_active: return
        gc.collect()
        torch.cuda.empty_cache()

        try:
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            yuv = cv2.cvtColor(frame, cv2.COLOR_BGR2YUV)
            y, u, v = cv2.split(yuv)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            y = clahe.apply(y)
            frame = cv2.cvtColor(cv2.merge((y, u, v)), cv2.COLOR_YUV2BGR)
        except Exception as e:
            self.get_logger().error(f"Error: {e}")
            return

        self.frame_count += 1

        # YOLO TensorRT 추론 (imgsz=320 필히 준수)
        with torch.no_grad():
            results = self.yolo.track(
                frame,
                persist=True,
                classes=0,
                verbose=False,
                imgsz=320,
                half=True
            )

        boxes = results[0].boxes
        detection_array = Detection2DArray()
        detection_array.header = msg.header
        target_box_vis = None

        if self.mode == "REGISTER":
            cv2.putText(frame, f"REGISTERING...", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            if boxes:
                areas = [((b.xyxy[0][2]-b.xyxy[0][0])*(b.xyxy[0][3]-b.xyxy[0][1])).cpu().item() for b in boxes]
                reg_box = boxes[np.argmax(areas)]
                current_time = time.time()
                if current_time - self.last_capture_time > 0.1:
                    xyxy = reg_box.xyxy[0].tolist()
                    body_emb = self.get_body_embedding(frame, xyxy)
                    if body_emb is not None:
                        self.temp_body_embs.append(body_emb)
                        self.last_capture_time = current_time

                cnt = len(self.temp_body_embs)
                cv2.putText(frame, f"Captured: {cnt}/40", (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                if cnt >= 40:
                    self.owner_gallery = [e / np.linalg.norm(e) for e in self.temp_body_embs]
                    self.owner_global_id = self.global_id_counter
                    self.global_id_counter += 1
                    self.mode = "TRACK"
                    self.temp_body_embs = []
                    status_msg = String()
                    status_msg.data = "REGISTER_DONE"
                    self.status_pub.publish(status_msg)

        elif self.mode == "TRACK":
            run_heavy_tasks = (self.frame_count % SKIP_FRAMES == 0)
            for box in boxes:
                if box.id is None: continue
                obj_id = int(box.id)
                xyxy = box.xyxy[0].tolist()
                bx1, by1, bx2, by2 = map(int, xyxy)

                if obj_id not in self.cached_results:
                    self.cached_results[obj_id] = (1.0, False)

                min_dist, is_match = self.cached_results[obj_id]
                is_confirmed_id = (obj_id == self.confirmed_yolo_id)

                if run_heavy_tasks or min_dist == 1.0:
                    curr_body = self.get_body_embedding(frame, xyxy)
                    if curr_body is not None:
                        raw_emb = curr_body.copy()
                        curr_body /= np.linalg.norm(curr_body)
                        dists = [np.linalg.norm(g - curr_body) for g in self.owner_gallery]
                        min_dist = min(dists) if dists else 1.0

                        if is_confirmed_id:
                            is_match = min_dist < LOOSE_DIST_THRESHOLD
                            if min_dist < STRICT_DIST_THRESHOLD: self.update_gallery(raw_emb)
                        else:
                            if min_dist < STRICT_DIST_THRESHOLD:
                                is_match = True
                                self.confirmed_yolo_id = obj_id
                    self.cached_results[obj_id] = (min_dist, is_match)

                det = Detection2D()
                det.id = str(obj_id + 1000 if is_match else obj_id)
                detection_array.detections.append(det)

                color = (0, 255, 0) if is_match else (255, 0, 0)
                cv2.rectangle(frame, (bx1, by1), (bx2, by2), color, 2 if is_match else 1)
                if is_match: target_box_vis = xyxy

        self.pub.publish(detection_array)
        out_msg = self.bridge.cv2_to_imgmsg(frame, encoding="bgr8")
        out_msg.header = msg.header
        self.result_pub.publish(out_msg)

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