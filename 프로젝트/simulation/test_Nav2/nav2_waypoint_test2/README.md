# Nav2 Waypoint Test 2 (WSL2 Guide)

이 폴더는 DB 0.2 기반의 맵을 생성하고, 프론트엔드(Vue.js)에서 전송한 경로를 받아 Nav2로 자율주행하는 테스트 환경입니다.

---

## 1. 환경 준비 (Map Generation)

맵 파일(`pgm`, `yaml`, `world`)을 생성합니다. (Windows에서 생성해도 Linux에서 잘 읽히도록 수정됨)

```bash
cd test_Nav2/nav2_waypoint_test2
pip install -r requirements.txt
python3 generate_map.py
```
> **주의**: 맵을 다시 생성했다면 Gazebo를 재시작해야 변경 사항이 반영됩니다.

---

## 2. 시뮬레이션 실행 (Simplified)

복잡한 경로 설정 없이, 아래 명령어로 Gazebo, Nav2, 그리고 **Rosbridge(Vue 통신용)**를 한 번에 실행하세요.

### [Option A] Gazebo + Rosbridge 실행 (GUI 렉 최소화)
RViz를 끄고 물리 시뮬레이터와 웹소켓 브릿지만 가동합니다.

```bash
cd ~/PIL/test_Nav2/nav2_waypoint_test2
source /opt/ros/humble/setup.bash

# 전용 런치 파일 실행 (Rosbridge 자동으로 포함됨)
ros2 launch simulation_launch.py use_rviz:=False
```

### [Option B] Gazebo + RViz + Rosbridge 동시 실행
```bash
ros2 launch simulation_launch.py use_rviz:=True

---

## 3. 주행 노드 실행 및 테스트

### [Step 1] 주행 스크립트 실행
```bash
cd ~/PIL/test_Nav2/nav2_waypoint_test2
python3 waypoint_navigator.py
```

### [Step 2] 로봇 초기화 (필수)
Nav2 실행 후 반드시 초기 위치를 설정해야 합니다.

*   **web 이용**: web 접속하면 초기 위치 자동 지정
*   **RViz 이용**: 상단 `2D Pose Estimate` 클릭 후 로봇 위치 지정
*   **터미널 이용**:
    ```bash
    ros2 topic pub --once /robot/set_init_pose std_msgs/msg/String "data: '{x: -5.0, y: 5.0}'"
    ```

### [Step 3] 주행 명령 테스트
```bash
# 여러 지점을 경유하는 명령
ros2 topic pub --once /robot/destination std_msgs/msg/String "data: '{command: navigate_waypoints, waypoints: [{x: 2.0, y: 0.0, z: 0.0, w: 1.0}, {x: 2.0, y: 5.0, z: 0.7, w: 0.7}]}'"
```

## 4. 트러블슈팅
*   **빈 맵이 보일 때**: `simulation_launch.py`를 사용하면 절대 경로로 파일을 로드하므로 해결됩니다. 반드시 `generate_map.py`를 먼저 실행하여 파일이 존재하는지 확인하세요.
*   **로봇이 없을 경우**: `ros2 topic pub --once /robot/set_init_pose std_msgs/msg/String "data: '{x: -5.0, y: 0.0}'` 명령어로 로봇 특정 위치 소환하기.
*   **ModuleNotFoundError**: `generate_map.py` 실행 시 에러가 나면 `pip install -r requirements.txt`를 실행하세요. (Windows/WSL 환경 확인)
