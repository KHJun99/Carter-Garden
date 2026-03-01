import cv2
import torch
import numpy as np
from ultralytics import YOLO
from torchreid.utils import FeatureExtractor
import time
import random
from insightface.app import FaceAnalysis # InsightFace 추가

# === [설정] ===
YOLO_MODEL = 'yolo26n.pt'     # 혹은 yolo8n.pt
REID_MODEL = 'resnet50_fc512' # 정확도 좋은 ReID 모델

# 거리 임계값 (낮을수록 엄격)
FACE_DIST_THRESHOLD = 1.0  # InsightFace 거리 (L2 Norm 기준, 1.0~1.1 이하가 본인)
BODY_DIST_THRESHOLD = 0.40 # ReID 거리 (0.4 이하가 본인)

MIN_HEIGHT_PIXELS = 100 

class LaptopFusionHybrid:
    def __init__(self):
        self.device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")
        print(f">>> Device: {self.device}")
        
        # 1. YOLO 로드
        print(">>> Loading YOLO...")
        self.yolo = YOLO(YOLO_MODEL)
        
        # 2. ReID (몸) 로드
        print(">>> Loading ReID (Body)...")
        self.reid = FeatureExtractor(
            model_name=REID_MODEL, 
            device=self.device.type, 
            image_size=(384, 192)
        )
        
        # 3. InsightFace (얼굴) 로드 [추가됨]
        print(">>> Loading InsightFace (Face)...")
        # providers=['CUDAExecutionProvider'] 가 가능하면 더 빠름. 안되면 'CPUExecutionProvider'
        self.face_app = FaceAnalysis(providers=['CUDAExecutionProvider']) 
        self.face_app.prepare(ctx_id=0, det_size=(640, 640))
        
        # 카메라 설정
        self.cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
        # 2. [핵심] 해상도를 640x480으로 강제합니다. (속도 향상)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        fourcc = cv2.VideoWriter_fourcc(*'MJPG')
        self.cap.set(cv2.CAP_PROP_FOURCC, fourcc)

        self.cap.set(3, 640)
        self.cap.set(4, 480)
        
        # 데이터 관리
        self.mode = "REGISTER"
        self.owner_face_emb = None   # 주인의 얼굴 데이터 (불변)
        self.owner_body_emb = None   # 주인의 몸 데이터 (가변 - 옷 갈아입으면 바뀜)
        
        self.temp_face_embs = []     # 등록용 임시 저장소

    def get_body_embedding(self, frame, box):
        """ ReID 모델을 사용해 몸 전체 특징 추출 """
        x1, y1, x2, y2 = map(int, box)
        h, w, _ = frame.shape
        crop = frame[max(0,y1):min(h,y2), max(0,x1):min(w,x2)]
        if crop.size == 0: return None
        return self.reid(crop).cpu().detach().numpy()

    def get_face_embedding(self, frame):
        """ InsightFace를 사용해 화면 내 가장 큰 얼굴 특징 추출 """
        faces = self.face_app.get(frame)
        if not faces:
            return None
        # 얼굴이 여러 개일 경우 가장 큰 얼굴 선택
        max_area = 0
        target_face = None
        for face in faces:
            box = face.bbox.astype(int)
            area = (box[2] - box[0]) * (box[3] - box[1])
            if area > max_area:
                max_area = area
                target_face = face
        
        if target_face is not None:
            return target_face.embedding # (512,) 벡터
        return None

    def run(self):
        print(">>> Start Hybrid Loop. (r: Register, q: Quit)")
        while True:
            ret, frame = self.cap.read()
            if not ret: break
            
            # YOLO로 사람 찾기
            results = self.yolo.track(frame, persist=True, classes=0, verbose=False)
            boxes = results[0].boxes
            
            # =========================
            # [모드 1] REGISTER (등록)
            # =========================
            if self.mode == "REGISTER":
                cv2.putText(frame, "Look at the camera!", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
                
                # 얼굴 찾기
                face_emb = self.get_face_embedding(frame)
                
                if face_emb is not None:
                    self.temp_face_embs.append(face_emb)
                    cv2.putText(frame, f"Collecting... {len(self.temp_face_embs)}/10", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                # 10장 모이면 등록 완료
                if len(self.temp_face_embs) >= 10:
                    # 얼굴 평균값 계산 (정규화)
                    avg_emb = np.mean(self.temp_face_embs, axis=0)
                    self.owner_face_emb = avg_emb / np.linalg.norm(avg_emb)
                    
                    print(">>> Face Registered! Now capturing initial body...")
                    
                    # [중요] 등록 순간의 옷차림(Body)도 초기값으로 저장
                    if boxes:
                        # 가장 큰 박스 찾기
                        areas = [((b.xyxy[0][2]-b.xyxy[0][0])*(b.xyxy[0][3]-b.xyxy[0][1])).item() for b in boxes]
                        best_idx = np.argmax(areas)
                        initial_body = self.get_body_embedding(frame, boxes[best_idx].xyxy[0].tolist())
                        
                        if initial_body is not None:
                            self.owner_body_emb = initial_body / np.linalg.norm(initial_body)
                            self.mode = "TRACK"
                            self.temp_face_embs = []
                            print(">>> Registration Complete! Switch to TRACK mode.")

            # =========================
            # [모드 2] TRACK (추적)
            # =========================
            elif self.mode == "TRACK":
                best_box = None
                best_state = "UNKNOWN" # 상태: FACE_MATCH, BODY_MATCH, UNKNOWN
                min_err = 999.0
                
                # 현재 화면의 얼굴 정보 가져오기 (비용이 비싸므로 한 번만 실행)
                # 주의: 사람이 여러 명일 때 매칭 로직이 복잡해질 수 있어 단순화함 (가장 큰 얼굴 기준)
                current_face_emb = self.get_face_embedding(frame)
                
                is_face_match = False
                face_dist = 999.0
                
                # 1. 얼굴 매칭 시도
                if current_face_emb is not None and self.owner_face_emb is not None:
                    # L2 Distance 계산
                    current_face_emb = current_face_emb / np.linalg.norm(current_face_emb)
                    face_dist = np.linalg.norm(self.owner_face_emb - current_face_emb)
                    
                    if face_dist < FACE_DIST_THRESHOLD:
                        is_face_match = True
                
                # 2. 모든 사람 박스 검사
                for box in boxes:
                    xyxy = box.xyxy[0].tolist()
                    
                    # 이 박스가 주인인가? 판단
                    # 시나리오 A: 얼굴이 매칭됨 -> 무조건 이 사람이 주인
                    # (정확히 하려면 얼굴 좌표가 이 몸 박스 안에 있는지 체크해야 하지만, 
                    # 여기서는 1인 추적 가정하에 얼굴 매칭 성공 시 가장 큰 박스를 주인으로 간주하거나 
                    # Face Box 중심이 Body Box 안에 있는지 체크하는 것이 좋습니다.)
                    
                    # 시나리오 B: 얼굴 매칭 실패(뒤돌음) -> ReID(몸)로 확인
                    
                    body_emb = self.get_body_embedding(frame, xyxy)
                    if body_emb is None: continue
                    body_emb = body_emb / np.linalg.norm(body_emb)
                    
                    # 몸 거리 계산
                    body_dist = np.linalg.norm(self.owner_body_emb - body_emb)
                    
                    is_owner = False
                    
                    # [핵심 로직]
                    if is_face_match:
                        # 얼굴이 맞으면 무조건 주인!
                        # 그리고 현재 입은 옷(body_emb)으로 주인의 Body 정보를 업데이트 (Chameleon)
                        self.owner_body_emb = body_emb # 업데이트!
                        best_state = "FACE_VERIFIED"
                        min_err = face_dist
                        is_owner = True
                        
                    elif body_dist < BODY_DIST_THRESHOLD:
                        # 얼굴은 안 보이지만 옷이 똑같음
                        best_state = "BODY_TRACKING"
                        min_err = body_dist
                        is_owner = True
                    
                    if is_owner:
                        x1, y1, x2, y2 = map(int, xyxy)
                        
                        # 색상 결정
                        color = (0, 255, 0) if best_state == "FACE_VERIFIED" else (0, 255, 255) # 초록 or 노랑
                        
                        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                        cv2.putText(frame, f"{best_state} (Err:{min_err:.2f})", (x1, y1-10), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

            cv2.imshow("Hybrid Fusion", frame)
            key = cv2.waitKey(1)
            if key == ord('q'): break
            if key == ord('r'):
                self.mode = "REGISTER"
                self.temp_face_embs = []
                print(">>> Reset Registration")

        self.cap.release()
        cv2.destroyAllWindows()

if __name__ == '__main__':
    fusion = LaptopFusionHybrid()
    fusion.run()