#!/bin/bash

ros2 daemon start

# 1. 환경 변수 설정
export TURTLEBOT3_MODEL=waffle_pi
export GAZEBO_MODEL_PATH=$GAZEBO_MODEL_PATH:/opt/ros/humble/share/turtlebot3_gazebo/models

# 현재 경로 확보
current_dir=$(pwd)

echo "--- 1. 시뮬레이션 통합 런치 실행 (Nav2 + Gazebo + Rosbridge) ---"
# 기존에 잘 되던 simulation_launch.py를 사용하여 안정적으로 실행
ros2 launch simulation_launch.py &

echo "--- Gazebo 및 로봇 로딩 대기 (15초)... ---"
sleep 15

echo "--- 2. 추종 타겟 (small_human) 소환 ---"
ros2 run gazebo_ros spawn_entity.py \
    -file ${current_dir}/models/small_human.sdf \
    -entity small_human \
    -x 1.4 -y 0.4 -z 0.0 &

echo "------------------------------------------------"
echo "시뮬레이션 준비 완료! 새로운 터미널에서 아래를 실행하세요."
echo "명령어: ./start_controller.sh"
echo "------------------------------------------------"

wait