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
| **`motor_hat.py`** | Motor HAT 하드웨어 제어를 위한 드라이버 파일로, 좌/우 모터 독립 제어를 지원합니다. |
| **`config.py`** | `MOTOR_SAFE_SPEED` 및 LiDAR 탐지 범위 등 하드웨어 관련 설정 상수를 관리합니다. |
| **`run_straight_stack.sh`** | 센서 발행부터 보정 노드 실행까지 전체 프로세스를 한 번에 실행하는 쉘 스크립트입니다. |

---

## 직진 보정(Straight Drive) 테스트 가이드

### 1. 환경 준비 및 빌드 (필수)

`ekf.yaml` 등 설정 파일이 변경되었을 경우, 반드시 빌드 후 소싱해야 합니다.

```bash
# 1. 워크스페이스 이동
cd ~/ros2_ws

# 2. 변경된 패키지 빌드 (ekf.yaml 반영)
colcon build --packages-select simple_imu

# 3. 환경 소싱 (모든 터미널에서 실행)
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash

```

### 2. 노드 실행 순서

* **터미널 1 (IMU):** `python3 6_imu_publisher.py`
* **터미널 2 (Odom):** `python3 5_odom_publisher.py`
* **터미널 3 (EKF):** `ros2 launch simple_imu imu_ekf_launch.py`
* **터미널 4 (보정 컨트롤러):** `python3 7_straight_drive_fusion.py`
* **터미널 5 (조작):** `ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r /cmd_vel:=/cmd_vel`

---

## 제어 파라미터 상세 (7번 코드)

로봇이 한쪽으로 쏠리거나 흔들릴 경우 아래 파라미터를 조정합니다.

| 변수명 | 현재 설정값 | 조절 가이드 |
| --- | --- | --- |
| **`kp`** | **3.0** | **보정 강도:** 왼쪽으로 더 휘면 절댓값을 키우고, 너무 지그재그로 가면 줄입니다. |
| **`ki`** | **0.0** | **누적 오차 보정:** 특정 방향으로 미세하게 계속 쏠리면 키우고, 주행이 불안정해지면 줄입니다. |
| **`kd`** | **0.1** | **진동 억제:** 보정 시 로봇이 좌우로 흔들리면 키우고, 반응이 너무 느려지면 줄입니다. |
| **`straight_angular_threshold`** | **0.05** | **직진 판정:** 조종 시 보정이 자꾸 풀리면 값을 키우고, 회전 시에도 보정이 걸리면 줄입니다. |
| **`odom_topic`** | **/odometry/filtered** | EKF를 통해 정제된 위치 정보를 수신합니다. |

---

## 주의사항

* **데이터 모니터링**: `ros2 topic echo /odometry/filtered --field pose.pose.orientation.z` 명령어로 각도가 0에서 변화하는지 꼭 확인하세요.
