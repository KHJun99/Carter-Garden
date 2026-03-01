# Nav2 Waypoint Navigation Test Guide

이 문서는 TurtleBot3 Waffle Pi를 사용하여 Nav2 기반의 웨이포인트 주행을 시뮬레이션하는 방법을 안내합니다. 커스텀 맵과 월드를 사용하여 정확한 주행 테스트를 수행할 수 있습니다.

## 1. 사전 준비 (Prerequisites)

먼저 터미널에서 프로젝트 루트 디렉토리(`nav2_waypoint_test`)로 이동합니다.

```bash
# 예시 경로 (본인의 환경에 맞게 이동하세요)
cd ~/server/test_ksy/nav2_waypoint_test
```

### 1.1 맵 파일 생성
다음 스크립트를 실행하여 `test_map.yaml`과 `test_map.pgm`을 현재 폴더에 생성합니다.
(이미지 좌표와 Nav2 좌표 동기화를 위해 상하 반전 및 마진 처리가 포함되어 있습니다.)

```bash
python3 generate_test_map.py
```

### 1.2 Gazebo 월드 파일 준비
`my_test_world.world` 파일이 필요합니다. 없다면 다음 절차로 생성하세요.
1. `ros2 launch gazebo_ros gazebo.launch.py` 실행.
2. 상단 툴바의 **Box** 도구를 사용하여 장애물 배치 (좌표 참고: `graph_data.py`).
3. `File` -> `Save World As...` -> 현재 폴더에 `my_test_world.world`로 저장.

---

## 2. 시뮬레이션 실행 (Execution Steps)

총 3개의 터미널이 필요합니다. 각 터미널에 아래 명령어를 순서대로 입력하세요.
**모든 터미널은 프로젝트 루트(`nav2_waypoint_test`)에서 실행한다고 가정합니다.**

### [Terminal 1] Gazebo & Nav2 실행 (Main System)
시뮬레이터(Gazebo), RViz, Nav2 스택을 모두 실행합니다.

```bash
# 1. 환경 변수 설정
source /opt/ros/humble/setup.bash
export TURTLEBOT3_MODEL=waffle_pi

# 2. 현재 폴더의 맵과 월드 파일 경로 지정
export CART_MAP=$(pwd)/test_map.yaml
export MY_WORLD=$(pwd)/my_test_world.world

# 3. 통합 런치 실행 (한 줄로 복사)
ros2 launch nav2_bringup tb3_simulation_launch.py map:=$CART_MAP world:=$MY_WORLD x_pose:=0.0 y_pose:=0.0 headless:=False use_sim_time:=True
```
> **참고**: `x_pose`, `y_pose`는 `0.0`으로 설정합니다. (맵 생성 시 -2.0m 마진을 주었으므로 0,0이 안전한 시작점입니다.)

### [Terminal 2] 로봇 스폰 (Spawn Robot)
Gazebo 상에 로봇 모델을 소환합니다. (Terminal 1에서 로봇이 안 보일 경우 수행)

```bash
source /opt/ros/humble/setup.bash

# Waffle Pi 스폰 명령어 (한 줄로 복사)
ros2 run gazebo_ros spawn_entity.py -file /opt/ros/humble/share/turtlebot3_gazebo/models/turtlebot3_waffle_pi/model.sdf -entity turtlebot3_waffle_pi -x 0.0 -y 0.0 -z 0.01
```

### [Terminal 3] 제어 코드 실행 (Controller)
파이썬 스크립트를 실행하여 로봇에게 웨이포인트 주행 명령을 내립니다.

```bash
source /opt/ros/humble/setup.bash
# 프로젝트 폴더로 이동 필수
# cd ~/server/test_ksy/nav2_waypoint_test

python3 simple_waypoint.py
```

**사용 명령어:**
- `init P0`: 로봇 초기 위치 설정 (필수).
- `go P6`: P6 노드로 주행 시작.
- `stop`: 주행 정지.
- `resume`: 주행 재개 (AMCL 기반 위치 재계산).

---

## 3. 트러블슈팅 (Troubleshooting)

**Q. Gazebo 창이 안 뜹니다.**
A. Terminal 1 실행 시 `headless:=False` 옵션이 있는지 확인하세요. 그래도 안 뜨면 새 터미널에서 `gzclient`를 입력하세요.

**Q. RViz에서 맵이 이상하게(치우쳐서) 보입니다.**
A. `test_map.yaml`의 `origin` 값이 `[-2.0, -2.0, 0.0]`으로 설정되어 있는지 확인하세요.

**Q. 로봇이 제자리에서 빙빙 돌거나 좌표가 튑니다.**
A. Gazebo의 물리적 벽(박스)과 Nav2 맵의 장애물 위치가 일치하지 않아서입니다. `my_test_world.world`에 박스를 정확히 배치했는지 확인하세요.

**Q. 'file not found' 에러 발생.**
A. 명령어 내의 파일 경로(`$CART_MAP`, `$MY_WORLD`)가 실제 파일 위치와 일치하는지 `ls` 명령어로 확인하세요. `$(pwd)`는 현재 디렉토리를 의미하므로, 반드시 프로젝트 폴더에서 명령어를 실행해야 합니다.
