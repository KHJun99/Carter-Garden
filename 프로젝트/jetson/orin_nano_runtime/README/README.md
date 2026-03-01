# Jetson Orin Nano 기반 카트 주행 제어

ROS 2 Humble 환경에서 IMU, Encoder(Odom), LiDAR 데이터를 융합하여 정밀한 주행 제어를 수행합니다.

## 주요 파일 설명

| 파일명 | 주요 기능 및 역할 |
| --- | --- |
| **`1_keyboard_control.py`** | ROS 토픽을 사용하지 않고 I2C 통신으로 모터를 직접 제어하는 기초 테스트 코드입니다. |
| **`4_autonomous_drive.py`** | LiDAR 장애물 회피와 카메라(YOLO) 객체 인식을 결합한 자율주행 통합 제어 스크립트입니다. |
| **`5_odom_publisher.py`** | 바퀴 엔코더 값을 읽어 로봇의 이동 거리와 속도 정보인 `/odom` 토픽을 발행합니다. |
| **`6_imu_publisher.py`** | MPU6050 센서 데이터(가속도/각속도)를 읽어 `/imu/data` 토픽을 발행합니다. |
| **`7_straight_drive_fusion.py`** | **[최종 수정]** IMU 각속도를 직접 적분하여 계산한 각도와 EKF 데이터를 기반으로 직진 보정을 수행합니다. |
| **`real_robot_launch.py`** | **[NEW]** 실물 로봇을 위한 통합 실행 파일입니다. (YDLidar, Camera, Odom, IMU, Nav2, Rosbridge 실행) |
| **`real_controller.py`** | **[NEW]** 실물 로봇용 메인 컨트롤러 노드입니다. Nav2 및 상태 관리를 담당합니다. |
| **`motor_hat.py`** | Motor HAT 하드웨어 제어를 위한 드라이버 파일로, 좌/우 모터 독립 제어를 지원합니다. |
| **`config.py`** | `MOTOR_SAFE_SPEED` 및 LiDAR 탐지 범위 등 하드웨어 관련 설정 상수를 관리합니다. |
| **`run_straight_stack.sh`** | 센서 발행부터 보정 노드 실행까지 전체 프로세스를 한 번에 실행하는 쉘 스크립트입니다. |

---

## 🚀 실물 로봇 통합 실행 가이드 (Real Robot Integration)

실제 로봇(Jetson Orin Nano)에서 자율 주행 및 제어 시스템을 구동하는 방법입니다.

### 1. 시스템 통합 구조 (Architecture)

시스템은 크게 **로봇(Jetson)**, **AI 서버(Docker)**, **제어기(Laptop)** 세 부분으로 나뉩니다. 모든 장치는 **동일한 Wi-Fi 네트워크**에 연결되어 있어야 합니다.

*   **Jetson Orin Nano (Robot)**
    *   **하드웨어 드라이버**: YDLidar, USB Camera, Motor Driver, IMU/Encoder
    *   **코어 시스템**: ROS 2 Humble, Nav2 (AMCL/Planner), Rosbridge Server
    *   **애플리케이션**: `real_controller.py` (상태 관리), `follower_node.py` (추종 로직)
*   **Docker Container (AI)**
    *   **Detector Node**: `/camera/image_raw` 토픽을 구독하여 YOLO 객체 인식을 수행하고, `/detections` 토픽으로 결과 전송.
*   **Laptop (Frontend/Control)**
    *   **Vue.js App**: Rosbridge(`ws://<JETSON_IP>:9090`)를 통해 로봇 상태 확인 및 명령 전송.
    *   **Rviz2**: 로봇의 지도 및 경로 시각화 (SSH X11 forwarding 혹은 로컬 실행 후 ROS_DOMAIN_ID 일치).

### 2. 실행 순서 (Execution Steps)

#### 단계 1: 로봇 실행 (Jetson Orin Nano)

`real_robot_launch.py` 하나만 실행하면 필요한 모든 하드웨어 드라이버와 노드가 실행됩니다.

```bash
# 워크스페이스 소싱 (필요 시)
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash

# 런치 파일 실행
cd /home/d201/test_d201_ssafy/test_minseo/Jetson_Orin_Nano
ros2 launch real_robot_launch.py
```

> **주요 실행 내용:**
> *   Lidar, Camera, IMU, Odom 드라이버 시작
> *   Nav2 네비게이션 스택 (Map 로드 포함) 시작
> *   Rosbridge Server (포트 9090) 시작
> *   Follower 및 Real Controller 노드 시작

#### 단계 2: 객체 인식 실행 (Docker)

별도의 터미널(또는 Docker 컨테이너)에서 객체 인식 노드를 실행합니다. 이 노드는 로봇이 발행한 이미지를 받아 사람을 감지합니다.

```bash
# (예시) Docker 진입 후 Detector 실행
python3 detector_node.py
```

#### 단계 3: 원격 제어 및 시각화 (Laptop)

노트북에서 로봇과 통신하여 모니터링하거나 제어합니다.

**1. Rviz2 실행 (시각화)**
같은 와이파이 망에서 `ROS_DOMAIN_ID`를 맞추거나, SSH `-X` 옵션 등을 활용합니다.

```bash
# Nav2 기본 Rviz 설정으로 실행 (옵션)
ros2 run rviz2 rviz2 -d $(ros2 pkg prefix nav2_bringup)/share/nav2_bringup/rviz/nav2_default_view.rviz
```

**2. 프론트엔드 연결 (웹 제어)**
웹 애플리케이션에서 로봇의 IP 주소와 포트(9090)를 입력하여 연결합니다.

---

## 🔧 문제 해결 (Troubleshooting)

*   **카메라 이미지가 안 나올 때:**
    *   `ls /dev/video*` 로 장치 확인 후 런치 파일의 `video_device` 경로를 수정하세요.
*   **LiDAR 에러:**
    *   USB 연결을 확인하고 권한을 부여하세요 (`sudo chmod 666 /dev/ttyUSB0` 등).
*   **Nav2 맵이 로드되지 않음:**
    *   `worlds/mart.yaml` 파일 경로가 정확한지 확인하세요.
*   **모터가 움직이지 않음:**
    *   `1_keyboard_control.py`로 하드웨어 연결을 먼저 테스트하세요.