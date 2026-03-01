# Frontend (Kiosk UI)

스마트 카트 키오스크 프론트엔드(Vue) 문서입니다.

## 폴더 구조
```text
raspberry_pi/frontend/
├── .env
├── package.json
├── vite.config.js
├── index.html
└── src/
    ├── api/                        # 백엔드/ROS 통신 모듈
    ├── assets/                     # 이미지/아이콘
    ├── components/                 # UI 컴포넌트
    ├── router/                     # 라우팅
    ├── store/                      # Pinia 상태
    └── views/                      # 화면 단위 컴포넌트
```

## 사전 시스템 설정 (최초 1회)
```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
sudo apt update
sudo apt install chromium-browser fontconfig -y
```

## 프론트엔드 실행
```bash
cd ~/S14P11D201/raspberry_pi/frontend
npm install
npm install vuetify @mdi/font
npm install socket.io-client
npm install roslib@1.1.0
npm install hangul-js
nohup npm run dev > vue.log 2>&1 &
```

## 키오스크 화면 실행
```bash
export DISPLAY=:0 && chromium --kiosk --password-store=basic http://localhost:5173
```

## 문제 발생 시
1. Wayland 대신 X11 사용 (`sudo raspi-config`)
2. HDMI 0번 포트 연결
3. 해상도 1080p 고정


## 실행 범위
- 이 문서는 **프론트엔드(UI)** 실행만 다룹니다.
- Jetson 런타임/ROS2 실행은 아래 문서를 사용하세요.
  - `jetson/orin_nano_runtime/README.md`
  - `jetson/ros2_ws/README.md`

## 연동 전 체크
1. 백엔드가 먼저 실행 중인지 확인 (`server/backend`)
2. 프론트 `.env`의 API/ROS 주소가 현재 장비 IP와 맞는지 확인
## 종료
```bash
pkill -f node
pkill -f chromium
```

