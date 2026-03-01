import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from std_msgs.msg import Float32MultiArray
import cv2
import torch
import numpy as np
from ultralytics import YOLO
from torchreid.utils import FeatureExtractor
import math

# === 설정 ===
YOLO_MODEL = 'yolo26n.pt'
REID_MODEL = 'osnet_x0_25'
DEPTH_MODEL_TYPE = "MiDaS_small" # 가장 가벼운 모델
CONF_THRESHOLD = 0.6         # ReID 유사도 임계값

class YoloDepthFusion(Node):
    def __init__(self):
        super().__init__('yolo_depth_fusion')
        
        # 1. Pub/Sub 설정
        # 결과 발행: [각도(degree), 거리(meter)]
        self.target_pub = self.create_publisher(Float32MultiArray, '/target_info', 10)
        # 라이다 구독
        self.create_subscription(LaserScan, '/scan', self.lidar_callback, 10)
        
        # 2. 모델 로드 (YOLO + ReID + MiDaS)
        self.device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")
        
        self.get_logger().info(f">>> Loading YOLO({YOLO_MODEL}) & ReID({REID_MODEL})...")
        self.yolo = YOLO(YOLO_MODEL)
        
        # ReID 추출기
        self.reid = FeatureExtractor(
            model_name=REID_MODEL, 
            device=self.device.type, 
            image_size=(256, 128)
        )
        
        self.get_logger().info(">>> Loading MiDaS Depth Model...")
        self.depth_model = torch.hub.load("intel-isl/MiDaS", DEPTH_MODEL_TYPE)
        self.depth_model.to(self.device)
        self.depth_model.eval()
        
        # MiDaS용 전처리 함수
        midas_transforms = torch.hub.load("intel-isl/MiDaS", "transforms")
        self.transform = midas_transforms.small_transform

        # 3. 변수 초기화
        self.cap = cv2.VideoCapture(0)
        self.cap.set(3, 640)
        self.cap.set(4, 480)
        
        # 라이다 데이터 저장소
        self.lidar_ranges = []
        self.lidar_info = None 
        
        # 추적 관련 상태 변수 (Code A의 핵심 로직 이식)
        self.mode = "REGISTER"
        self.owner_embedding = None
        self.temp_embeddings = [] # 등록 시 평균을 내기 위한 버퍼
        self.tracking_id = -1     # 현재 추적 중인 YOLO ID
        self.scale_factor = 1.0   # Depth -> Meter 변환 계수 (자동 학습)
        
        # 30 FPS 타이머
        self.timer = self.create_timer(0.033, self.process_frame)

    def lidar_callback(self, msg):
        self.lidar_ranges = msg.ranges
        self.lidar_info = (msg.angle_min, msg.angle_increment)

    def get_lidar_dist(self, angle_deg):
        """특정 각도의 라이다 거리 반환"""
        if not self.lidar_ranges or self.lidar_info is None: return None
        
        angle_rad = math.radians(angle_deg)
        angle_min, angle_inc = self.lidar_info
        
        try:
            # 인덱스 계산 (라이다 설치 방향에 따라 180도 보정 필요할 수 있음)
            index = int((angle_rad - angle_min) / angle_inc)
            if 0 <= index < len(self.lidar_ranges):
                d = self.lidar_ranges[index]
                # 유효 거리 필터링 (0.1m ~ 10m)
                return d if 0.1 < d < 10.0 else None
        except:
            pass
        return None

    def get_embedding(self, frame, box):
        x1, y1, x2, y2 = map(int, box)
        h, w, _ = frame.shape
        # 좌표 클리핑
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        
        crop = frame[y1:y2, x1:x2]
        if crop.size == 0: return None
        
        # ReID 특징 추출
        return self.reid(crop).cpu().detach().numpy()

    def process_frame(self):
        ret, frame = self.cap.read()
        if not ret: return
        
        h, w, _ = frame.shape
        
        # === 1. YOLO 탐지 및 트래킹 ===
        # persist=True로 설정하여 ID 유지
        results = self.yolo.track(frame, persist=True, classes=0, verbose=False)
        boxes = results[0].boxes
        
        target_box = None
        
        # =========================================
        # [모드 1] 주인 등록 (안정화 로직 추가됨)
        # =========================================
        if self.mode == "REGISTER":
            cv2.putText(frame, "REGISTER: Stand Center & Wait...", (20, 40), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            cv2.putText(frame, f"Progress: {len(self.temp_embeddings)}/50", (20, 80), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            
            if boxes:
                # 화면 중앙에 가장 가까운(면적이 큰) 사람 찾기
                areas = [(box.xyxy[0][2]-box.xyxy[0][0])*(box.xyxy[0][3]-box.xyxy[0][1]) for box in boxes]
                target_idx = np.argmax(areas)
                target_box_reg = boxes[target_idx]
                
                # 특징 추출 및 저장
                emb = self.get_embedding(frame, target_box_reg.xyxy[0].tolist())
                if emb is not None:
                    self.temp_embeddings.append(emb)
                    
                    # 시각화
                    x1, y1, x2, y2 = map(int, target_box_reg.xyxy[0])
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 3)

            # 50프레임(약 2초) 모으면 평균 내서 등록
            if len(self.temp_embeddings) >= 50:
                self.owner_embedding = np.mean(self.temp_embeddings, axis=0)
                self.owner_embedding /= np.linalg.norm(self.owner_embedding)
                self.mode = "TRACK"
                self.temp_embeddings = [] # 초기화
                self.get_logger().info(">>> Owner Registered Successfully!")

        # =========================================
        # [모드 2] 주인 추적 (ID 우선 + ReID 보정)
        # =========================================
        elif self.mode == "TRACK":
            found_by_id = False
            
            # 2-1. [우선순위 1] ID로 먼저 찾기 (빠름)
            if self.tracking_id != -1:
                for box in boxes:
                    if box.id is not None and int(box.id) == self.tracking_id:
                        target_box = box.xyxy[0].tolist()
                        found_by_id = True
                        break
            
            # 2-2. [우선순위 2] ID를 놓쳤다면 ReID로 다시 찾기 (느리지만 정확)
            if not found_by_id:
                best_sim = 0.0
                best_box_obj = None
                
                for box in boxes:
                    if box.id is None: continue
                    xyxy = box.xyxy[0].tolist()
                    
                    # 특징 추출
                    emb = self.get_embedding(frame, xyxy)
                    if emb is None: continue
                    emb /= np.linalg.norm(emb)
                    
                    # 코사인 유사도
                    sim = np.dot(self.owner_embedding, emb.T)
                    
                    if sim > CONF_THRESHOLD and sim > best_sim:
                        best_sim = sim
                        best_box_obj = box
                
                # 주인을 다시 찾았다면 ID 갱신
                if best_box_obj is not None:
                    target_box = best_box_obj.xyxy[0].tolist()
                    self.tracking_id = int(best_box_obj.id)
                    cv2.putText(frame, f"RE-ID Success ({best_sim:.2f})", (20, 100), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        # =========================================
        # [공통] Depth Map 생성 & 센서 퓨전
        # =========================================
        if target_box:
            x1, y1, x2, y2 = map(int, target_box)
            cx = (x1 + x2) / 2
            
            # (1) Depth Map 생성 (MiDaS) - 타겟이 있을 때만 수행 (성능 최적화)
            img_batch = self.transform(frame).to(self.device)
            with torch.no_grad():
                prediction = self.depth_model(img_batch)
                prediction = torch.nn.functional.interpolate(
                    prediction.unsqueeze(1),
                    size=frame.shape[:2],
                    mode="bicubic",
                    align_corners=False,
                ).squeeze()
            depth_map = prediction.cpu().numpy()
            
            # (2) 주인 영역 Depth 추출
            pad_x = int((x2-x1)*0.2)
            pad_y = int((y2-y1)*0.2)
            # 패딩 예외처리
            if pad_x > 0 and pad_y > 0:
                owner_roi = depth_map[y1+pad_y:y2-pad_y, x1+pad_x:x2-pad_x]
            else:
                owner_roi = depth_map[y1:y2, x1:x2]
                
            visual_depth_raw = np.mean(owner_roi) if owner_roi.size > 0 else 0
            
            # (3) 각도 및 거리 계산
            fov_x = 60.0
            angle_deg = ((cx / w) - 0.5) * fov_x
            lidar_dist = self.get_lidar_dist(angle_deg)
            
            # (4) 센서 퓨전 (Weighted Average)
            final_dist = 0.0
            status_text = "Vision"
            
            if lidar_dist is not None:
                # 퓨전: 라이다 70% + 비전 30%
                scale_guess = self.scale_factor / (visual_depth_raw + 1e-6)
                final_dist = (lidar_dist * 0.7) + (scale_guess * 0.3)
                
                # 스케일 팩터 학습
                current_scale = lidar_dist * visual_depth_raw
                self.scale_factor = 0.95 * self.scale_factor + 0.05 * current_scale
                status_text = "Fusion"
            else:
                # 라이다 없으면 비전만 사용
                final_dist = self.scale_factor / (visual_depth_raw + 1e-6)
                status_text = "VisionOnly"

            # (5) 결과 발행 (ROS 2 Topic)
            msg = Float32MultiArray()
            msg.data = [float(angle_deg), float(final_dist)]
            self.target_pub.publish(msg)
            
            # 시각화
            color = (0, 255, 0) if self.tracking_id != -1 else (0, 0, 255)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, f"{status_text}: {final_dist:.2f}m / {angle_deg:.1f}dg", 
                       (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        else:
             cv2.putText(frame, "SEARCHING OWNER...", (20, 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

        # 화면 출력
        cv2.imshow("Sensor Fusion Tracker", frame)
        
        # 키 입력 처리 ('r' 누르면 재등록, 'q' 종료)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            rclpy.shutdown()
        elif key == ord('r'):
            self.mode = "REGISTER"
            self.temp_embeddings = []
            self.tracking_id = -1
            self.get_logger().info(">>> Reset Registration Mode")

def main(args=None):
    rclpy.init(args=args)
    node = YoloDepthFusion()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
        cv2.destroyAllWindows()

if __name__ == '__main__':
    main()