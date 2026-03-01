#!/bin/bash

# ROS 2 환경 설정 (필요시 주석 해제)
# source /opt/ros/humble/setup.bash

echo ">>> [START] Follower System Integration"

# 1. 인식 노드 (YOLO + ReID) 실행
echo ">>> Launching Detector Node..."
python3 detector_node.py &

# 2. 추종 노드 (PID + Nav2) 실행
echo ">>> Launching Follower Node..."
python3 follower_node.py &

echo ">>> All nodes are running in background."
echo ">>> Use 'pkill -f python3' to stop."

wait
