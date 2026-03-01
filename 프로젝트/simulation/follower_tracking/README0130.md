# 사용자 추종 기능 구현

YOLO 기반의 객체 인식, ReID(객체 재식별), 그리고 LiDAR 데이터를 결합하여 사용자를 자동으로 추적하는 지능형 제어 시스템입니다.

##필수 주의사항: Python 라이브러리 버전 충돌

현재 ROS 2 Humble 및 주요 AI 라이브러리는 **NumPy 2.0 버전과 호환되지 않습니다.** 반드시 아래 순서대로 설치하여 버전을 고정해야 합니다.

### 1. 의존성 설치 (버전 고정)

```bash
cd ~/S14P11D201/simulation/follower_tracking
# 기존 NumPy 제거 및 황금 밸런스 버전 설치
pip uninstall numpy -y
pip install -r requirements.txt

# ReID 라이브러리 별도 설치
pip install git+https://github.com/KaiyangZhou/deep-person-reid.git

```
sudo apt update
sudo apt install ros-humble-nav2-dwb-controller

### 2. ROS 2 시스템 의존성 설치

```bash
sudo apt update
sudo apt install ros-humble-cv-bridge ros-humble-vision-msgs ros-humble-joint-state-publisher-gui ros-humble-robot-state-publisher -y

```

---

## 파일 구조 및 역할

* `start_sim.sh`: 가제보 월드 실행 및 사람 모델 소환 스크립트
* `requirements.txt`: NumPy 1.26.4 기반의 라이브러리 버전 명시
* `src/follower/follower/yolo_node.py`: **[시각]** 전체 객체 인식 및 주인 식별
* `src/follower/follower/follower_node.py`: **[제어]** LiDAR 기반 거리 유지 및 추종

---

## 프로젝트 실행 순서

### Step 1: 빌드 및 환경 로드

```bash
colcon build --symlink-install
source install/setup.bash

```

### Step 2: 시뮬레이션 및 노드 가동 (각각 새 터미널)

1. **환경 실행**: `./start_sim.sh`
2. **rviz2 실행**: `ros2 run rviz2 rviz2`
3. **rviz2에 맵 띄우기**: `ros2 launch nav2_bringup localization_launch.py map:=/home/minseo/S14P11D201/simulation/follower_tracking/minseo_map/my_map.yaml use_sim_time:=true` 
혹시나 여기서 map의 폴더path 잘되어있는지 확인하고 rviz2에 맵이 잘 들어왔으면
4. **nav2실행**: `ros2 launch nav2_bringup navigation_launch.py params_file:=/home/minseo/S14P11D201/simulation/follower_tracking/my_nav2_params.yaml use_sim_time:=true`
5. **yolo노드**: `ros2 run follower yolo_node --ros-args -p use_sim_time:=true`
6. **rviz2에서 2d 추정 화살표 만들기** 안만들면 nav2로 못감
7. **follower 노드**: `ros2 run follower follower_node --ros-args -p use_sim_time:=true`
8. **화면 모니터링**: `ros2 run rqt_image_view rqt_image_view` (토픽: `/yolo_result`)

만약 키보드로 제어하고싶으면 
**키보드제어** : `ros2 run teleop_twist_keyboard teleop_twist_keyboard`


---

## 긴급 조치 가이드

**1. "AttributeError: _ARRAY_API not found" 에러 발생 시**
NumPy가 2.0으로 자동 업데이트된 경우입니다. 아래 명령어로 즉시 복구하세요.
`pip install "numpy==1.26.4" "opencv-python<4.9" matplotlib --force-reinstall`

**2. "package 'joint_state_publisher' not found" 에러 발생 시**
`sudo apt install ros-humble-joint-state-publisher`를 실행하세요.

---
