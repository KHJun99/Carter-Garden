import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
from vision_msgs.msg import Detection2DArray, Detection2D
import cv2
import torch
import numpy as np
from ultralytics import YOLO
from torchreid.utils import FeatureExtractor
import time
import os
from insightface.app import FaceAnalysis

# =========================================================
# [설정 및 하이퍼파라미터] - yolo_best_model.py 기반
# =========================================================
current_dir = os.path.dirname(os.path.abspath(__file__))
YOLO_MODEL = os.path.join(current_dir, 'models', 'yolo11n.pt')
REID_MODEL = 'osnet_x0_25' 

# 1. 판별 기준값
STRICT_DIST_THRESHOLD = 0.5    # 처음 찾을 때 (엄격)
LOOSE_DIST_THRESHOLD = 0.70    # 트래킹 중일 때 (널널)
FACE_SIM_THRESHOLD = 0.4       
MIN_HEIGHT_PIXELS = 100        
SKIP_FRAMES = 3                

# 2. 갤러리 및 데이터 다양성 설정
MAX_GALLERY_SIZE = 100         
GALLERY_UPDATE_INTERVAL = 1.0  

# 데이터 편향 방지 임계값
REGISTRATION_SIM_THRESHOLD = 0.94
DYNAMIC_ADD_THRESHOLD = 0.94

# 이미지 처리
PROCESS_WIDTH = 640
PROCESS_HEIGHT = 480 # yolo_best_model은 480 사용, follower_node와 맞춤

from std_msgs.msg import String

