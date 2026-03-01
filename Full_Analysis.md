# Carter Garden (카터가든) — 스마트 자율주행 쇼핑카트 시스템 전체 분석

## 1. 프로젝트 개요

| 항목 | 내용 |
|------|------|
| **프로젝트명** | Carter Garden (스마트 자율주행 쇼핑카트 PoC) |
| **기간** | 2026.01.12 ~ 2026.02.08 (4주) |
| **팀 구성** | 6명 (IoT/Web 3명, HW/Robotics 3명) |
| **목표** | LiDAR SLAM 기반 자율주행 + RFID 장바구니 + 사람 추종 쇼핑카트 |

---

## 2. 전체 디렉토리 구조

```
프로젝트/
├── jetson/                           # 로봇 두뇌 (Jetson Orin Nano)
│   ├── jetson_vehicle_control/       # 저수준 차량 제어
│   │   ├── config.py                 # 하드웨어 상수
│   │   ├── motor_hat.py              # PCA9685 모터 드라이버
│   │   ├── encoder_count.py          # 인코더 틱 카운터
│   │   ├── 1_keyboard_control.py     # 키보드 수동 조작
│   │   ├── 2_slam_mapping.py         # LiDAR 100스캔 지도 저장
│   │   ├── 3_slam_navigation.py      # LiDAR 장애물 회피 주행
│   │   ├── 4_autonomous_drive.py     # YOLO+LiDAR 자율주행
│   │   ├── 5_odom_publisher.py       # 휠 인코더 오도메트리
│   │   ├── 6_imu_publisher.py        # MPU6050 IMU 발행
│   │   ├── 7_straight_drive_fusion.py # PID 직진 보정 컨트롤러
│   │   ├── run_straight_stack.sh     # 전체 스택 원클릭 실행
│   │   └── test/                     # GPIO/인코더/IMU 테스트
│   │
│   └── orin_nano_runtime/            # 고수준 런타임 (Nav2 + AI)
│       ├── config.py                 # 런타임 설정
│       ├── controller.py             # 시뮬레이션 마스터 컨트롤러
│       ├── real_controller.py        # 실제 로봇 Nav2 컨트롤러
│       ├── detector_node.py          # YOLO TensorRT + OSNet ReID
│       ├── detector_monkey_node.py   # 커스텀 모델 + ByteTrack
│       ├── detector_monkey_perform_node.py  # 파라미터 조정 가능 디텍터
│       ├── follower_node.py          # 사람 추종 (포텐셜필드+PID)
│       ├── sub_motor_control.py      # /cmd_vel → 모터 변환
│       ├── motor_hat.py              # PCA9685 드라이버
│       ├── 1.5_keyboard_slam_drive.py # 키보드 SLAM 매핑 도구
│       ├── test.py                   # 풀기능 ReID 갤러리 테스트
│       ├── real_robot_launch.py      # 전체 통합 런치
│       ├── robot_hardware.launch.py  # 하드웨어 계층 런치
│       ├── robot_nav.launch.py       # 내비게이션 계층 런치
│       ├── robot_app.launch.py       # 애플리케이션 계층 런치
│       ├── build_trt_engine.sh       # TensorRT 엔진 빌드
│       ├── tasks.json                # VS Code 7단계 부팅
│       ├── config/
│       │   ├── follower_params.yaml  # 추종모드 Nav2 파라미터
│       │   └── nav2_params.yaml      # 전체 Nav2 파라미터
│       └── worlds/
│           ├── mart.pgm              # 점유격자 지도 이미지
│           └── mart.yaml             # 지도 메타데이터
│
├── raspberry_pi/                     # 키오스크 + RFID (라즈베리파이 5)
│   ├── frontend/                     # Vue 3 키오스크 앱
│   │   ├── src/
│   │   │   ├── App.vue               # 루트 (RFID WS, 로봇 초기화)
│   │   │   ├── config.js             # 환경변수 + MAP_INFO
│   │   │   ├── api/
│   │   │   │   ├── index.js          # Axios + JWT 인터셉터
│   │   │   │   ├── rosManager.js     # ROS Bridge 싱글톤
│   │   │   │   ├── productApi.js     # 상품 API
│   │   │   │   ├── locationApi.js    # 위치 API
│   │   │   │   └── couponApi.js      # 쿠폰 API
│   │   │   ├── store/
│   │   │   │   ├── cart.js           # 장바구니 (RFID+쿠폰+추천)
│   │   │   │   ├── navigation.js     # Dijkstra 경로 + 로봇 위치
│   │   │   │   └── user.js           # JWT 인증
│   │   │   ├── utils/
│   │   │   │   ├── dijkstra.js       # 그래프 + 최단경로
│   │   │   │   ├── mapRenderer.js    # Canvas 지도 렌더링
│   │   │   │   ├── mathUtil.js       # 거리/방향 계산
│   │   │   │   ├── audio.js          # 효과음 재생
│   │   │   │   └── keyboardInput.js  # 한글 조합 처리
│   │   │   ├── composables/
│   │   │   │   └── useTossPayment.js # 토스 결제 연동
│   │   │   ├── views/ (10개 화면)
│   │   │   ├── components/common/
│   │   │   ├── router/index.js
│   │   │   └── plugins/vuetify.js
│   │   ├── package.json
│   │   ├── vite.config.js
│   │   └── .env
│   ├── frontend_perform/             # 데모/발표용 프론트 사본
│   └── rfid/
│       ├── rfid_server.py            # 실제 MFRC522 + WebSocket
│       └── rfid_mock_server.py       # PC 테스트용 Mock
│
├── server/                           # 백엔드 서버
│   └── backend/
│       ├── run.py                    # Flask 진입점 (포트 5001)
│       ├── .env                      # DB/AWS/Toss/AI 키
│       ├── requirements.txt
│       ├── app/
│       │   ├── __init__.py           # 앱 팩토리 + 블루프린트 9개
│       │   ├── config.py             # 환경변수 로딩
│       │   ├── extensions.py         # SQLAlchemy/JWT/CORS 등
│       │   ├── models/               # ORM 모델 8개
│       │   ├── routes/               # API 라우트 9개
│       │   ├── schemas/              # Marshmallow 직렬화
│       │   ├── services/             # 비즈니스 로직
│       │   └── utils/                # 응답/시간/이미지 유틸
│       └── smartcartDB/0.3/
│           └── Smart_Cart_DB.sql     # DDL 10테이블
│
├── simulation/                       # Gazebo 시뮬레이션
│   ├── follower_tracking/
│   ├── orin_nano_test/
│   └── test_Nav2/
│
├── yolo/                             # YOLO 학습/실험
│   ├── yolo.py                       # YOLO+ReID+Face 퓨전
│   ├── yolo_best_model.py            # 이중임계값+갤러리 관리
│   └── monkey_model4/               # 커스텀 YOLO 학습
│
├── TIL/                              # 팀원 6명 학습 기록
├── .gitlab-ci.yml                    # CI/CD 파이프라인
└── readme.md                         # 프로젝트 문서
```

