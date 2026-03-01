#!/usr/bin/env bash
set -euo pipefail

# Docker container example:
# source /opt/ros/humble/setup.bash
# source /workspace/jetson/ros2_ws/install/setup.bash
# ./run_detector_monkey_perform.sh

source /opt/ros/humble/setup.bash
source /workspace/jetson/ros2_ws/install/setup.bash

python3 /workspace/jetson/jetson/orin_nano_runtime/detector_monkey_perform_node.py \
  --ros-args \
  -p imgsz:=320 \
  -p frame_skip:=2 \
  -p conf_thres:=0.4 \
  -p start_active:=true \
  -p image_topic:=/image_raw \
  -p camera_fallback_topic:=/camera/image_raw
