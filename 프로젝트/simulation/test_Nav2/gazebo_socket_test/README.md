---

# ROS 2 Humble & Gazebo Nav2 자율주행 가이드

이 문서는 ROS 2 Humble 환경에서 TurtleBot3 시뮬레이션(Gazebo)과 Nav2 자율주행을 테스트하기 위한 실행 가이드입니다.

> **전제 조건:** WSL 환경설정, Gazebo, ROS 2, TurtleBot3 패키지가 이미 설치되어 있어야 합니다.

---

## 1. 환경 설정 (최초 1회 필수)

매번 터미널을 열 때마다 환경변수를 입력하는 번거로움과, Gazebo 모델 경로 에러를 방지하기 위해 `.bashrc`에 설정을 등록합니다.

### 1-1. 설정 파일 열기

```bash
nano ~/.bashrc

```

### 1-2. 파일 맨 아래에 다음 내용 추가

```bash
# ==========================================
# [ROS 2 & TurtleBot3 Settings]
# ==========================================
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID=30 # (팀원들과 겹치지 않게 숫자는 변경 가능)

# 1. 터틀봇 모델명 지정 (필수)
export TURTLEBOT3_MODEL=waffle_pi

# 2. Gazebo 모델 경로 픽스 (필수: 모델 튕김 방지)
export GAZEBO_MODEL_PATH=$GAZEBO_MODEL_PATH:/opt/ros/humble/share/turtlebot3_gazebo/models

# 3. 그래픽 가속 호환성 모드 (WSL 튕김 방지)
export LIBGL_ALWAYS_SOFTWARE=1

# 4. [청소 단축키] Gazebo 강제 종료 및 데몬 리셋 (명령어: kg)
alias kg='killall -9 gzserver gzclient && ros2 daemon stop && ros2 daemon start && echo "Gazebo & ROS Cleaned!"'

```

### 1-3. 적용 및 확인

```bash
source ~/.bashrc
printenv ROS_DISTRO
# 결과로 'humble'이 나오면 성공

```

---

## 2. 필수 라이브러리 설치 (최초 1회 필수)

프로젝트 실행에 필요한 Python 및 Node.js 라이브러리를 설치합니다.

### 2-1. Python 의존성 (제어 스크립트용)

ROS 2 제어 스크립트(`simple_navigator2.py`) 실행을 위해 필요합니다.

```bash
pip3 install websockets

```

### 2-2. Frontend 의존성 (Vue.js)

`roslib`의 최신 버전 호환성 이슈를 방지하기 위해 **1.1.0 버전**으로 고정하여 설치해야 합니다.

```bash
# Frontend 프로젝트 폴더로 이동 후 실행
npm uninstall roslib
npm install roslib@1.1.0

```

---

## 3. 빈 맵 생성 (최초 1회)

로봇이 자유롭게 주행할 수 있도록 장애물이 없는 (20m x 20m) 맵 파일을 생성합니다.

```bash
# 1. 거대한 흰색 지도(PGM) 생성
# 터미널에 복사 붙여넣기
python3 -c "
import os

# 홈 디렉토리 경로 가져오기 (/home/사용자명)
home_dir = os.path.expanduser('~')
pgm_path = os.path.join(home_dir, 'small_map.pgm')
yaml_path = os.path.join(home_dir, 'small_map.yaml')

# 1. PGM 파일 생성
width = 400
height = 400
header = f'P5\n{width} {height}\n255\n'.encode()
data = b'\xff' * (width * height)

with open(pgm_path, 'wb') as f:
    f.write(header + data)

# 2. YAML 파일 생성
yaml_content = f'''image: {pgm_path}
mode: trinary
resolution: 0.05
origin: [-10.0, -10.0, 0.0]
negate: 0
occupied_thresh: 0.65
free_thresh: 0.196
'''

with open(yaml_path, 'w') as f:
    f.write(yaml_content)

print(f'=== 맵 생성 완료 ===')
print(f'YAML 경로: {yaml_path}')
"
```

---

## 4. 실행 프로세스 (터미널 4개 필요)

자율주행 시뮬레이션을 위해서는 반드시 **4개의 터미널**이 순서대로 켜져 있어야 합니다.

### 재실행 전 주의사항

이전 실행 프로세스가 남아있으면 에러가 발생할 수도 있습니다. **청소 후 실행하세요.**

```bash
kg

# 또는

killall -9 gzserver gzclient rviz2 robot_state_publisher nav2_lifecycle_manager python3
ros2 daemon stop
ros2 daemon start
```

### [터미널 1] Gazebo 시뮬레이터 (빈 월드)

```bash
export TURTLEBOT3_MODEL=waffle_pi
ros2 launch turtlebot3_gazebo empty_world.launch.py x_pose:=1.0 y_pose:=0.0

```

### [터미널 2] Nav2 네비게이션 (빈 맵 적용)

Gazebo가 완전히 켜진 후 실행합니다.

```bash
ros2 launch turtlebot3_navigation2 navigation2.launch.py use_sim_time:=True autostart:=True map:=~/small_map.yaml

```

### [터미널 3] RViz 실행

```bash
GALLIUM_DRIVER=llvmpipe LIBGL_ALWAYS_SOFTWARE=1 ros2 run rviz2 rviz2 -d $(ros2 pkg prefix nav2_bringup)/share/nav2_bringup/rviz/nav2_default_view.rviz --ros-args -p use_sim_time:=true
```
### [터미널 4] Rosbridge 실행 (웹 통신용)

웹 프론트엔드와 ROS 간의 통신을 중계합니다.

```bash
ros2 launch rosbridge_server rosbridge_websocket_launch.xml

```

### [터미널 5] Python 제어 스크립트

```bash
python3 simple_navigator2.py

```
* 웹에서 상품 추적, 주차장 위치 선택 등으로 이동 명령을 내릴 수 있습니다.