class SmartYoloDetector(Node):
    def __init__(self):
        super().__init__('smart_yolo_detector')
        try:
            self.declare_parameter('use_sim_time', False)
        except Exception:
            pass
        
        # 1. 디바이스 설정
        self.device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")
        self.get_logger().info(f">>> Device: {self.device}")
        
        self.bridge = CvBridge()

        # 2. 모델 로드 (시작 시 한 번만)
        self.get_logger().info(f">>> Loading YOLO ({YOLO_MODEL})...")
        self.yolo = YOLO(YOLO_MODEL)
        
        self.get_logger().info(f">>> Loading ReID ({REID_MODEL})...")
        self.reid = FeatureExtractor(
            model_name=REID_MODEL, 
            device=self.device.type, 
            image_size=(256, 128)
        )

        self.get_logger().info(">>> Loading InsightFace...")
        providers = ['CUDAExecutionProvider'] if torch.cuda.is_available() else ['CPUExecutionProvider']
        self.face_app = FaceAnalysis(providers=providers)
        self.face_app.prepare(ctx_id=0, det_size=(320, 320))
        
        # 3. 상태 변수
        self.is_active = False # 기본값은 비활성
        self.mode = "REGISTER"
        self.last_capture_time = 0
        self.global_id_counter = 1
        
        # === 데이터 저장소 ===
        self.owner_gallery = []      
        self.owner_face_emb = None   
        self.owner_global_id = None
        
        self.confirmed_yolo_id = -1
        self.last_gallery_update_time = 0
        self.temp_body_embs = []     
        self.temp_face_embs = []     
        self.frame_count = 0
        self.cached_results = {}     

        # 4. ROS 통신
        # [수정] QoS 설정: Best Effort (Gazebo 호환)
        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=10
        )
        self.sub = self.create_subscription(Image, '/camera/image_raw', self.image_callback, qos_profile)
        self.mode_sub = self.create_subscription(String, '/robot/mode', self.mode_toggle_callback, 10)
        self.pub = self.create_publisher(Detection2DArray, '/detections', 10)
        self.result_pub = self.create_publisher(Image, '/yolo_result', 10)
        self.status_pub = self.create_publisher(String, '/robot/status', 10)

        self.get_logger().info('>>> [준비 완료] Smart YOLO Detector (Memory Resident)')

    def get_simple_dist(self, box):
        _, y1, _, y2 = map(int, box)
        h = y2 - y1
        if h < 1: return 0.0
        return 500.0 / h 

    def get_body_embedding(self, frame, box):
        x1, y1, x2, y2 = map(int, box)
        h, w, _ = frame.shape
        if (y2 - y1) < MIN_HEIGHT_PIXELS: return None
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        crop = frame[y1:y2, x1:x2]
        if crop.size == 0: return None
        return self.reid(crop).cpu().detach().numpy()

    def get_face_embedding(self, frame, box):
        x1, y1, x2, y2 = map(int, box)
        h, w, _ = frame.shape
        pad_x = int((x2-x1)*0.1)
        pad_y = int((y2-y1)*0.1)
        x1 = max(0, x1 - pad_x)
        y1 = max(0, y1 - pad_y)
        x2 = min(w, x2 + pad_x)
        y2 = min(h, y2 + pad_y)
        person_img = frame[y1:y2, x1:x2]
        if person_img.size == 0: return None
        
        # InsightFace는 BGR 이미지를 기대함
        faces = self.face_app.get(person_img)
        if len(faces) > 0:
            faces.sort(key=lambda x: (x.bbox[2]-x.bbox[0]) * (x.bbox[3]-x.bbox[1]), reverse=True)
            return faces[0].embedding 
        return None

    def update_gallery(self, body_emb):
        current_time = time.time()
        if current_time - self.last_gallery_update_time < GALLERY_UPDATE_INTERVAL:
            return

        norm_emb = body_emb / np.linalg.norm(body_emb)

        if len(self.owner_gallery) > 0:
            sims = [np.dot(g, norm_emb.T).item() for g in self.owner_gallery]
            max_sim = max(sims)
            
            if max_sim > DYNAMIC_ADD_THRESHOLD:
                return 

        if len(self.owner_gallery) >= MAX_GALLERY_SIZE:
            self.owner_gallery.pop(0) 
        
        self.owner_gallery.append(norm_emb)
        self.last_gallery_update_time = current_time
        # self.get_logger().info(f">>> Gallery Updated! Size: {len(self.owner_gallery)}")

    def mode_toggle_callback(self, msg):
        mode = msg.data.upper()
        if mode == "FOLLOW":
            if not self.is_active:
                self.get_logger().info(">>> 추적 모드 활성화 (Inference ON)")
                self.is_active = True
                # 이미 등록된 주인이 있다면 바로 TRACK 모드로 복귀
                if self.owner_global_id is not None:
                    self.mode = "TRACK"
                    self.get_logger().info(f">>> 기존 주인(ID:{self.owner_global_id}) 추적 재개")
                else:
                    self.mode = "REGISTER"
        else:
            if self.is_active:
                self.get_logger().info(">>> 추적 모드 비활성화 (Inference OFF)")
                self.is_active = False

    def image_callback(self, msg):
        # 활성화 상태가 아니면 무거운 연산을 하지 않고 즉시 리턴
        if not self.is_active:
            return

        try:
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except Exception as e:
            return

        # 리사이즈 (연산 효율성)
        # frame = cv2.resize(frame, (PROCESS_WIDTH, PROCESS_HEIGHT))
        h, w, _ = frame.shape
        self.frame_count += 1

        results = self.yolo.track(frame, persist=True, classes=0, verbose=False, imgsz=320)
        boxes = results[0].boxes
        
        detection_array = Detection2DArray()
        detection_array.header = msg.header
        
        target_box_vis = None

        # ============================================
        # [모드 1] REGISTER
        # ============================================
        if self.mode == "REGISTER":
            cv2.putText(frame, f"REGISTER ID: {self.global_id_counter}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # ROS 파라미터나 토픽으로 모드 변경을 받을 수도 있지만, 
            # 여기서는 편의상 로직 내에서 처리 (실제로는 별도 트리거 필요할 수 있음)
            # 일단 가장 큰 사람을 자동으로 등록 절차 진행
            
            if boxes:
                areas = [((b.xyxy[0][2]-b.xyxy[0][0])*(b.xyxy[0][3]-b.xyxy[0][1])).cpu().item() for b in boxes]
                target_idx = np.argmax(areas)
                reg_box = boxes[target_idx]
                
                current_time = time.time()
                captured_this_frame = False
                warning_msg = None
                
                if current_time - self.last_capture_time > 0.1:
                    xyxy = reg_box.xyxy[0].tolist()
                    body_emb = self.get_body_embedding(frame, xyxy)
                    face_emb = self.get_face_embedding(frame, xyxy)
                    
                    if body_emb is not None:
                        is_diverse = True
                        if len(self.temp_body_embs) > 0:
                            last_emb = self.temp_body_embs[-1]
                            curr_norm = body_emb / np.linalg.norm(body_emb)
                            last_norm = last_emb / np.linalg.norm(last_emb)
                            sim = np.dot(curr_norm, last_norm.T).item()
                            
                            if sim > REGISTRATION_SIM_THRESHOLD:
                                is_diverse = False
                        
                        if is_diverse:
                            self.temp_body_embs.append(body_emb)
                            if face_emb is not None:
                                self.temp_face_embs.append(face_emb)
                            self.last_capture_time = current_time
                            captured_this_frame = True
                        else:
                            warning_msg = "TURN AROUND!"

                x1, y1, x2, y2 = map(int, reg_box.xyxy[0])
                if captured_this_frame:
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 5)
                elif warning_msg:
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 255), 2)
                    cv2.putText(frame, warning_msg, (x1, y1-20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                else:
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 1)

                cnt = len(self.temp_body_embs)
                target_cnt = 40 
                cv2.putText(frame, f"Collected: {cnt}/{target_cnt}", (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

                if cnt >= target_cnt:
                    self.owner_gallery = [e / np.linalg.norm(e) for e in self.temp_body_embs]
                    if len(self.temp_face_embs) > 0:
                        avg_face = np.mean(self.temp_face_embs, axis=0)
                        self.owner_face_emb = avg_face / np.linalg.norm(avg_face)
                    else:
                        self.owner_face_emb = None
                        
                    self.owner_global_id = self.global_id_counter
                    self.global_id_counter += 1
                    self.confirmed_yolo_id = -1
                    
                    self.mode = "TRACK"
                    self.temp_body_embs = []
                    self.temp_face_embs = []
                    
                    # 프론트엔드에 등록 완료 알림 전송
                    status_msg = String()
                    status_msg.data = "REGISTER_DONE"
                    self.status_pub.publish(status_msg)
                    
                    self.get_logger().info(f">>> Registered! Gallery Size: {len(self.owner_gallery)}")

        # ============================================
        # [모드 2] TRACK
        # ============================================
        elif self.mode == "TRACK":
            run_heavy_tasks = (self.frame_count % SKIP_FRAMES == 0)
            
            for box in boxes:
                if box.id is None: continue
                obj_id = int(box.id)
                xyxy = box.xyxy[0].tolist()
                bx1, by1, bx2, by2 = map(int, xyxy)
                
                if obj_id not in self.cached_results:
                    self.cached_results[obj_id] = (1.0, 0.0, False)
                
                min_dist, face_score, is_match = self.cached_results[obj_id]
                is_confirmed_id = (obj_id == self.confirmed_yolo_id)
                
                if run_heavy_tasks or min_dist == 1.0:
                    curr_body = self.get_body_embedding(frame, xyxy)
                    
                    if curr_body is not None:
                        raw_body_emb = curr_body.copy() 
                        curr_body /= np.linalg.norm(curr_body)
                        dists = [np.linalg.norm(g - curr_body) for g in self.owner_gallery]
                        min_dist = min(dists) if dists else 1.0
                    else:
                        raw_body_emb = None

                    face_score = 0.0
                    has_face = False
                    if self.owner_face_emb is not None:
                        curr_face = self.get_face_embedding(frame, xyxy)
                        if curr_face is not None:
                            curr_face /= np.linalg.norm(curr_face)
                            face_score = np.dot(self.owner_face_emb, curr_face)
                            has_face = True
                    
                    is_match = False
                    
                    if has_face and face_score > FACE_SIM_THRESHOLD:
                        is_match = True
                        self.confirmed_yolo_id = obj_id
                        if raw_body_emb is not None:
                            self.update_gallery(raw_body_emb) 
                    else:
                        if is_confirmed_id:
                            if min_dist < LOOSE_DIST_THRESHOLD:
                                is_match = True
                                if min_dist < STRICT_DIST_THRESHOLD and raw_body_emb is not None:
                                    self.update_gallery(raw_body_emb)
                            else:
                                is_match = False
                                self.confirmed_yolo_id = -1 
                        else:
                            if min_dist < STRICT_DIST_THRESHOLD:
                                is_match = True
                                self.confirmed_yolo_id = obj_id 

                    self.cached_results[obj_id] = (min_dist, face_score, is_match)
                
                # ROS 메시지 생성
                det = Detection2D()
                det.bbox.center.position.x = float(box.xywh[0][0])
                det.bbox.center.position.y = float(box.xywh[0][1])
                det.bbox.size_x = float(box.xywh[0][2])
                det.bbox.size_y = float(box.xywh[0][3])
                
                # 주인 식별 ID 전송: 주인이면 1000 + ID
                final_id = obj_id
                if is_match:
                    final_id += 1000
                    target_box_vis = xyxy # 시각화용
                    
                det.id = str(final_id)
                detection_array.detections.append(det)

                # 시각화 (디버그용)
                label_text = f"ID:{obj_id}"
                if is_match:
                    color = (0, 255, 0)
                    label_text += " OWNER"
                    cv2.rectangle(frame, (bx1, by1), (bx2, by2), color, 2)
                else:
                    color = (255, 0, 0)
                    cv2.rectangle(frame, (bx1, by1), (bx2, by2), color, 1)
                cv2.putText(frame, label_text, (bx1, by1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

        # 주인 타겟 정보 표시
        if target_box_vis:
            x1, y1, x2, y2 = map(int, target_box_vis)
            cv2.putText(frame, "LOCKED", (x1, y1-25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        # 결과 발행
        self.pub.publish(detection_array)
        
        # 디버깅용 이미지 발행
        out_msg = self.bridge.cv2_to_imgmsg(frame, encoding="bgr8")
        self.result_pub.publish(out_msg)

import sys

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