---

## 3. 시스템 아키텍처

```
┌──────────────────────────────────────────────────────────────────────┐
│                    Raspberry Pi 5 (키오스크)                          │
│                                                                      │
│  ┌─ Vue 3 프론트엔드 ─────────────────────────────────────────────┐   │
│  │  Pinia 상태관리 | Vuetify UI | 한글 가상키보드 | 토스 결제        │   │
│  │  Dijkstra 경로탐색 | Canvas 지도 | MJPEG 카메라 뷰               │   │
│  └──────────┬──────────┬──────────┬──────────────────────────────┘   │
│             │          │          │                                   │
│     REST API│  ROS WS  │  RFID WS │                                  │
│   (5001포트) │ (9090포트)│ (8765포트)│                                 │
│             │          │          │                                   │
│  ┌──────────┘     ┌────┘     ┌────┘                                  │
│  │                │          │  ┌─ RFID 서버 ─────┐                   │
│  │                │          └──│ MFRC522 + pygame │                  │
│  │                │             └──────────────────┘                  │
└──│────────────────│──────────────────────────────────────────────────┘
   │                │
   │                │ WebSocket (rosbridge)
   │                │
┌──│────────────────│──────────────────────────────────────────────────┐
│  │    Jetson Orin Nano (로봇 두뇌)                                    │
│  │                │                                                  │
│  │    ┌───────────┴───────────────────────────────────────────┐      │
│  │    │              ROS 2 Humble 노드 네트워크                │      │
│  │    │                                                       │      │
│  │    │  real_controller ─── Nav2 (AMCL+DWB+Costmap)          │      │
│  │    │       │                    │                           │      │
│  │    │       │              /cmd_vel                          │      │
│  │    │       │                    │                           │      │
│  │    │  detector_node ──→ follower_node ──→ sub_motor_control │      │
│  │    │  (YOLO+ReID)     (포텐셜필드+PID)     (차동구동)         │      │
│  │    │                                          │             │      │
│  │    │  5_odom_publisher ←── 휠 인코더           │             │      │
│  │    │  6_imu_publisher  ←── MPU6050            │             │      │
│  │    │       │                                   │             │      │
│  │    │       └──→ EKF 센서퓨전 ──→ /odom         │             │      │
│  │    │                                           ↓             │      │
│  │    │                              PCA9685 Motor HAT ──→ 모터 │      │
│  │    └───────────────────────────────────────────────────────┘      │
│  │                                                                   │
│  │    하드웨어: YDLidar X4 Pro | USB카메라 | GA25-370 모터×2           │
│  │              MPU6050 IMU | 휠인코더×2 | 캐스터휠                     │
└──│───────────────────────────────────────────────────────────────────┘
   │
┌──▼──────────────────────────────┐
│      Cloud (EC2 서버)            │
│  Flask API (5001포트)            │
│  MySQL (AWS RDS)                │
│  AWS S3 (이미지 저장)            │
│  Toss Payments API              │
│  GMS AI API (GPT-5.2 추천)      │
└─────────────────────────────────┘
```

