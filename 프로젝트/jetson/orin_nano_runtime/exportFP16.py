
import os
from ultralytics import YOLO

# =========================================================
# [설정 및 하이퍼파라미터]
# =========================================================
current_dir = os.path.dirname(os.path.abspath(__file__))
YOLO_MODEL = os.path.join(current_dir, 'models', 'yolo11n.pt')
# 모델 로드
model = YOLO(YOLO_MODEL)

# TensorRT 엔진으로 내보내기 (FP16 정밀도 사용)
# use `half=True` (Ultralytics export uses `half` for half-precision)
# Try building TensorRT engine with a limited workspace to reduce memory use
# workspace is bytes (e.g. 1<<28 == 268435456 bytes)
model.export(format='engine', device=0, half=True, workspace=(1<<28))