# Video Stream Troubleshooting (RegisterYoloView / FollowView)

## 1) Run detector with safer defaults

```bash
chmod +x /home/d201/S14P11D201/jetson/orin_nano_runtime/run_detector_monkey_perform.sh
/home/d201/S14P11D201/jetson/orin_nano_runtime/run_detector_monkey_perform.sh
```

Applied defaults:
- `start_active:=true`
- `image_topic:=/image_raw`
- `camera_fallback_topic:=/camera/image_raw`

## 2) Check ROS topic and web stream health

```bash
source /opt/ros/humble/setup.bash
source /home/d201/ros2_ws/install/setup.bash
chmod +x /home/d201/S14P11D201/jetson/orin_nano_runtime/check_video_pipeline.sh
/home/d201/S14P11D201/jetson/orin_nano_runtime/check_video_pipeline.sh <JETSON_IP> 8080
```

Example:

```bash
/home/d201/S14P11D201/jetson/orin_nano_runtime/check_video_pipeline.sh 192.168.0.45 8080
```

## 3) Minimal expected condition

- `/image_raw` or `/camera/image_raw` has a publisher.
- `/yolo_result` has a publisher.
- `http://<JETSON_IP>:8080/stream?topic=/yolo_result` returns HTTP headers.
- `/robot/mode` is published as `REGISTER` (frontend now keeps this alive automatically).
