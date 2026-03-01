# Jetson

Jetson 장비에서 사용하는 코드 모음입니다.

## 하위 폴더
- `orin_nano_runtime/`: 실기 통합 실행 스택
- `jetson_vehicle_control/`: 하드웨어 테스트/제어 스크립트
- `ros2_ws/`: ROS2 패키지 워크스페이스

## 사용 흐름
1. `ros2_ws` 빌드
2. 필요 시 `jetson_vehicle_control`로 센서/모터 점검
3. `orin_nano_runtime`에서 통합 실행
