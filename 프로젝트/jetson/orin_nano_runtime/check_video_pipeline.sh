#!/usr/bin/env bash
set -euo pipefail

JETSON_IP="${1:-127.0.0.1}"
VIDEO_PORT="${2:-8080}"

echo "[1/5] ROS topics summary"
ros2 topic list | grep -E "image_raw|camera/image_raw|yolo_result|robot/mode|robot/status" || true
echo

echo "[2/5] Input topic stats"
if ros2 topic info /image_raw >/dev/null 2>&1; then
  echo "- /image_raw"
  ros2 topic info /image_raw
fi
if ros2 topic info /camera/image_raw >/dev/null 2>&1; then
  echo "- /camera/image_raw"
  ros2 topic info /camera/image_raw
fi
echo

echo "[3/5] Output topic stats"
if ros2 topic info /yolo_result >/dev/null 2>&1; then
  ros2 topic info /yolo_result
else
  echo "/yolo_result topic not found"
fi
echo

echo "[4/5] Quick bandwidth check (5 seconds each)"
timeout 6 ros2 topic hz /yolo_result || true
timeout 6 ros2 topic hz /image_raw || true
timeout 6 ros2 topic hz /camera/image_raw || true
echo

echo "[5/5] web_video_server HTTP check"
URL="http://${JETSON_IP}:${VIDEO_PORT}/stream?topic=/yolo_result"
echo "URL: ${URL}"
if command -v curl >/dev/null 2>&1; then
  curl -I --max-time 3 "${URL}" || true
else
  echo "curl is not installed; skip HTTP header check"
fi

echo
echo "Done. If /yolo_result has no publisher/subscriber, verify detector node and mode (/robot/mode=REGISTER)."