---

## 4. 저수준 차량 제어 (`jetson_vehicle_control/`)

### 4-1. 하드웨어 설정 (`config.py`)

| 상수 | 값 | 안전등급 | 설명 |
|------|-----|---------|------|
| `MOTOR_HAT_I2C_ADDRESS` | `0x40` | 빨강(변경금지) | 모터 HAT I2C 주소 |
| `PWM_FREQUENCY` | `1000` Hz | 빨강 | PWM 주파수 |
| `MOTOR_SAFE_SPEED` | `0.6` | 빨강 | 최대 속도 (0.7 초과 시 과열) |
| `SPEED_NORMAL` | `0.3` | 초록(자유변경) | 기본 주행 속도 |
| `OBSTACLE_DISTANCE` | `1.0` m | 초록 | 장애물 정지 거리 |
| `CONFIDENCE_THRESHOLD` | `0.5` | 초록 | YOLO 신뢰도 |
| `TURN_THRESHOLD` | `40` px | 초록 | 조향 감도 |

### 4-2. 모터 드라이버 (`motor_hat.py`)

PCA9685 기반 2채널 DC 모터 제어. 좌측 모터(A)는 SW 반전 배선.

```
Left Motor (A):  PWMA=ch0, AIN1=ch2, AIN2=ch1
Right Motor (B): BIN1=ch3, BIN2=ch4, PWMB=ch5
```

- `straight(speed)`: 직진 (LEFT_FACTOR/RIGHT_FACTOR 보정 적용)
- `drive(left, right)`: 독립 좌/우 제어 (차동구동)
- `turn_left/right(speed)`: 제자리 회전 (한쪽 전진, 반대쪽 후진)
- 속도 클램핑: `[-0.6, +0.6]` 범위 제한

### 4-3. 휠 인코더 오도메트리 (`5_odom_publisher.py`)

**하드웨어 상수:**

| 상수 | 값 | 설명 |
|------|-----|------|
| `WHEEL_DIAMETER` | 0.064m | 바퀴 지름 |
| `WHEEL_BASE` | 0.16m | 바퀴 간 거리 |
| `PPR` | 11 | 인코더 펄스/회전 |
| `GEAR_RATIO` | 20 | 기어비 |
| `TICKS_PER_REV` | 220 | 1회전당 총 틱 |

**GPIO 핀:** LEFT_A=7, LEFT_B=11, RIGHT_A=13, RIGHT_B=15 (BOARD 모드)

**알고리즘 (100Hz):**
- 폴링 스레드로 인코더 틱 카운팅 (GPIO 인터럽트 불안정하여 폴링 방식 채택)
- 차동구동 역기구학으로 위치 추정
- `odom → base_link` TF 브로드캐스트
- 공분산: 대각 [x, y, yaw] = 0.01

### 4-4. IMU 발행 (`6_imu_publisher.py`)

**MPU6050 설정:** GYRO_CONFIG=24 (+/-2000 dps), 기본 ACCEL (+/-2g)

