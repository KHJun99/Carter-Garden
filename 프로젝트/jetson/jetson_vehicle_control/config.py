# config.py - GA25-370 후륜 + 회전캐스터
# 🔴 절대 변경 금지 = 하드웨어 터짐/쇼트 위험
# 🟡 매우 조심 = 과열 위험  
# 🟢 자유 변경 = 성능 튜닝용

# 🔴 I2C 주소 (sudo i2cdetect -y 7로 확인!)
PCA9685_ADDRESS = 0x60           # 서보 PCA (필요시)
MOTOR_HAT_I2C_ADDRESS = 0x40     # Motor HAT 주소

# 🔴 하드웨어 안전 한계
PWM_FREQUENCY = 1000            # Motor HAT 권장 (500~2000Hz)
MOTOR_SAFE_SPEED = 0.6           # GA25-371 최대 2A (0.7↑ 과열⚠️)

# 🟢 튜닝 자유 (테스트하며 변경)
SPEED_NORMAL = 0.3               # 기본 속도
TURN_THRESHOLD = 40              # 회전 민감도 (px)
CONFIDENCE_THRESHOLD = 0.5       # YOLO 인식 민감도

# 🟢 카메라 설정
CAMERA_INDEX = 0                 # USB 카메라 번호
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
FRAME_CENTER_X = FRAME_WIDTH // 2
MODEL_PATH = "custom.pt"         # YOLO 모델 경로

# 🟢 SLAM 설정
OBSTACLE_DISTANCE = 1.0          # 장애물 정지 거리 (m)
LIDAR_MIN_RANGE = 0.1
LIDAR_MAX_RANGE = 10.0
