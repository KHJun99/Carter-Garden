import cv2
import torch
import numpy as np
from ultralytics import YOLO
from torchreid.utils import FeatureExtractor
import math
import time
import random
import os
from depth_anything_v2.dpt import DepthAnythingV2

# InsightFace 라이브러리
from insightface.app import FaceAnalysis

# === [설정] ===
YOLO_MODEL = 'yolo26n.pt'  # 모델명 확인
# 기존 (아주 가벼움)
#REID_MODEL = 'osnet_x0_25' 

# 변경 추천 1 (밸런스형)
#REID_MODEL = 'osnet_x1_0'

# 변경 추천 2 (정확도 중시)
# REID_MODEL = 'osnet_ain_x1_0'

# 2. [추천] 정확도 대폭 상승 (ResNet50 기반)
REID_MODEL = 'resnet50_fc512'

# 3. [대안] 조명 변화에 강함 (IBN)
# REID_MODEL = 'osnet_ibn_x1_0'

DEPTH_weights = "depth_anything_v2_vits.pth" 

# [핵심 변경] 유사도(0~1)가 아니라 '거리(Distance)'를 씁니다.
# 거리는 '낮을수록' 똑같은 사람입니다. (0에 가까울수록 완벽히 일치)
# 보통 같은 사람은 0.3 ~ 0.5 정도 나옵니다.
# 다른 사람은 0.7 ~ 1.0 이상 나옵니다.
DIST_THRESHOLD = 0.36  # 이 값보다 '작아야' 주인으로 인정 (엄격하게 잡음)

# 얼굴 인식 설정
FACE_CONF_THRESHOLD = 0.5 # 얼굴이 이 점수 이상이어야 주인으로 인정

