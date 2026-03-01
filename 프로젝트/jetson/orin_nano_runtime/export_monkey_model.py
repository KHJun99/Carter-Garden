from ultralytics import YOLO
import os

# 모델 경로 설정
model_path = '/root/test_d201_ssafy/test_minseo/Jetson_Orin_Nano/models/monkey_model.pt'

print(f"Loading model from {model_path}...")
model = YOLO(model_path)

print("Exporting to TensorRT engine (this may take a few minutes)...")
# arguments: format='engine', half=True (FP16 quantization), device=0 (GPU)
model.export(format='engine', half=True, device=0)

print("Export completed!")
