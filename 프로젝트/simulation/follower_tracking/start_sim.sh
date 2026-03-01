#!/bin/bash

# 1. 환경 변수 및 모델 설정
export TURTLEBOT3_MODEL=waffle_pi
export GAZEBO_MODEL_PATH=$GAZEBO_MODEL_PATH:/opt/ros/humble/share/turtlebot3_gazebo/models

echo "--- 1. 가제보 시뮬레이션 실행 (waffle_pi) ---"
ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py &

echo "--- Gazebo 로드 대기 중 (12초)... ---"
sleep 12

echo "--- 2. 추종 타겟 (small_human) 소환 ---"
ros2 run gazebo_ros spawn_entity.py \
    -file ./small_human.sdf \
    -entity small_human \
    -x 0.0 -y -0.5 -z 0.0 &

sleep 3

echo "--- 3. 내장 지도로 Nav2 실행 (매핑 생략) ---"
# 이 명령어가 실행되면 보통 RViz2도 함께 뜹니다.
ros2 launch turtlebot3_navigation2 navigation2.launch.py use_sim_time:=True &

echo "------------------------------------------------"
echo "설정 완료! 아래 노드들을 각각의 터미널에서 실행하세요."
echo "------------------------------------------------"
echo "[모니터링용]"
echo "1. 카메라 확인: ros2 run rqt_image_view rqt_image_view"
echo "2. RViz 확인: ros2 run rviz2 rviz2 (이미 켜져 있다면 생략)"
echo "------------------------------------------------"
echo "[인식 및 주행용]"
echo "3. YOLO 인식: ros2 run follower yolo_node --ros-args -p use_sim_time:=true"
echo "4. 추종 제어: ros2 run follower nav_follower_node --ros-args -p use_sim_time:=true"
echo "------------------------------------------------"
echo "팁: RViz에서 '2D Pose Estimate'로 로봇 위치를 먼저 잡아주세요!"
echo "------------------------------------------------"

wait