# 너무 멀리 있는(작은) 사람은 ReID 하지 않음 (오탐지 방지)
MIN_HEIGHT_PIXELS = 100  # 사람 키가 100픽셀보다 작으면 무시
class LaptopFusionTest:
    def __init__(self):
        # 1. 디바이스 설정
        self.device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")
        print(f">>> Device: {self.device}")
        
        # 2. 모델 로드
        print(">>> Loading YOLO...")
        self.yolo = YOLO(YOLO_MODEL)
        
        print(">>> Loading ReID...")
        self.reid = FeatureExtractor(
            model_name=REID_MODEL, 
            device=self.device.type, 
            image_size=(384, 192)
        )
        
        print(">>> Loading InsightFace (Face)...")
        # 얼굴 탐지 및 인식 모델 초기화
        self.face_app = FaceAnalysis(providers=['CUDAExecutionProvider'] if torch.cuda.is_available() else ['CPUExecutionProvider'])
        self.face_app.prepare(ctx_id=0, det_size=(640, 640))

        # Depth 모델 로드
        print(">>> Loading Depth Anything V2...")
        try:
            model_configs = {'vits': {'encoder': 'vits', 'features': 64, 'out_channels': [48, 96, 192, 384]}}
            self.depth_model = DepthAnythingV2(**model_configs['vits'])
            self.depth_model.load_state_dict(torch.load(DEPTH_weights, map_location='cpu'))
            self.depth_model.to(self.device).eval()
        except:
            print("⚠️ Depth 모델 로드 실패. (파일 없음)")
            self.depth_model = None

        # 3. 카메라 및 변수 초기화
        self.cap = cv2.VideoCapture(1)
        self.cap.set(3, 640)
        self.cap.set(4, 480)
        
        # === 등록 속도 조절을 위한 변수 ===
        self.last_capture_time = 0  # 마지막으로 사진 찍은 시간

        self.mode = "REGISTER"

        # === [핵심] ID 관리 변수 ===
        self.global_id_counter = 1  # 새로운 사람이 등록될 때마다 부여할 번호표 (1, 2, 3...)
        
        # 현재 추적 중인 대상의 정보
        # 단일 임베딩 대신 '특징 은행(Gallery)' 사용
        self.owner_gallery = [] 
        self.owner_face_emb = None   # 얼굴(Face) 특징 (가장 잘 나온 1장)
        self.owner_global_id = None
        self.current_yolo_id = -1
        
        self.temp_body_embs = []     # 등록용 임시 저장소
        self.temp_face_embs = []     # 등록용 임시 저장소
        self.scale_factor = 1.0

    def get_body_embedding(self, frame, box):
        """ 몸통 특징 추출 (ReID) """
        x1, y1, x2, y2 = map(int, box)
        h, w, _ = frame.shape

        # 너무 작은 객체(먼 거리)는 ReID 시도조차 하지 않음 (노이즈 방지)
        if (y2 - y1) < MIN_HEIGHT_PIXELS:
            return None
        
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        crop = frame[y1:y2, x1:x2]
        if crop.size == 0: return None
        # TorchReID는 텐서를 반환하므로 numpy로 변환
        return self.reid(crop).cpu().detach().numpy()

    def get_face_embedding(self, frame, box):
        """ 얼굴 특징 추출 (InsightFace) """
        x1, y1, x2, y2 = map(int, box)
        h, w, _ = frame.shape
        
        # 사람 영역을 조금 여유 있게 자름 (얼굴이 잘리지 않도록)
        pad_x = int((x2-x1)*0.1)
        pad_y = int((y2-y1)*0.1)
        x1 = max(0, x1 - pad_x)
        y1 = max(0, y1 - pad_y)
        x2 = min(w, x2 + pad_x)
        y2 = min(h, y2 + pad_y)
        
        person_img = frame[y1:y2, x1:x2]
        if person_img.size == 0: return None

        # 얼굴 분석
        faces = self.face_app.get(person_img)
        
        if len(faces) > 0:
            # 가장 큰 얼굴을 주인 얼굴로 간주
            faces.sort(key=lambda x: (x.bbox[2]-x.bbox[0]) * (x.bbox[3]-x.bbox[1]), reverse=True)
            return faces[0].embedding # 얼굴 특징 벡터 (512차원)
        return None

    def get_fake_lidar_dist(self, visual_depth_raw):
        estimated_dist = self.scale_factor / (visual_depth_raw + 1e-6)
        return estimated_dist + random.uniform(-0.1, 0.1) 

    def run(self):
        print(">>> Start Loop (Press 'q' to quit, 'r' to register new person)")
        while True:
            ret, frame = self.cap.read()
            if not ret: break
            h, w, _ = frame.shape
            
            # 1. YOLO 추적 (persist=True로 ID 유지 시도)
            results = self.yolo.track(frame, persist=True, classes=0, verbose=False)
            boxes = results[0].boxes
            
            target_box = None
            
            # ============================================
            # [모드 1] REGISTER: 새로운 주인 등록
            # ============================================
            if self.mode == "REGISTER":
                cv2.putText(frame, "Looking for Owner...", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                
                if boxes:
                    # 화면 중앙에 제일 가깝거나 가장 큰 사람 찾기
                    areas = [((b.xyxy[0][2]-b.xyxy[0][0])*(b.xyxy[0][3]-b.xyxy[0][1])).cpu().item() for b in boxes]
                    target_idx = np.argmax(areas)
                    reg_box = boxes[target_idx]
                    
                    # 1) Body Embedding 수집
                    body_emb = self.get_body_embedding(frame, reg_box.xyxy[0].tolist())
                    
                    # 2) Face Embedding 수집
                    face_emb = self.get_face_embedding(frame, reg_box.xyxy[0].tolist())
                    
                    if body_emb is not None:
                        self.temp_body_embs.append(body_emb)
                        # 얼굴은 발견될 때만 추가
                        if face_emb is not None:
                            self.temp_face_embs.append(face_emb)
                        
                        # 시각화 (초록 박스)
                        x1,y1,x2,y2 = map(int, reg_box.xyxy[0])
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 3)

                    # 진행률 표시
                    cnt = len(self.temp_body_embs)
                    cv2.putText(frame, f"Collecting: {cnt}/30", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)
                    
                    if cnt >= 30:
                        # 등록 완료 처리
                        # 몸: 여러 장의 평균 사용 or 갤러리 방식
                        self.owner_gallery = [e / np.linalg.norm(e) for e in self.temp_body_embs]
                        
                        # 얼굴: 수집된 것 중 평균 사용
                        if len(self.temp_face_embs) > 0:
                            avg_face = np.mean(self.temp_face_embs, axis=0)
                            self.owner_face_emb = avg_face / np.linalg.norm(avg_face)
                            print(f">>> Face Registered! (Samples: {len(self.temp_face_embs)})")
                        else:
                            print(">>> Warning: No face detected during registration.")
                            self.owner_face_emb = None
                            
                        self.owner_global_id = self.global_id_counter
                        self.global_id_counter += 1
                        self.mode = "TRACK"
                        self.temp_body_embs = []
                        self.temp_face_embs = []
                        print(">>> Registration Complete. Mode switched to TRACK.")
            # ============================================
            # [모드 2] TRACK
            # ============================================
            elif self.mode == "TRACK":
                found = False
                
                # --- (1) 기존 ID로 추적 시도 ---
                if self.current_yolo_id != -1:
                    for box in boxes:
                        if box.id is not None and int(box.id) == self.current_yolo_id:
                            target_box = box.xyxy[0].tolist()
                            found = True
                            
                            # 추적 중일 때도 점수(확신도)를 계산해서 보여줌
                            # (디버깅용: 잘 따라가고 있는지 확인)
                            # [디버깅] 현재 주인의 오차 거리 확인
                            emb = self.get_embedding(frame, target_box)
                            if emb is not None:
                                emb /= np.linalg.norm(emb)
                                # 유클리드 거리 계산 (가장 가까운 거리 찾기)
                                dists = [np.linalg.norm(g_emb - emb) for g_emb in self.owner_gallery]
                                min_dist = min(dists) if dists else 100.0
                                
                                x1, y1, x2, y2 = map(int, target_box)
                                # 거리가 작을수록 좋음 (초록색)
                                color = (0, 255, 0) if min_dist < DIST_THRESHOLD else (0, 0, 255)
                                cv2.putText(frame, f"Err: {min_dist:.2f}", (x1, y1 - 25), 
                                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                            break
                
                # --- (2) ID를 놓쳤다면? 전체 스캔 (ReID) ---
                if not found:
                    best_dist = 100.0  # 거리는 작을수록 좋으므로 큰 값으로 초기화
                    best_box = None
                    
                    for box in boxes:
                        if box.id is None: continue
                        
                        # 거리 필터링
                        bh = box.xyxy[0][3] - box.xyxy[0][1]
                        if bh < MIN_HEIGHT_PIXELS: continue

                        # 임베딩 추출
                        emb = self.get_embedding(frame, box.xyxy[0].tolist())
                        if emb is None: continue
                        emb /= np.linalg.norm(emb)
                        
                        # [핵심] 갤러리와의 유클리드 거리(L2 Norm) 계산
                        # dist = sqrt( (x1-x2)^2 + ... )
                        dists = [np.linalg.norm(g_emb - emb) for g_emb in self.owner_gallery]
                        min_dist = min(dists) if dists else 100.0

                        # Gallery 매칭
                        sims = [np.dot(g_emb, emb.T).item() for g_emb in self.owner_gallery]
                        max_sim = max(sims) if sims else 0
                        
                        # [시각화] 탐색 중인 모든 사람 점수 표시
                        bx1, by1, _, _ = map(int, box.xyxy[0])
                        
                        # 점수가 높으면 초록색, 낮으면 하얀색
                        # 오차가 임계값보다 작으면 초록색(주인), 크면 하얀색(타인)
                        if min_dist < DIST_THRESHOLD:
                            color = (0, 255, 0) # Green
                        else:
                            color = (255, 255, 255) # White
                        cv2.putText(frame, f"Err: {min_dist:.2f}", (bx1, by1 - 25), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

                        # 가장 오차가 작은(비슷한) 사람 찾기
                        if min_dist < DIST_THRESHOLD and min_dist < best_dist:
                            best_dist = min_dist
                            best_box = box
                    
                    # 주인을 다시 찾았다면
                    if best_box:
                        target_box = best_box.xyxy[0].tolist()
                        new_id = int(best_box.id)
                        if self.current_yolo_id != new_id:
                            print(f">>> Found Owner! Error Dist: {best_dist:.2f}")
                            self.current_yolo_id = new_id
                        cv2.putText(frame, "Re-ID MATCH!", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255), 2)
            # ============================================
            # [공통] 정보 표시 (ID, 거리, 각도)
            # ============================================
            if target_box:
                x1, y1, x2, y2 = map(int, target_box)
                cx = (x1 + x2) / 2
                
                # Depth
                visual_depth = 10.0
                if self.depth_model:
                    try:
                        d_map = self.depth_model.infer_image(frame)
                        roi = d_map[y1:y2, x1:x2]
                        visual_depth = np.mean(roi) if roi.size > 0 else 0
                    except: pass
                
                # 거리/각도 계산
                lidar_dist = self.get_fake_lidar_dist(visual_depth)
                angle = ((cx / w) - 0.5) * 60.0
                
                # 기본은 빨강 (의심스러움 or 놓침)
                box_color = (0, 0, 255) 
                
                # ReID 오차 계산 (현재 프레임 기준 다시 계산)
                current_emb = self.get_embedding(frame, [x1, y1, x2, y2])
                if current_emb is not None:
                    current_emb /= np.linalg.norm(current_emb)
                    dists = [np.linalg.norm(g_emb - current_emb) for g_emb in self.owner_gallery]
                    current_dist = min(dists) if dists else 1.0
                    
                    # 오차가 기준치(0.4)보다 작으면 초록색 (확실한 주인)
                    if current_dist < DIST_THRESHOLD:
                        box_color = (0, 255, 0)
                # === [최종 라벨링] ===
                # YOLO ID가 몇 번이든 상관없이, 우리는 owner_global_id를 표시합니다.
                label = f"[User {self.owner_global_id}] {lidar_dist:.2f}m / {angle:.1f}deg"
                
                # 수정된 색상(box_color) 적용
                cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, 2)
                # 텍스트 배경 등도 색상 맞춤
                cv2.putText(frame, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, box_color, 2)

            cv2.imshow("Laptop Fusion", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'): break
            if key == ord('r'):
                # 리셋 시: 카운터(global_id_counter)는 초기화 안 함! 
                # 그래야 다음 사람은 User 2, User 3... 이 됨
                self.mode = "REGISTER"
                self.temp_embeddings = []
                self.current_yolo_id = -1
                self.owner_embedding = None
                print(">>> Ready to register NEW person.")

        self.cap.release()
        cv2.destroyAllWindows()

if __name__ == '__main__':
    test = LaptopFusionTest()
    test.run()