**알고리즘 (20Hz):**
- 시작 시 200샘플 자이로 Z 캘리브레이션
- 가속도: raw/16384 × 9.81 (m/s²)
- 자이로: raw/131 × π/180 (rad/s), 바이어스 제거 후 지수 LPF (α=0.9)

### 4-5. 직진 보정 컨트롤러 (`7_straight_drive_fusion.py`)

**PID 파라미터:** KP=3.0, KI=0.0, KD=0.1, max_correction=1.0

**알고리즘 (30Hz):**
1. `/cmd_vel` 수신 → 직진 판별 (`|linear| ≥ 0.05` AND `|angular| ≤ 0.05`)
2. 직진 시작 시 현재 IMU yaw를 목표값으로 캡처
3. IMU 자이로 Z를 적분하여 실시간 yaw 추정
4. PID로 각속도 보정값 계산 → `/cmd_vel`의 angular에 더함
5. 차동구동 변환 → 모터 출력 (linear 방향 반전 보정)
6. 0.5초 명령 타임아웃 시 자동 정지

### 4-6. 단계별 학습 스크립트

| 스크립트 | 기능 | 핵심 로직 |
|---------|------|----------|
| `1_keyboard_control.py` | SSH 수동 조작 | `getch()`로 raw 키 입력, w/a/s/d/q |
| `2_slam_mapping.py` | LiDAR 지도 저장 | 100스캔 수집 → 극좌표 플롯 PNG |
| `3_slam_navigation.py` | 장애물 회피 주행 | 전방 30도 LiDAR → 1m 이내 시 좌회전 |
| `4_autonomous_drive.py` | YOLO+LiDAR 자율주행 | 사람 감지 시 추종, 장애물 우선 회피 |

---

## 5. 고수준 런타임 (`orin_nano_runtime/`)

### 5-1. 3계층 런치 시스템

```
Terminal 1: robot_hardware.launch.py
  ├── USB 카메라 (640×480, 30fps, mjpeg2rgb)
  └── Robot State Publisher (TurtleBot3 Waffle Pi URDF)

Terminal 2: robot_nav.launch.py
  ├── Static TF: base_link → base_footprint
  ├── Nav2 Bringup (기존 지도 또는 SLAM 모드)
  ├── Rosbridge WebSocket (9090포트)
  └── Web Video Server (8080포트)

Terminal 3: robot_app.launch.py
  ├── follower_node.py (사람 추종)
  ├── real_controller.py (Nav2 웨이포인트)
  └── sub_motor_control.py (모터 브릿지)
```

**VS Code tasks.json** 7단계 순차 부팅:
1. 다리(Odom) → 2. 눈(LiDAR) → 3. 뇌(IMU+EKF) → 4. 관절(TF) → 5. 하드웨어 → 6. 네비게이션 → 7. 애플리케이션

**Static TF:** `base_link → laser_frame` (LiDAR 장착 위치: 전방 0.1m, 높이 0.2m)

### 5-2. 마스터 컨트롤러

**`controller.py` (시뮬레이션):**
- `FollowerManager`: detector + follower를 서브프로세스로 1회 생성 (메모리 상주)
- `use_sim_time=True`, 종료 시 SIGINT → 2초 → kill

**`real_controller.py` (실제 로봇):**
- `use_sim_time=False`, 서브프로세스 관리 없음
- 나머지 로직 동일

**공통 기능:**

| 기능 | 토픽 | 설명 |
|------|------|------|
| 웨이포인트 수신 | `/robot/destination` → Nav2 액션 | YAML 파싱 → NavigateThroughPoses |
| 모드 전환 | `/robot/mode` | STOP 시 Nav2 취소 + `ROBOT_STOPPED` 발행 |
| 초기위치 설정 | `/robot/set_init_pose` → `/initialpose` | AMCL 파티클 리셋 |
| 위치 릴레이 | `/amcl_pose` → `/robot/current_pose` | JSON `{x, y}` 프론트 전달 |
| 상태 보고 | `/robot/status` | `ACK_NAV`, `ACK_STOP`, `ARRIVED` |

### 5-3. 디텍터 노드 3세대

**① `detector_node.py` — TensorRT + ReID**

| 항목 | 값 |
|------|-----|
| YOLO 모델 | `yolo11n.engine` (TensorRT FP16) |
| ReID 모델 | `osnet_x0_25` (CPU) |
| YOLO 설정 | persist=True, classes=0, imgsz=320, half=True |
| 매칭 임계값 | L2 거리 < 0.5 |
| Owner 인코딩 | `det.id = obj_id + 1000` |

