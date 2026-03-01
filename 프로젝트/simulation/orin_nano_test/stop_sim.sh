#!/bin/bash
echo ">>> ROS 2 시뮬레이션 및 컨트롤러 프로세스 종료 중..."

# 1. 시뮬레이터 및 ROS 코어 관련
pkill -f "ros2"
pkill -f "gzserver"
pkill -f "gzclient"
pkill -f "robot_state_publisher"
pkill -f "nav2"
pkill -f "rviz2"

# 2. 파이썬 노드 (컨트롤러, 디텍터, 팔로워)
pkill -f "python3 controller.py"
pkill -f "python3 detector_node.py"
pkill -f "python3 follower_node.py"

ros2 daemon stop

echo ">>> 모든 프로세스가 정리되었습니다."
