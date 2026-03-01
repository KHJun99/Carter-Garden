import cv2
import torch
import numpy as np
from ultralytics import YOLO
from torchreid.utils import FeatureExtractor
import time
# InsightFace (얼굴 인식)
from insightface.app import FaceAnalysis

# =========================================================
# [설정 및 하이퍼파라미터]
# =========================================================
# 1. 모델 설정 (Jetson 최적화)
YOLO_MODEL = 'yolo26n.pt'      # 가장 가벼운 YOLO 모델
REID_MODEL = 'osnet_x0_25'     # [핵심] ResNet50 대신 매우 가벼운 OSNet 사용
# DEPTH 모델은 너무 무거워서 제거하고, 박스 크기로 거리를 추정합니다.

# 2. 판별 기준값 (Threshold)
# ReID 모델이 바뀌었으므로(osnet), 거리 기준을 조금 넉넉하게 잡습니다.
DIST_THRESHOLD = 0.5           # 이 값보다 '작아야' 옷/체형이 같다고 판단
FACE_SIM_THRESHOLD = 0.4       # 이 값보다 '커야' 얼굴이 같다고 판단
MIN_HEIGHT_PIXELS = 100        # 너무 작은(멀리 있는) 사람은 무시

# 3. 최적화 설정
SKIP_FRAMES = 3                # 3프레임마다 한 번씩만 무거운 인식(ReID/Face) 수행