REGISTER 모드에서 갤러리 구축, TRACK 모드에서 ReID 매칭.

**② `detector_monkey_node.py` — 커스텀 모델**

| 항목 | 값 |
|------|-----|
| 모델 | `monkey_model.pt` (커스텀 학습) |
| 트래커 | ByteTrack |
| 프레임 스킵 | 2프레임마다 1회 |
| 타겟 선택 | 최대 면적 바운딩박스 |
| 출력 리사이즈 | 320×240 (대역폭 최적화) |
| GC | 200프레임마다 |
| 실행기 | MultiThreadedExecutor |

**③ `detector_monkey_perform_node.py` — 파라미터 조정 가능**

| ROS 파라미터 | 기본값 | 설명 |
|-------------|--------|------|
| `imgsz` | 416 | 추론 입력 크기 |
| `conf_thres` | 0.35 | 신뢰도 임계값 |
| `iou_thres` | 0.5 | NMS IoU |
| `frame_skip` | 1 | 프레임 스킵 |
| `start_active` | False | 시작 시 활성화 |

신뢰도 90%↑ 감지 시 빨간 "Match" 오버레이. 5초마다 디버그 통계 로깅.

### 5-4. 사람 추종 (`follower_node.py`)

**핵심 상수:**

| 상수 | 값 |
|------|-----|
| `TARGET_DISTANCE` | 0.5m |
| `CLOSE_PROXIMITY_LIMIT` | 0.10m |
| `MAX_LINEAR_VEL` | 0.35 m/s |
| `MAX_ROTATION_SPEED` | 0.6 rad/s |
| `PID_KP / KD` | 0.5 / 0.03 |
| `OBSTACLE_CHECK_DIST` | 0.5m |
| `LIDAR_AVOIDANCE_WEIGHT` | 0.4 |
| `ANGLE_SMOOTHING_ALPHA` | 0.4 |

**5단계 상태 머신:**
```
WAITING → SEARCHING → VISUAL_TRACKING → BLIND_TRACKING → RECOVERY
                ↑                                            │
                └────────────────────────────────────────────┘
```

- VISUAL_TRACKING: YOLO 감지 + LiDAR 거리 + 포텐셜필드 장애물 회피
- BLIND_TRACKING: 1.0초 시각 타임아웃 → LiDAR 최근접 이웃 탐색
- RECOVERY: 3.0초 블라인드 타임아웃 → Nav2로 마지막 위치 복귀
- SEARCHING: 제자리 대기

**포텐셜 필드:** 인력(목표 방향 크기 2.0) + 척력(0.5m 이내, 전면 100도)
**피벗 턴:** 목표 각도 > 20° → linear=0 (제자리 회전)
**정적 장애물 필터링:** TF 변환으로 LiDAR 포인트를 맵 좌표로 변환, OccupancyGrid > 50 체크

### 5-5. 모터 구독자 (`sub_motor_control.py`)

```
/cmd_vel 수신 → linear 반전(-1배) → angular 스케일(×0.4)
→ left = linear - angular, right = linear + angular
→ motor_hat.drive(left, right)
```

### 5-6. Nav2 파라미터

**`nav2_params.yaml` (전체 설정, 350줄):**

| 구성요소 | 핵심 파라미터 |
|---------|-------------|
| **AMCL** | base_footprint 프레임, 500~2000 파티클, Likelihood Field |
| **DWB** | max_vel_x=0.35, max_vel_theta=1.5, sim_time=1.7 |
| **Global Planner** | NavfnPlanner, Dijkstra, tolerance=0.5 |
| **Behavior** | Spin, BackUp, DriveOnHeading, Wait |
| **Velocity Smoother** | max=[0.35, 0.0, 1.5], OPEN_LOOP |
| **Local Costmap** | 3×3m, VoxelLayer + Inflation(0.55m) |
| **Global Costmap** | Static + Obstacle + Inflation(0.55m) |

**`follower_params.yaml` (추종모드 특화, 197줄):**

| 차이점 | 값 |
|--------|-----|
| base_frame | `base_link` (nav2_params는 base_footprint) |
| max_vel_theta | 1.8 (더 빠른 회전) |
| Local inflation | radius=0.50, cost_scaling=40.0 |
| Global inflation | radius=0.10, cost_scaling=70.0 (좁은 통로용) |
| QoS | BEST_EFFORT (LiDAR 호환) |

