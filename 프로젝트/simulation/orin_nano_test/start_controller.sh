#!/bin/bash
# source /opt/ros/humble/setup.bash (필요시 주석 해제)

echo ">>> [SYSTEM START] Robot Master Controller"
echo ">>> Waiting for ROS 2 system..."

# 통합 컨트롤러 실행 (시뮬레이션 모드)
python3 controller.py --ros-args -p use_sim_time:=true
