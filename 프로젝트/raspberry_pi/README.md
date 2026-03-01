# Embedded System Integration Guide

이 디렉토리는 스마트 카트 프로젝트의 임베디드 제어 로직(Raspberry Pi & Jetson Orin Nano)을 포함하고 있습니다.

## 폴더 구조
- **`Raspberry_Pi/`**: RFID 상품 인식 및 오디오 피드백 담당
- **`jetson/orin_nano_runtime/`**: YOLO 기반 추종 주행 및 Nav2 자율 주행 통합 제어 담당

---

## 1. Raspberry Pi (RFID Server)
상품 인식을 위한 웹소켓 서버를 실행합니다.

### 실행 방법
```bash
cd ~/S14P11D201/raspberry_pi/rfid
python3 rfid_server.py
```
- **포트:** `8765` (WebSocket)
- **기능:** RFID 태그 스캔 시 상품 ID를 프론트엔드로 전송하고 `audio/beep.wav`를 재생합니다.

---

## 2. Jetson Orin Nano (Integrated Controller)
추종 주행(Follower)과 자율 주행(Nav2)을 하나의 컨트롤러에서 통합 관리합니다.
Jetson Orin Nano 디렉토리에서 진행합니다.
```bash
cd ~/S14P11D201/jetson/orin_nano_runtime
```
### 실행 방법 (시뮬레이션 / 가제보)

1. **권한 부여**
```bash
chmod +x start_sim.sh start_controller.sh stop_sim.sh
```

**혹시 줄바꿈 오류 나타나면**
```bash
sudo apt update && sudo apt install dos2unix -y
dos2unix *.sh
```
# 1. 맵 서버 설정(Configure) 상태로 변경
ros2 lifecycle set /map_server configure

# 2. 맵 서버 활성화(Activate) 상태로 변경
ros2 lifecycle set /map_server activate

2. **가제보 환경 실행 (터미널 1):**
```bash
./start_sim.sh
```

3. **통합 컨트롤러 실행 (터미널 2):**
```bash
./start_controller.sh
```

4. **종료 (터미널 3):**
```bash
./stop_sim.sh
```

### 실행 방법 (실제 로봇)
`start_controller.sh` 파일 내의 `use_sim_time:=true`를 `false`로 수정한 뒤 실행하세요.

---

## 주의 사항
1. **IP 설정:** 프론트엔드 앱은 브라우저 접속 주소의 IP를 자동으로 감지하여 웹소켓에 연결합니다.
2. **의존성:** Jetson Nano에서는 `torch`, `ultralytics`, `torchreid`, `insightface` 라이브러리가 설치되어 있어야 합니다.
3. **종료:** 백그라운드에서 실행 중인 노드들을 한 번에 종료하려면 `pkill -f python3` 명령어를 사용하세요.