### 5-7. 지도 설정 (`mart.yaml`)

| 파라미터 | 값 |
|---------|-----|
| 해상도 | 0.05 m/px |
| 원점 | (-4.0, -4.0, 0.0) |
| 점유 임계 | 0.65 |
| 비점유 임계 | 0.196 |

---

## 6. 프론트엔드 (`raspberry_pi/frontend/`)

### 6-1. 기술 스택

Vue 3 + Vuetify 3 + Pinia + Vite + roslib + Toss Payments SDK + hangul-js

### 6-2. 환경설정

| 변수 | 값 |
|------|-----|
| `VITE_API_URL` | `http://i14d201.p.ssafy.io:5001/api` |
| `VITE_JETSON_IP` | `192.168.137.18` |
| `VITE_JETSON_ROS_PORT` | `9090` |
| `VITE_JETSON_VIDEO_PORT` | `8080` |
| `VITE_TOSS_CLIENT_KEY` | 테스트 키 |

### 6-3. ROS 통신 (`rosManager.js`)

싱글톤 클래스, 자동 3초 재연결.

| 토픽 | 방향 | 용도 |
|------|------|------|
| `/robot/destination` | 발행 | JSON 웨이포인트 전송 |
| `/robot/mode` | 발행 | REGISTER/FOLLOW/NAV/STOP/RESUME |
| `/robot/set_init_pose` | 발행 | AMCL 초기 위치 |
| `/robot/current_pose` | 구독 | 실시간 로봇 위치 {x, y} |
| `/robot/status` | 구독 | REGISTER_DONE, ARRIVED 등 |

### 6-4. 상태 관리 (Pinia)

**`cart.js` (304줄):**
- RFID 스캔 핸들링: `rfidRemovalTargetId` 설정 시 제거, 아닐 때 추가
- AI 추천: 장바구니 변경 시마다 `POST /products/recommend` 호출
- 쿠폰: 할인액 계산, 최종가 = 상품합계 - 할인 (최소 0원)
- localStorage 영속화

**`navigation.js` (98줄):**
- 백엔드 `GET /map/`에서 그래프 데이터 로드 → `Graph.build()`
- 로봇 위치 갱신 시 최근접 노드 스냅 (0.5m 임계)
- `getNavigationPayload()`: Dijkstra 실행 → 각 웨이포인트에 방향 쿼터니언(z, w) 계산

**`user.js`:**
- `login()` → JWT 토큰 저장 (localStorage)
- `fetchUserInfo()` → `/users/me`
- 401 응답 시 자동 로그아웃

### 6-5. 유틸리티

| 파일 | 기능 |
|------|------|
| `dijkstra.js` | `Graph` 클래스: build, findPath, findNearestNode |
| `mapRenderer.js` | 월드→캔버스 좌표 변환, 배경/경로/마커 렌더링 |
| `mathUtil.js` | 유클리드 거리, 방향 쿼터니언(z, w) 계산 |
| `audio.js` | Audio 객체 캐시 + 재생 |
| `keyboardInput.js` | hangul-js로 자모 분해/조합 |

### 6-6. 10개 화면 흐름

```
① HomeView (/)
   "회원" → ② LoginView (/login) → ③ RegisterYoloView
   "비회원" → ③ RegisterYoloView (/register-yolo)

③ RegisterYoloView
   YOLO 카메라 표시, REGISTER 모드 전송
   REGISTER_DONE 수신 → ④ ProductListView

④ ProductListView (/products)
   카테고리 필터 | 검색 | AI 추천 패널
   상품 터치 → Nav2 웨이포인트 전송 → ⑥ GuideView
   "따라가기" → ⑦ FollowView
   "쇼핑 종료" → ⑨ PaymentView

⑤ CartView (/cart)
   장바구니 목록 | 수량 관리 | RFID 재스캔 삭제
   "결제하기" → ⑨ PaymentView

⑥ GuideView (/guide)
   Canvas 실시간 지도 (배경+계획경로+이동경로+마커)
   일시정지/재개 | 목적지 변경

⑦ FollowView (/follow)
   YOLO 카메라 스트림 | FOLLOW 모드 활성화
   일시정지/재개

⑨ PaymentView (/payment)
   쿠폰 선택 | 결제수단 (카드/간편결제/포인트)
   → ⑧ FinishShopView

⑧ FinishShopView (/finish)
   "여기서 반납" → STOR-001로 Nav2 → ⑩ ThanksView
   "주차장 이동" → 차번호 검색 → 주차위치로 Nav2 → ⑥ GuideView

⑩ ThanksView (/thanks)
   ARRIVED 수신 → 초기위치 리셋 → ① 홈으로 복귀
```

