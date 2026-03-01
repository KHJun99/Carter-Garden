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
STRICT_DIST_THRESHOLD = 0.5    # 처음 찾을 때 (엄격)
LOOSE_DIST_THRESHOLD = 0.70    # 트래킹 중일 때 (널널)
FACE_SIM_THRESHOLD = 0.4       
MIN_HEIGHT_PIXELS = 100        
SKIP_FRAMES = 3                

# 2. 갤러리 및 데이터 다양성 설정 (핵심 변경)
MAX_GALLERY_SIZE = 100         
GALLERY_UPDATE_INTERVAL = 1.0  

# [NEW] 데이터 편향 방지 임계값
# 등록 시: 이전 프레임과 유사도가 이 값보다 '낮아야' (달라야) 캡처함.
# 값이 낮을수록 더 많이 움직여야 찍힘 (0.90 ~ 0.98 권장)
REGISTRATION_SIM_THRESHOLD = 0.94

# 동적 업데이트 시: 갤러리 내 기존 데이터와 유사도가 이 값보다 '낮아야' 추가함.
# 너무 똑같은 사진이 갤러리에 쌓이는 것을 방지 (0.95 ~ 0.99 권장)
DYNAMIC_ADD_THRESHOLD = 0.94

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
        
        # 트래킹 변수
        self.confirmed_yolo_id = -1
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

    # [New] 중복 제거가 적용된 갤러리 업데이트
    def update_gallery(self, body_emb):
        """ 
        확실한 주인의 특징을 갤러리에 추가하되, 
        기존에 있는 데이터와 너무 똑같으면(중복) 추가하지 않음.
        """
        current_time = time.time()
        if current_time - self.last_gallery_update_time < GALLERY_UPDATE_INTERVAL:
            return

        # 정규화
        norm_emb = body_emb / np.linalg.norm(body_emb)

        # [핵심] 기존 갤러리와 유사도 검사 (중복 방지)
        if len(self.owner_gallery) > 0:
            # 코사인 유사도 계산 (Dot Product)
            sims = [np.dot(g, norm_emb.T).item() for g in self.owner_gallery]
            max_sim = max(sims)
            
        
            # 가장 비슷한게 97% 이상 일치하면 "이미 아는 모습"이므로 추가 안 함
            if max_sim > DYNAMIC_ADD_THRESHOLD:
                # print(f"[Skip] Too similar ({max_sim:.3f})") # 디버깅용
                return 

        # 갤러리 용량 관리 (FIFO)
        if len(self.owner_gallery) >= MAX_GALLERY_SIZE:
            self.owner_gallery.pop(0) 
        
        self.owner_gallery.append(norm_emb)
        self.last_gallery_update_time = current_time
        print(f">>> Gallery Updated! (New view added). Size: {len(self.owner_gallery)}")

    def run(self):
        print(">>> Start Loop (Press 'q': Quit, 'r': Register)")
        while True:
            ret, frame = self.cap.read()
            if not ret: break
            h, w, _ = frame.shape
            self.frame_count += 1
            
            results = self.yolo.track(frame, persist=True, classes=0, verbose=False, imgsz=320)
            boxes = results[0].boxes
            
            target_box = None
            
            # ============================================
            # [모드 1] REGISTER: 강제 회전 유도 & 중복 방지
            # ============================================
            if self.mode == "REGISTER":
                cv2.putText(frame, f"REGISTER ID: {self.global_id_counter}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                if boxes:
                    areas = [((b.xyxy[0][2]-b.xyxy[0][0])*(b.xyxy[0][3]-b.xyxy[0][1])).cpu().item() for b in boxes]
                    target_idx = np.argmax(areas)
                    reg_box = boxes[target_idx]
                    
                    current_time = time.time()
                    captured_this_frame = False
                    warning_msg = None
                    
                    # 0.1초마다 시도
                    if current_time - self.last_capture_time > 0.1:
                        xyxy = reg_box.xyxy[0].tolist()
                        body_emb = self.get_body_embedding(frame, xyxy)
                        face_emb = self.get_face_embedding(frame, xyxy)
                        
                        if body_emb is not None:
                            # [핵심] 유사도 검사: 이전 수집된 데이터와 비교
                            is_diverse = True
                            if len(self.temp_body_embs) > 0:
                                last_emb = self.temp_body_embs[-1] # 마지막으로 찍힌 것
                                # 정규화 후 비교
                                curr_norm = body_emb / np.linalg.norm(body_emb)
                                last_norm = last_emb / np.linalg.norm(last_emb)
                                sim = np.dot(curr_norm, last_norm.T).item()
                                
                                # 너무 똑같으면(예: 0.95 이상) 저장 안 함
                                if sim > REGISTRATION_SIM_THRESHOLD:
                                    is_diverse = False
                            
                            if is_diverse:
                                self.temp_body_embs.append(body_emb)
                                if face_emb is not None:
                                    self.temp_face_embs.append(face_emb)
                                self.last_capture_time = current_time
                                captured_this_frame = True
                            else:
                                # 유사해서 스킵된 경우 -> 사용자에게 움직이라고 경고
                                warning_msg = "TURN AROUND! (Too similar)"

                    # 시각화
                    x1, y1, x2, y2 = map(int, reg_box.xyxy[0])
                    
                    if captured_this_frame:
                        # 캡처 성공: 초록색 깜빡임
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 5)
                    elif warning_msg:
                        # 캡처 실패(유사함): 노란색 경고
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 255), 2)
                        cv2.putText(frame, warning_msg, (x1, y1-20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                    else:
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 1)

                    # Progress Bar
                    cnt = len(self.temp_body_embs)
                    target_cnt = 40 # 360도 다양하게 40장이면 충분함
                    
                    # 진행률 텍스트
                    cv2.putText(frame, f"Collected: {cnt}/{target_cnt}", (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    
                    # 팁 문구
                    if cnt < 10:
                        msg = "Step 1: Front View"
                    elif cnt < 20:
                        msg = "Step 2: Turn Left..."
                    elif cnt < 30:
                        msg = "Step 3: Back View..."
                    else:
                        msg = "Step 4: Turn Right..."
                    cv2.putText(frame, msg, (20, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2)

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
                        print(f">>> Registered! Gallery Size: {len(self.owner_gallery)} (Diverse)")

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
                        
                        # [판단 로직]
                        if has_face and face_score > FACE_SIM_THRESHOLD:
                            is_match = True
                            self.confirmed_yolo_id = obj_id
                            # [중복제거 업데이트] 얼굴이 확실하면 갤러리에 추가 시도
                            if raw_body_emb is not None:
                                self.update_gallery(raw_body_emb) 

                        else:
                            if is_confirmed_id:
                                if min_dist < LOOSE_DIST_THRESHOLD:
                                    is_match = True
                                    # [중복제거 업데이트] ReID가 매우 확실하면(0.5 미만) 추가 시도
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
                    
                    # 시각화
                    label_text = f"Err:{min_dist:.2f}"
                    if face_score > 0: label_text += f"|Face:{face_score:.2f}"
                    
                    if is_match:
                        color = (0, 255, 0)
                        if is_confirmed_id: label_text += " [LOCKED]"
                        cv2.rectangle(frame, (bx1, by1), (bx2, by2), color, 2)
                        cv2.putText(frame, label_text, (bx1, by1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
                        target_box = xyxy
                    else:
                        cv2.putText(frame, label_text, (bx1, by1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

            # [공통] 주인 타겟 정보
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

            cv2.imshow("Smart Data Fusion", frame)
            
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