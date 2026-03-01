#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source ROS2 and workspace overlays if available
if [ -f "/opt/ros/humble/setup.bash" ]; then
  source "/opt/ros/humble/setup.bash"
fi

if [ -f "$HOME/ros2_ws/install/setup.bash" ]; then
  source "$HOME/ros2_ws/install/setup.bash"
fi

# Optional: customize these topics at runtime
CMD_TOPIC="/cmd_vel"
IMU_TOPIC="/imu/data"
ODOM_TOPIC="/odom"
SCAN_TOPIC="/scan"

# Start sensor/odom nodes in background
python3 "$BASE_DIR/6_imu_publisher.py" &
IMU_PID=$!

python3 "$BASE_DIR/5_odom_publisher.py" &
ODOM_PID=$!

ros2 launch ydlidar_ros2_driver ydlidar_launch.py &
LIDAR_PID=$!

python3 "$BASE_DIR/7_straight_drive_fusion.py" --ros-args \
  -p cmd_in_topic:=$CMD_TOPIC \
  -p imu_topic:=$IMU_TOPIC \
  -p odom_topic:=$ODOM_TOPIC \
  -p scan_topic:=$SCAN_TOPIC &
CTRL_PID=$!

cleanup() {
  echo "Stopping..."
  kill $CTRL_PID $LIDAR_PID $ODOM_PID $IMU_PID 2>/dev/null || true
}
trap cleanup EXIT INT TERM

# Teleop in foreground (interactive)
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r cmd_vel:=$CMD_TOPIC