### 6-7. RFID 통합

```
App.vue에서 ws://hostname:8765 연결
  ↓ 태그 스캔 메시지 수신
  ↓ cartStore.handleRfidScan(productId)
  ↓
rfidRemovalTargetId 설정됨?
  ├─ Yes + ID 일치 → 상품 1개 제거 (lastRfidEvent.action='removed')
  └─ No → 장바구니에 추가 (lastRfidEvent.action='added')
  ↓
App.vue가 lastRfidEvent 감시 → 초록 스낵바 토스트
```

---

## 7. 백엔드 서버 (`server/backend/`)

### 7-1. 기술 스택

Flask + SQLAlchemy + MySQL(AWS RDS) + JWT + Marshmallow + boto3(S3) + Flasgger

### 7-2. 데이터베이스 스키마 (v0.3, 10테이블)

| 테이블 | 역할 | 주요 컬럼 |
|--------|------|----------|
| `users` | 사용자 | user_id, login_id(unique), password(해시), user_name |
| `categories` | 상품 분류 | category_id, category_name |
| `locations` | 매장 좌표 노드 | location_id, location_code(unique), category, pos_x, pos_y |
| `location_paths` | 그래프 엣지 | node1_id, node2_id (양방향, unique) |
| `products` | 상품 | product_id, category_id(FK), location_id(FK), product_name, price |
| `coupons` | 쿠폰 | coupon_id, user_id(FK), discount_amount, is_used, expire_date |
| `carts` | 물리 카트 | cart_id, user_id(FK, nullable), status(WAITING/USED/RETURN/ERROR) |
| `park_info` | 주차 정보 | park_info_id, location_id(FK), car_number, entry_time |
| `orders` | 주문 (미구현) | order_id, user_id, cart_id, total_price, final_price |
| `order_items` | 주문 상세 (미구현) | order_id, product_id, quantity, total_price |

### 7-3. API 엔드포인트

| Method | 경로 | 인증 | 기능 |
|--------|------|------|------|
| POST | `/api/users/login` | 없음 | 로그인 → JWT 발급 |
| GET | `/api/users/me` | JWT | 내 정보 조회 |
| GET | `/api/products/` | 없음 | 상품 목록 (카테고리/키워드 필터) |
| GET | `/api/products/<id>` | 없음 | 상품 상세 |
| GET | `/api/products/categories` | 없음 | 카테고리 목록 |
| POST | `/api/products/recommend` | 없음 | AI 상품 추천 |
| POST | `/api/carts/rent` | 없음 | 카트 대여 (WAITING→USED) |
| POST | `/api/carts/return` | 없음 | 카트 반납 (USED→WAITING) |
| GET | `/api/coupons/<user_id>` | 없음 | 사용 가능 쿠폰 조회 |
| POST | `/api/coupons/use/<id>` | 없음 | 쿠폰 사용 처리 |
| GET | `/api/locations/` | 없음 | 위치 조회 (코드/카테고리) |
| GET | `/api/parking/search` | 없음 | 차량번호로 주차 검색 |
| GET | `/api/map/` | 없음 | 매장 그래프 (노드+엣지) |
| GET | `/api/payment/toss/success` | 없음 | 토스 결제 성공 콜백 |
| GET | `/api/payment/toss/fail` | 없음 | 토스 결제 실패 콜백 |

### 7-4. AI 상품 추천 로직 (`product_service.py`)

1. 장바구니 상품의 카테고리 중 하나를 무작위 선택
2. 해당 카테고리에서 장바구니에 없는 후보 30개 추출 (랜덤 정렬)
3. 카테고리별 맞춤 프롬프트 생성 (식품/생활용품/문구완구/패션/디지털)
4. GMS API (GPT-5.2)에 전송 → 상품명 1개 응답
5. 응답이 후보 목록에 없으면 ILIKE 검색 → 그래도 없으면 첫 번째 후보 반환
6. 전체 실패 시 첫 번째 후보를 폴백으로 반환

---

## 8. RFID 시스템 (`raspberry_pi/rfid/`)