class LaptopFusionOptimized:
    def __init__(self):
        # 1. 디바이스 설정 (CUDA 권장)
        self.device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")
        print(f">>> Device: {self.device}")
        
        # 2. 모델 로드
        print(">>> Loading YOLO...")
        self.yolo = YOLO(YOLO_MODEL)
        
        print(f">>> Loading ReID ({REID_MODEL})...")
        self.reid = FeatureExtractor(
            model_name=REID_MODEL, 
            device=self.device.type, 
            image_size=(256, 128) # [최적화] 입력 이미지 크기를 줄여 속도 향상
        )

        print(">>> Loading InsightFace (Face)...")
        # [최적화] det_size를 (320, 320)으로 줄여 얼굴 탐지 속도 향상
        self.face_app = FaceAnalysis(providers=['CUDAExecutionProvider'] if torch.cuda.is_available() else ['CPUExecutionProvider'])
        self.face_app.prepare(ctx_id=0, det_size=(320, 320))
        
        # 3. 카메라 설정
        self.cap = cv2.VideoCapture(0)
        # Jetson에서는 해상도가 성능에 큰 영향을 줍니다. (640x480 권장)
        self.cap.set(3, 640)
        self.cap.set(4, 480)
        
        # 4. 상태 변수 초기화
        self.mode = "REGISTER"
        self.last_capture_time = 0
        self.global_id_counter = 1
        
        # 데이터 저장소
        self.owner_gallery = []      # 주인의 몸 특징들
        self.owner_face_emb = None   # 주인의 얼굴 특징
        self.owner_global_id = None
        
        # 등록 임시 저장소
        self.temp_body_embs = []     
        self.temp_face_embs = []     

        # [최적화] 프레임 스킵을 위한 캐시 변수
        self.frame_count = 0
        self.cached_results = {}     # {detect_id: (min_dist, face_score, is_match)}

    def get_simple_dist(self, box):
        """ 
        [최적화] 무거운 Deep Learning Depth 모델 대신, 
        박스의 높이(픽셀)를 이용해 거리를 대략적으로 추정합니다.
        """
        _, y1, _, y2 = map(int, box)
        h = y2 - y1
        if h < 1: return 0.0
        # 공식: 거리 = (초점거리 * 실제사람키) / 픽셀높이
        # 대략적인 상수(500)를 사용했습니다. 필요 시 보정하세요.
        return 500.0 / h 

    def get_body_embedding(self, frame, box):
        """ 몸통 특징 추출 (ReID) """
        x1, y1, x2, y2 = map(int, box)
        h, w, _ = frame.shape
        
        if (y2 - y1) < MIN_HEIGHT_PIXELS: return None
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        
        crop = frame[y1:y2, x1:x2]
        if crop.size == 0: return None
        
        # 이미지를 ReID 모델에 넣어 특징 벡터 추출
        return self.reid(crop).cpu().detach().numpy()

    def get_face_embedding(self, frame, box):
        """ 얼굴 특징 추출 (InsightFace) """
        x1, y1, x2, y2 = map(int, box)
        h, w, _ = frame.shape
        
        # 얼굴이 잘리지 않게 박스를 조금 여유 있게(padding) 자름
        pad_x = int((x2-x1)*0.1)
        pad_y = int((y2-y1)*0.1)
        x1 = max(0, x1 - pad_x)
        y1 = max(0, y1 - pad_y)
        x2 = min(w, x2 + pad_x)
        y2 = min(h, y2 + pad_y)
        
        person_img = frame[y1:y2, x1:x2]
        if person_img.size == 0: return None
        
        faces = self.face_app.get(person_img)
        if len(faces) > 0:
            # 가장 큰 얼굴을 선택
            faces.sort(key=lambda x: (x.bbox[2]-x.bbox[0]) * (x.bbox[3]-x.bbox[1]), reverse=True)
            return faces[0].embedding 
        return None

    def run(self):
        print(">>> Start Loop (Press 'q': Quit, 'r': Register)")
        while True:
            ret, frame = self.cap.read()
            if not ret: break
            h, w, _ = frame.shape
            self.frame_count += 1
            
            # 1. YOLO 추적 (가벼운 모델이라 매 프레임 실행)
            # imgsz=320으로 낮춰서 속도 확보
            results = self.yolo.track(frame, persist=True, classes=0, verbose=False, imgsz=320)
            boxes = results[0].boxes
            
            target_box = None # 주인을 찾았을 때 박스 좌표 저장
            
            # ============================================
            # [모드 1] REGISTER: 등록
            # ============================================
            if self.mode == "REGISTER":
                # 안내 문구
                cv2.putText(frame, f"REGISTER ID: {self.global_id_counter}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(frame, "Slowly rotate body...", (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2)
                
                if boxes:
                    # 화면에서 가장 큰 사람 찾기
                    areas = [((b.xyxy[0][2]-b.xyxy[0][0])*(b.xyxy[0][3]-b.xyxy[0][1])).cpu().item() for b in boxes]
                    target_idx = np.argmax(areas)
                    reg_box = boxes[target_idx]
                    
                    current_time = time.time()
                    captured_this_frame = False
                    
                    # 0.1초마다 캡처
                    if current_time - self.last_capture_time > 0.1:
                        xyxy_list = reg_box.xyxy[0].tolist()
                        body_emb = self.get_body_embedding(frame, xyxy_list)
                        face_emb = self.get_face_embedding(frame, xyxy_list)
                        
                        if body_emb is not None:
                            self.temp_body_embs.append(body_emb)
                            # 얼굴은 감지될 때만 추가
                            if face_emb is not None:
                                self.temp_face_embs.append(face_emb)
                            
                            self.last_capture_time = current_time
                            captured_this_frame = True
                    
                    # [시각화] 캡처 시 박스 깜빡임
                    x1, y1, x2, y2 = map(int, reg_box.xyxy[0])
                    if captured_this_frame:
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 5) # 두꺼운 박스
                    else:
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 1) # 얇은 박스

                    # [시각화] 진행률 바 (Progress Bar)
                    target_count = 30
                    current_count = len(self.temp_body_embs)
                    
                    bar_x, bar_y = 20, 100
                    bar_w, bar_h = 200, 20
                    fill_w = int(bar_w * (current_count / target_count))
                    
                    cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (100, 100, 100), -1)
                    cv2.rectangle(frame, (bar_x, bar_y), (bar_x + fill_w, bar_y + bar_h), (0, 255, 0), -1)
                    cv2.putText(frame, f"{current_count}/{target_count}", (bar_x + bar_w + 10, bar_y + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

                    # 완료 조건
                    if current_count >= target_count:
                        # 갤러리 등록
                        self.owner_gallery = [e / np.linalg.norm(e) for e in self.temp_body_embs]
                        if len(self.temp_face_embs) > 0:
                            avg_face = np.mean(self.temp_face_embs, axis=0)
                            self.owner_face_emb = avg_face / np.linalg.norm(avg_face)
                        else:
                            self.owner_face_emb = None
                            
                        self.owner_global_id = self.global_id_counter
                        self.global_id_counter += 1
                        
                        # 모드 변경 및 초기화
                        self.mode = "TRACK"
                        self.temp_body_embs = []
                        self.temp_face_embs = []
                        print(">>> Registered! Switching to TRACK mode.")

            # ============================================
            # [모드 2] TRACK: 추적 (최적화 적용)
            # ============================================
            elif self.mode == "TRACK":
                # [최적화] 3프레임에 한 번만 무거운 인식(ReID/Face) 수행
                run_heavy_tasks = (self.frame_count % SKIP_FRAMES == 0)
                
                for box in boxes:
                    if box.id is None: continue
                    obj_id = int(box.id)
                    xyxy = box.xyxy[0].tolist()
                    bx1, by1, bx2, by2 = map(int, xyxy)
                    
                    # 새로 등장한 ID면 캐시 초기화
                    if obj_id not in self.cached_results:
                        # 초기값 (거리 1.0 = 아주 멂, 얼굴점수 0.0)
                        self.cached_results[obj_id] = (1.0, 0.0, False) 
                    
                    # 캐시된 결과 가져오기
                    min_dist, face_score, is_match = self.cached_results[obj_id]
                    
                    # [연산 수행 조건] 프레임 스킵 타이밍 or 처음 보는 사람(dist=1.0)
                    if run_heavy_tasks or min_dist == 1.0:
                        # 1. Body ReID 거리 계산
                        curr_body = self.get_body_embedding(frame, xyxy)
                        if curr_body is not None:
                            curr_body /= np.linalg.norm(curr_body)
                            dists = [np.linalg.norm(g - curr_body) for g in self.owner_gallery]
                            min_dist = min(dists) if dists else 1.0
                        
                        # 2. Face 유사도 계산
                        face_score = 0.0
                        has_face = False
                        if self.owner_face_emb is not None:
                            curr_face = self.get_face_embedding(frame, xyxy)
                            if curr_face is not None:
                                curr_face /= np.linalg.norm(curr_face)
                                face_score = np.dot(self.owner_face_emb, curr_face)
                                has_face = True
                        
                        # 3. 주인 여부 판단 (Hybrid Logic)
                        is_match = False
                        if has_face:
                            # 얼굴이 보이면 얼굴 점수가 최우선
                            if face_score > FACE_SIM_THRESHOLD: is_match = True
                        else:
                            # 얼굴 안 보이면(뒤돌음) 옷/체형(ReID) 거리로 판단
                            if min_dist < DIST_THRESHOLD: is_match = True
                            
                        # 결과를 캐시에 저장 (다음 프레임들을 위해)
                        self.cached_results[obj_id] = (min_dist, face_score, is_match)
                    
                    # === [시각화: 점수 및 박스 표시] ===
                    # Err: 낮을수록 좋음 (옷 차이), Face: 높을수록 좋음 (얼굴 유사도)
                    score_label = f"Err:{min_dist:.2f}"
                    if face_score > 0: score_label += f" | Face:{face_score:.2f}"

                    if is_match:
                        # [주인] 초록색 박스 그리기
                        cv2.rectangle(frame, (bx1, by1), (bx2, by2), (0, 255, 0), 2)
                        
                        # [주인] 머리 위 1단: 점수 표시 (초록색)
                        cv2.putText(frame, score_label, (bx1, by1 - 10), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                        
                        target_box = xyxy # 최종 타겟으로 설정
                    else:
                        # [타인] 박스 없음 (화면 깔끔하게)
                        
                        # [타인] 머리 위 1단: 점수만 표시 (회색)
                        # 왜 주인이 아닌지 디버깅 가능
                        cv2.putText(frame, score_label, (bx1, by1 - 10), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

            # ============================================
            # [공통] 주인 최종 라벨 (2단 정보: ID, 거리, 각도)
            # ============================================
            if target_box:
                x1, y1, x2, y2 = map(int, target_box)
                cx = (x1 + x2) / 2
                
                # [최적화] Depth 모델 없이 박스 크기로 거리 추정
                est_dist = self.get_simple_dist(target_box)
                angle = ((cx / w) - 0.5) * 60.0
                
                label = f"[User {self.owner_global_id}] {est_dist:.1f}m / {angle:.1f}deg"
                
                # [위치 조정] 1단 점수 텍스트(Err/Face)와 겹치지 않게 더 위로 띄움
                # text_base_y를 y1 - 25로 설정하여 1단 텍스트(y1-10)보다 위에 배치
                text_base_y = y1 - 25
                (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                
                # 라벨 배경 (초록색)
                cv2.rectangle(frame, (x1, text_base_y - th - 5), (x1 + tw, text_base_y + 5), (0, 255, 0), -1)
                # 라벨 텍스트 (검은색)
                cv2.putText(frame, label, (x1, text_base_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)

            # 화면 출력
            cv2.imshow("Jetson Fusion Optimized", frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'): break
            if key == ord('r'):
                # 리셋 (재등록 모드)
                self.mode = "REGISTER"
                self.temp_body_embs = []
                self.temp_face_embs = []
                self.owner_gallery = []
                self.owner_face_emb = None
                self.cached_results = {}
                print(">>> Ready to register NEW person.")

        self.cap.release()
        cv2.destroyAllWindows()

if __name__ == '__main__':
    test = LaptopFusionOptimized()
    test.run()