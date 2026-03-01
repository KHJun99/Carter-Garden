import cv2
import torch
import numpy as np
from ultralytics import YOLO
from torchreid.utils import FeatureExtractor
import time
from insightface.app import FaceAnalysis

# =========================================================
# [설정 및 하이퍼파라미터]
# =========================================================
YOLO_MODEL = 'yolo11n.pt'
REID_MODEL = 'osnet_x0_25' 

# 1. 판별 기준값
# [Strict] 처음 주인을 찾을 때의 엄격한 기준
STRICT_DIST_THRESHOLD = 0.5    
FACE_SIM_THRESHOLD = 0.4       

# [Loose] 이미 주인으로 확인된 ID를 놓치지 않기 위한 널널한 기준
# (등을 돌려서 옷 특징이 좀 달라져도 주인으로 인정)
LOOSE_DIST_THRESHOLD = 0.70    

MIN_HEIGHT_PIXELS = 100        
SKIP_FRAMES = 3                

# [New] 동적 갤러리 설정
MAX_GALLERY_SIZE = 100         # 갤러리가 무한정 커지지 않게 제한
GALLERY_UPDATE_INTERVAL = 1.0  # 1초에 한 번만 갤러리 업데이트 (연산 부하 방지)

class LaptopFusionSmart:
    def __init__(self):
        # 1. 디바이스 설정
        self.device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")
        print(f">>> Device: {self.device}")
        
        # 2. 모델 로드
        print(">>> Loading YOLO...")
        self.yolo = YOLO(YOLO_MODEL)
        
        print(f">>> Loading ReID ({REID_MODEL})...")
        self.reid = FeatureExtractor(
            model_name=REID_MODEL, 
            device=self.device.type, 
            image_size=(256, 128)
        )

        print(">>> Loading InsightFace...")
        self.face_app = FaceAnalysis(providers=['CUDAExecutionProvider'] if torch.cuda.is_available() else ['CPUExecutionProvider'])
        self.face_app.prepare(ctx_id=0, det_size=(320, 320))
        
        # 3. 카메라 설정
        self.cap = cv2.VideoCapture(0)
        self.cap.set(3, 640)
        self.cap.set(4, 480)
        
        self.mode = "REGISTER"
        self.last_capture_time = 0
        self.global_id_counter = 1
        
        # === 데이터 저장소 ===
        self.owner_gallery = []      
        self.owner_face_emb = None   
        self.owner_global_id = None
        
        # [New] 트래킹 신뢰 변수
        self.confirmed_yolo_id = -1  # 현재 주인이라고 확신하는 YOLO ID
        self.last_gallery_update_time = 0
        
        self.temp_body_embs = []     
        self.temp_face_embs = []     

        self.frame_count = 0
        self.cached_results = {}     

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
        faces = self.face_app.get(person_img)
        if len(faces) > 0:
            faces.sort(key=lambda x: (x.bbox[2]-x.bbox[0]) * (x.bbox[3]-x.bbox[1]), reverse=True)
            return faces[0].embedding 
        return None

    # [New] 동적 갤러리 업데이트 함수
    def update_gallery(self, body_emb):
        """ 확실한 주인의 특징을 갤러리에 추가하여 '기억'을 강화함 """
        current_time = time.time()
        # 너무 자주 업데이트하면 느려지므로 1초 간격 제한
        if current_time - self.last_gallery_update_time < GALLERY_UPDATE_INTERVAL:
            return

        # 갤러리 용량 관리 (FIFO: 오래된 것 삭제)
        if len(self.owner_gallery) >= MAX_GALLERY_SIZE:
            self.owner_gallery.pop(0) 
        
        # 정규화 후 추가
        norm_emb = body_emb / np.linalg.norm(body_emb)
        self.owner_gallery.append(norm_emb)
        self.last_gallery_update_time = current_time
        # print(f">>> Gallery Updated! Size: {len(self.owner_gallery)}") # 디버깅용

    def run(self):
        print(">>> Start Loop (Press 'q': Quit, 'r': Register)")
        while True:
            ret, frame = self.cap.read()
            if not ret: break
            h, w, _ = frame.shape
            self.frame_count += 1
            
            # YOLO 추적 (persist=True가 ID 유지의 핵심)
            results = self.yolo.track(frame, persist=True, classes=0, verbose=False, imgsz=320)
            boxes = results[0].boxes
            
            target_box = None
            
            # ============================================
            # [모드 1] REGISTER: 360도 회전 유도
            # ============================================
            if self.mode == "REGISTER":
                cv2.putText(frame, f"REGISTER ID: {self.global_id_counter}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                # [안내 변경]
                cv2.putText(frame, "Please rotate 360 degrees slowly!", (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                
                if boxes:
                    areas = [((b.xyxy[0][2]-b.xyxy[0][0])*(b.xyxy[0][3]-b.xyxy[0][1])).cpu().item() for b in boxes]
                    target_idx = np.argmax(areas)
                    reg_box = boxes[target_idx]
                    
                    current_time = time.time()
                    captured_this_frame = False
                    
                    if current_time - self.last_capture_time > 0.1:
                        xyxy = reg_box.xyxy[0].tolist()
                        body_emb = self.get_body_embedding(frame, xyxy)
                        face_emb = self.get_face_embedding(frame, xyxy)
                        
                        if body_emb is not None:
                            self.temp_body_embs.append(body_emb)
                            if face_emb is not None:
                                self.temp_face_embs.append(face_emb)
                            self.last_capture_time = current_time
                            captured_this_frame = True
                    
                    # 시각화
                    x1, y1, x2, y2 = map(int, reg_box.xyxy[0])
                    color = (0, 255, 0) if captured_this_frame else (200, 255, 200)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                    
                    # Progress Bar
                    cnt = len(self.temp_body_embs)
                    # 360도 도는 시간을 고려해 50장 정도로 늘림
                    target_cnt = 50 
                    
                    cv2.putText(frame, f"{cnt}/{target_cnt}", (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

                    if cnt >= target_cnt:
                        self.owner_gallery = [e / np.linalg.norm(e) for e in self.temp_body_embs]
                        if len(self.temp_face_embs) > 0:
                            avg_face = np.mean(self.temp_face_embs, axis=0)
                            self.owner_face_emb = avg_face / np.linalg.norm(avg_face)
                        else:
                            self.owner_face_emb = None
                            
                        self.owner_global_id = self.global_id_counter
                        self.global_id_counter += 1
                        self.confirmed_yolo_id = -1 # 초기화
                        
                        self.mode = "TRACK"
                        self.temp_body_embs = []
                        self.temp_face_embs = []
                        print(f">>> Registered! Gallery Size: {len(self.owner_gallery)}")

            # ============================================
            # [모드 2] TRACK: 스마트 추적 (Trust YOLO + Dynamic Gallery)
            # ============================================
            elif self.mode == "TRACK":
                run_heavy_tasks = (self.frame_count % SKIP_FRAMES == 0)
                
                # 현재 프레임에 주인이 있는지 확인하기 위한 플래그
                owner_found_in_frame = False

                for box in boxes:
                    if box.id is None: continue
                    obj_id = int(box.id)
                    xyxy = box.xyxy[0].tolist()
                    bx1, by1, bx2, by2 = map(int, xyxy)
                    
                    if obj_id not in self.cached_results:
                        self.cached_results[obj_id] = (1.0, 0.0, False)
                    
                    min_dist, face_score, is_match = self.cached_results[obj_id]
                    
                    # [3. Trust YOLO] 이 ID가 이전에 주인으로 확정된 ID인가?
                    is_confirmed_id = (obj_id == self.confirmed_yolo_id)
                    
                    if run_heavy_tasks or min_dist == 1.0:
                        # 1. Feature Extraction
                        curr_body = self.get_body_embedding(frame, xyxy)
                        
                        # ReID Distance Check
                        if curr_body is not None:
                            # 갤러리 업데이트용 원본(정규화 전) 저장
                            raw_body_emb = curr_body.copy() 
                            
                            curr_body /= np.linalg.norm(curr_body)
                            dists = [np.linalg.norm(g - curr_body) for g in self.owner_gallery]
                            min_dist = min(dists) if dists else 1.0
                        else:
                            raw_body_emb = None

                        # Face Check
                        face_score = 0.0
                        has_face = False
                        if self.owner_face_emb is not None:
                            curr_face = self.get_face_embedding(frame, xyxy)
                            if curr_face is not None:
                                curr_face /= np.linalg.norm(curr_face)
                                face_score = np.dot(self.owner_face_emb, curr_face)
                                has_face = True
                        
                        # === [핵심] 판단 로직 개선 ===
                        is_match = False
                        
                        # Case A: 얼굴이 확인됨 -> 무조건 주인 & ID 잠금 & 갤러리 업데이트
                        if has_face and face_score > FACE_SIM_THRESHOLD:
                            is_match = True
                            self.confirmed_yolo_id = obj_id # ID 확정 (Lock)
                            if raw_body_emb is not None:
                                self.update_gallery(raw_body_emb) # [2. Dynamic Gallery]

                        # Case B: 얼굴 안 보임 -> ReID + Tracking ID로 판단
                        else:
                            # 3-1. 이미 주인으로 확정된 ID라면? (Loose 기준 적용)
                            if is_confirmed_id:
                                # ReID 오차가 '조금' 커도(0.6~0.7) 주인으로 인정 (등 돌림 등)
                                if min_dist < LOOSE_DIST_THRESHOLD:
                                    is_match = True
                                    # 이 상태에서도 오차가 꽤 작으면(0.4) 갤러리 업데이트 (뒷모습 학습)
                                    if min_dist < STRICT_DIST_THRESHOLD and raw_body_emb is not None:
                                        self.update_gallery(raw_body_emb)
                                else:
                                    # 오차가 너무 크면(완전 다른 사람) 추적 포기
                                    is_match = False
                                    self.confirmed_yolo_id = -1 
                                    
                            # 3-2. 새로운 사람이면? (Strict 기준 적용)
                            else:
                                if min_dist < STRICT_DIST_THRESHOLD:
                                    is_match = True
                                    self.confirmed_yolo_id = obj_id # ID 확정

                        self.cached_results[obj_id] = (min_dist, face_score, is_match)
                    
                    # === 시각화 ===
                    label_text = f"Err:{min_dist:.2f}"
                    if face_score > 0: label_text += f"|Face:{face_score:.2f}"
                    
                    if is_match:
                        owner_found_in_frame = True
                        color = (0, 255, 0) # Green
                        # 주인 표시 강화 (ID 유지 중임을 표시)
                        if is_confirmed_id: 
                            label_text += " [LOCKED]"
                        
                        cv2.rectangle(frame, (bx1, by1), (bx2, by2), color, 2)
                        cv2.putText(frame, label_text, (bx1, by1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
                        target_box = xyxy
                    else:
                        cv2.putText(frame, label_text, (bx1, by1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

                # 만약 화면에 확정된 ID가 사라졌다면? (화면 밖으로 나감)
                # (YOLO ID가 끊기면 confirmed_yolo_id는 다음 detection 때 초기화되거나 strict 모드로 다시 찾음)

            # [공통] 주인 정보 표시
            if target_box:
                x1, y1, x2, y2 = map(int, target_box)
                est_dist = self.get_simple_dist(target_box)
                cx = (x1 + x2) / 2
                angle = ((cx / w) - 0.5) * 60.0
                
                label = f"[User {self.owner_global_id}] {est_dist:.1f}m / {angle:.1f}deg"
                
                text_y = y1 - 25
                (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                cv2.rectangle(frame, (x1, text_y - th - 5), (x1 + tw, text_y + 5), (0, 255, 0), -1)
                cv2.putText(frame, label, (x1, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)

            cv2.imshow("Jetson Smart Tracker", frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'): break
            if key == ord('r'):
                self.mode = "REGISTER"
                self.temp_body_embs = []
                self.temp_face_embs = []
                self.owner_gallery = []
                self.owner_face_emb = None
                self.cached_results = {}
                self.confirmed_yolo_id = -1
                print(">>> Reset.")

        self.cap.release()
        cv2.destroyAllWindows()

if __name__ == '__main__':
    test = LaptopFusionSmart()
    test.run()