**`rfid_server.py` (실제 하드웨어):**
- MFRC522 RFID 리더 (SPI 연결)
- WebSocket 서버 `0.0.0.0:8765`
- 태그 읽기 → beep.wav 재생 (pygame) → 상품 ID 전송
- 2초 쿨다운

**`rfid_mock_server.py` (PC 테스트):**
- 터미널 stdin에서 상품 ID 입력
- 동일 WebSocket 프로토콜

---

## 9. YOLO/CV 실험 (`yolo/`)

### 9-1. `yolo.py` — 기본 퓨전 감지

YOLO 26n + OSNet x0.25 + InsightFace. REGISTER(30캡처) → TRACK(하이브리드 매칭). 거리 추정: `500/pixel_height`. 각도: `((cx/width)-0.5)×60°`.

### 9-2. `yolo_best_model.py` — 최종 알고리즘

이중 임계값 + 갤러리 관리:
- STRICT=0.5 (최초 확인), LOOSE=0.70 (확정 후 유지)
- 40캡처 등록, 다양성 체크 (유사도 > 0.94 거부)
- 동적 갤러리 업데이트 (최대 100개, FIFO)
- ID 잠금 → 얼굴 확인 후 YOLO ID에 대해 느슨한 임계값 적용

### 9-3. 커스텀 모델 학습 (`monkey_model4/args.yaml`)

yolo26n 기반, 100 에포크, 배치 32, 640px, BotSort 트래커, AMP 활성화

---

## 10. 시뮬레이션 (`simulation/`)

- `follower_tracking/`: Gazebo 환경에서 사람 추종 테스트
- `orin_nano_test/`: controller + follower + detector 시뮬레이션
- `test_Nav2/`: Nav2 웨이포인트 내비게이션 테스트

TurtleBot3 Waffle Pi URDF 모델, 커스텀 마트 월드 파일 사용.

---

## 11. CI/CD (`.gitlab-ci.yml`)

master 브랜치 push 시 단일 deploy 스테이지:
1. EC2 서버의 `/home/ubuntu/server-app/`에 코드 복사
2. Python venv 생성/활성화
3. 의존성 설치
4. 기존 Flask 프로세스 종료 → `nohup python run.py` 재시작

---

## 12. ROS 토픽 전체 맵

| 토픽 | 메시지 타입 | 발행자 | 구독자 |
|------|-----------|--------|--------|
| `/image_raw` | Image | usb_cam | detector 노드들 |
| `/yolo_result` | Image | detector 노드들 | web_video_server |
| `/detections` | Detection2DArray | detector 노드들 | follower_node |
| `/robot/status` | String | controller, detector | 프론트엔드 (rosbridge) |
| `/robot/mode` | String | 프론트엔드 | controller, detector, follower |
| `/robot/destination` | String | 프론트엔드 | controller |
| `/robot/set_init_pose` | String | 프론트엔드 | controller |
| `/robot/current_pose` | String | controller | 프론트엔드 |
| `/initialpose` | PoseWithCovarianceStamped | controller | AMCL |
| `/amcl_pose` | PoseWithCovarianceStamped | AMCL | controller |
| `/cmd_vel` | Twist | Nav2, follower | sub_motor_control |
| `/scan` | LaserScan | ydlidar | follower, Nav2 |
| `/map` | OccupancyGrid | map_server | follower_node |
| `/odom` | Odometry | odom_publisher | Nav2, EKF |
| `/imu/data` | Imu | imu_publisher | EKF, 직진보정 |

---

## 13. 통신 채널 요약

| 채널 | 프로토콜 | 포트 | 용도 |
|------|---------|------|------|
| 프론트↔백엔드 | REST (Axios) | 5001 | 상품/유저/쿠폰/지도/결제 API |
| 프론트↔Jetson | WebSocket (roslib) | 9090 | 로봇 명령/상태/위치 |
| 프론트↔카메라 | MJPEG HTTP | 8080 | YOLO 결과 영상 스트림 |
| 프론트↔RFID | WebSocket (raw) | 8765 | 태그 스캔 이벤트 |
| Jetson 내부 | ROS 2 DDS | - | 노드 간 토픽/액션/TF |
| 백엔드↔AI | HTTPS | GMS 프록시 | GPT-5.2 상품 추천 |
| 백엔드↔결제 | HTTPS | Toss API | 결제 승인 |

---