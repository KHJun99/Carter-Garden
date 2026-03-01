# 2026-01-12
## 📅 TIL : AIoT 프로젝트 아이디어 기획 회의

## 1. 회의 목적
* 2학기 프로젝트 주제 선정 및 실현 가능성 검토 (수상 목표)

## 2. 아이디어 피드백 요약

### ✅ 긍정 검토 (Develop)
* **스마트 쇼핑 카트**
    * **평가:** 현재 하드웨어(오린카)로는 구현 난이도 높음.
    * **보완:** RFID/전자석 활용 및 소형화하여 SW(군집주행 등) 비중을 높이는 방향으로 수정 필요.

### ❌ 반려 및 보류
* **무인 매장 관리:** 차별성 부족, 아이디어 약함.
* **자세 교정 로봇:** 오린카의 회전 반경/기동성 문제로 부적합.
* **게이밍 화분:** 기획 의도 불분명, 시연 및 게임 개발 난이도 높음.
* **타자 교정:** 기술적 메리트 없음.

# 2026-01-13
# 🛒 TIL: 자율주행 스마트 카트 (Smart Cart PoC)

> **한 줄 요약:** 3×3m 축소 마트 환경에서 **자율주행(SLAM)**으로 진열대를 찾아가고, **RFID**로 상품을 인식하며, 결제 후 **자동 주차/반납**까지 수행하는 미래형 카트 프로젝트.

---

## 1. 🏗️ 시스템 아키텍처 (System Architecture)

### 하드웨어 (HW)
* **Brain:** 🧠 `Raspberry Pi 5` (메인 연산, ROS2, 웹 서버)
* **Actuator:** ⚙️ `Arduino` (모터 제어, Pi와 UART 통신)
* **Sensors:**
    * 👁️ **LiDAR:** SLAM 및 장애물 회피 (RPLidar)
    * 📷 **Camera:** 사용자 추적 (Follow Mode)
    * 🏷️ **RFID:** 장바구니 상품 인식 (RC522)

### 소프트웨어 (SW)
* **OS/Middleware:** Ubuntu 22.04 / ROS 2 Humble (또는 ROS 1 Noetic)
* **Web:** Flask + WebSocket (실시간 맵/장바구니 연동)
* **Algorithms:** Hector SLAM, Navigation2 (DWA), OpenCV (마커 추적)

---

## 2. 🔄 핵심 시나리오 (Workflow)
- 전체 구조는 **LiDAR+SLAM+Navigation+카메라 추적+RFID 장바구니+주차 위치 안내**로 구성된 소형 자율주행 카트 시스템
- **디스플레이는 WiFi 기반 무선 연결**, 결제 후에는 **자동 반납 / 주차 위치 안내** 두 가지 플로우를 제공해 사용자 경험을 완성.
- RFID는 예산 상 **RC522 전제를 두고**, 한 번에 한 개씩 넣도록 하드웨어 가이드와 UI로 보완.
- 주차 구역은 **알파벳+숫자 코드(G1, F3)**로 정의해 향후 실제 마트로 확장하기 좋은 구조.

# 2026-01-14
# 📝 [TIL] UWB 기반 실내 측위와 자율주행 스마트 카트 프로젝트 구상

## 1. 기술 연구: UWB를 활용한 정밀 위치 추적

### 🎯 핵심 기술
오늘의 핵심 기술 주제는 **UWB(Ultra-Wideband, 초광대역) 통신**이다. 애플의 에어태그(AirTag)처럼 **cm 단위의 정밀한 위치 추적**이 가능한 기술이다.

### 🛠 구현 방법 (H/W)
* **알고리즘:** 실내 위치 측위를 위해 **삼각측량(Triangulation)** 기법을 사용한다.
* **하드웨어 조합:** * 
  * **DWM1000 (UWB 모듈)** + **ESP32 (MCU)**
  * 이 조합이 가장 접근성이 좋고 개발 속도도 빠르다.

### 💰 이슈 (Cost)
* UWB 모듈 중에서는 저렴한 편에 속하는 DWM1000을 사용하더라도, 다수의 **앵커(Anchor)**와 **태그(Tag)**를 구성해야 하므로 전체적인 시스템 비용이 꽤 비싼 편이다.
* **비용 대비 효율을 극대화하는 설계**가 필요하다.

---

## 2. 서비스 기획: 새로운 쇼핑 경험(UX)을 위한 스마트 카트

### 💡 목표
단순히 기술을 구현하는 것을 넘어, **"매장 입장부터 물건 구매, 결제, 그리고 퇴장까지"** 끊김 없는(Seamless) 새로운 사용자 경험을 제공하는 것이 목표다.

### 🛒 핵심 시나리오 (User Journey)

1. **입장 및 쇼핑 시작**
   - 사용자가 매장에 들어서서 카트를 사용한다.

2. **자율주행 네비게이션**
   - 사용자가 구매할 물건 목록을 입력한다.
   - 카트는 해당 물건이 있는 위치 근처까지 **자율주행**으로 이동한다.

3. **상품 찾기 (Pick-to-Light)**
   - 카트가 매대에 도착하면, 해당 상품이 위치한 매대 칸의 **LED 불빛이 자동으로 켜져** 사용자가 직관적으로 물건을 찾을 수 있게 돕는다.

4. **자동 장바구니 등록 (RFID)**
   - 물건을 집어 카트에 담는 순간, 카트에 내장된 **RFID 리더**가 태그를 인식하여 장바구니 목록(결제 목록)에 자동으로 추가한다.

5. **즉시 결제**
   - 계산대 줄을 설 필요 없이, 카트에 부착된 단말기에 카드를 꽂으면 그 자리에서 **자동 결제**가 완료된다.

6. **퇴장 및 반납**
   - 빈 카트는 다시 **자율주행으로 카트 보관소(충전소)로 복귀**한다.

# 2026-01-15
# 📝 TIL: UWB 추종 로봇 연구 & ROS 2 자율주행 실습

**📅 날짜:** 2026. 01. 15
**🏷️ 태그:** #ROS2 #Humble #Nav2 #Gazebo #UWB #YOLO #Flask #Project

## 1. UWB 하드웨어 및 시스템 설계 (연구 단계)

### Q. SmartTag2 3개로 실내 GPS를 구현할 수 있는가?
* **배운 점:** 이론적으로 삼변측량 원리를 통해 가능하지만, 현실적인 제약이 있음.
    * **제약:** Samsung SmartThings API가 비공개라 개발자가 Raw Data(거리, 각도)를 직접 뽑아 쓰기 매우 어려움.
* **대안 (Standard):** **ESP32 + DWM3000** 모듈 사용.
    * **DWM1000:** 거리(Distance)만 측정 가능. 위치를 특정하려면 앵커 3개 이상 필요.
    * **DWM3000:** 안테나 2개로 위상차(PDoA)를 계산하여 **거리 + 방위각(AoA)** 측정 가능. (앵커 1개로도 추종 로봇 구현 가능).

### Q. 로봇은 키(Tag)를 어떻게 따라가는가? (좌표 변환)
* **배운 점:** UWB 센서는 **"로봇 기준의 상대 위치"**(예: 내 앞 2m, 오른쪽 30도)를 제공함.
* **핵심 로직:** 로봇이 자율주행(Nav2)을 하려면 이를 **"지도(Map) 기준의 절대 좌표"**로 변환해야 함.
> $$Target\_X = Robot\_X + (Distance \times \cos(Robot\_Theta + AoA))$$

---

## 2. Flask (Python 웹 서버)

### Q. 실행할 때마다 환경변수(`set FLASK_APP...`) 설정이 번거로움.
* **배운 점:** 파일명이 `app.py`가 아니더라도 강제로 실행하는 간편한 방법이 존재함.
    1. **CLI 옵션 사용 (추천 ⭐):** ```bash
       flask --app <파일이름> run
       ```
    2. **Python 실행:** 코드 하단에 `if __name__ == '__main__': app.run()` 추가 후 `python <파일이름>.py` 실행.

---

## 3. ROS 2 시뮬레이션 & SLAM (지도 그리기)

### Q. 하드웨어는 LiDAR인데 왜 RViz에서는 `LaserScan`인가?
* **배운 점:** 2D LiDAR 센서가 전송하는 데이터의 ROS 표준 메시지 타입 이름이 **`LaserScan`**임.
* **필수 체크:** RViz에서 정상적으로 데이터를 확인하려면:
    * **Fixed Frame** 설정 확인 (`map` 또는 `odom`).
    * **TF (좌표 변환)** 토픽 추가.
    * **LaserScan** 토픽(`/scan`) 추가.

### Q. 지도 저장 명령어 (`mkdir` 포함)
* **배운 점:** 저장할 폴더를 먼저 생성하고(`-p` 옵션), `map_saver` 노드를 실행해야 함.
    ```bash
    # 폴더 생성
    mkdir -p ~/articubot_ws/src/articubot_one/maps
    
    # 맵 저장 실행
    ros2 run nav2_map_server map_saver_cli -f my_map
    ```

---

## 4. ROS 2 Nav2 (자율주행)

### Q. `apt install` 시 `Could not get lock` 에러 발생
* **원인:** 리눅스 패키지 매니저는 중복 실행이 불가능함. 백그라운드에서 업데이트가 돌고 있거나 비정상 종료된 경우 발생.
* **해결:**
    ```bash
    sudo kill -9 <PID>             # 범인 프로세스 종료
    sudo rm /var/lib/dpkg/lock* # 잠금 파일 삭제
    sudo dpkg --configure -a       # 패키지 설정 복구
    ```

### Q. Nav2 실행 시 `Activating...` 로그가 계속 뜸
* **배운 점:** 에러가 아님. Nav2의 생명주기(Lifecycle) 노드들이 순차적으로 깨어나 **준비 완료(Active)** 상태가 되는 정상적인 과정임.

### Q. 자율주행 시키는 순서 (RViz 조작)
1.  **2D Pose Estimate:** "로봇, 너 지금 지도상 여기(실제 위치)에 있어." (초기 위치 추정)
2.  **Nav2 Goal:** "로봇, 저기(목표 지점)로 이동해." (경로 생성 및 주행 시작)

---

## 5. 🚀 프로젝트 방향 전환 (Pivot)

### 결정 사항
* **UWB 하드웨어 구현의 복잡성 및 SmartTag2 연동 불가 문제로 인해 추종 방식을 변경함.**
* **변경 전:** UWB (DWM3000) 기반 태그 추적.
* **변경 후:** **YOLO (Vision AI) 기반 사람 인식 및 추종.**

### 변경 후 로직 (Plan)
1.  **Sensor:** 카메라 (Webcam or CSI Camera).
2.  **Processing:** Jetson Orin Nano (GPU)에서 `YOLOv8` 구동.
3.  **Algorithm:** * `Person` 객체 감지.
    * Bounding Box의 중심점($x$) 좌표로 **조향(회전)** 결정.
    * Bounding Box의 크기(또는 Depth 센서)로 **거리(전진/후진)** 결정.

# 2026-01-16
## 🎨 Design & Data
### 웹 디자인 및 데이터 수집
* **Figma 활용 웹 디자인:** 프로젝트 웹 프론트엔드 UI/UX 초안 디자인 작업 진행.
* **데이터셋 구축:** 상품 목록 페이지에 활용할 상품 이미지 데이터 수집 및 정리.

## 🛠 Tech Stack & Environment
### 개발 환경 설정 및 아키텍처 학습
* **기술 스택 설치:**
    * **Frontend:** Vue.js
    * **Backend:** Flask
    * **Database:** MySQL
* **데이터 흐름(Data Flow) 및 연동 구조 학습:**
    * Vue(Client) ↔ Flask(Server) 간의 API 통신 구조 이해.
    * Flask ↔ MySQL 간의 데이터베이스 연결(Connection) 및 쿼리 동작 원리 파악.
    * 전체적인 웹 어플리케이션의 데이터 동작 방식(Request/Response cycle) 정리.

## 📝 Retrospective
* 프론트엔드부터 백엔드, DB까지 이어지는 전체적인 데이터 흐름을 이해하는 데 집중함.
* 수집한 이미지 데이터를 실제 DB에 어떻게 적재하고 불러올지 구상 필요.


# 2026.01.19 (월) TIL - 스마트 카트 아키텍처 및 CI/CD 구축



## 1. 오늘 진행한 내용 (What I Did)



### **스마트 카트 프로젝트 아키텍처 설계**

* **하드웨어 구성 정의**:

    * **Jetson Orin Nano**: YOLO 객체 인식, SLAM, ROS 2 기반 자율주행 등 고성능 연산 담당.

    * **Raspberry Pi**: 사용자 UI(Vue.js) 구동 및 터치스크린 입력 처리.

* **통신 프로토콜 결정**:

    * 영상 스트리밍: HTTP 기반 MJPEG 스트리밍 방식 채택.

    * 제어 명령: 실시간성이 중요한 로봇 제어 신호는 WebSocket 사용.



### **CI/CD 파이프라인 구축 및 트러블슈팅**

* **Jenkins 설정**: EC2 서버에 Jenkins 설치 및 플러그인 의존성 버전 문제 해결 (v2.528.3 → v2.546).

* **배포 환경 구성**: GitLab CI/CD 연동 및 EC2 배포를 위한 SSH/Git 권한 설정 완료.

* **백엔드**: Flask 서버 배포 준비 및 간단한 AI 상품 추천 기능 구현 논의.



---



## 2. 오늘 배운 내용 (What I Learned)



### **시스템 설계 (System Design)**

* **역할 분리 (Separation of Concerns)**:

    * 엣지 디바이스 간의 부하를 효율적으로 분산하기 위해 무거운 AI/Vision 처리는 Jetson이, 가벼운 웹 뷰 및 사용자 인터랙션은 라즈베리파이가 전담하도록 설계함.

* **프로토콜 최적화**:

    * 단순 영상 송출에는 오버헤드가 적은 HTTP 스트리밍이 유리하고, 양방향 소통과 즉각적인 반응이 필요한 주행 제어에는 WebSocket이 필수적임을 이해함.



### **DevOps & Troubleshooting**

* **Jenkins 버전 호환성**:

    * Jenkins 코어 버전과 플러그인 버전이 맞지 않을 때 발생하는 오류를 경험하고, 이를 해결하기 위해 최신 버전(2.546)으로 업데이트하거나 호환되는 플러그인 버전을 찾는 과정을 학습함.

* **배포 보안**:

    * CI/CD 도구가 원격 서버(EC2)에 접근할 때 필요한 SSH 키 관리와 Git 권한 설정의 중요성을 확인함.



---
# TIL: Server Troubleshooting & Jetson AI Design (2026-01-20)

## 1. Backend & DevOps (AWS EC2, Nginx, Flask)

### 🛑 502 Bad Gateway 해결 과정
* **상황:** Nginx 서버는 켜져 있으나, Flask 백엔드와 연결되지 않음 (`Connection refused`).
* **원인 1 (프로세스):** SSH 세션이 끊기면서 포그라운드에서 실행 중이던 Flask 서버가 같이 종료됨.
* **원인 2 (의존성):** 서버를 다시 켜려 했으나 `ModuleNotFoundError: No module named 'flask_migrate'` 발생.
    * 코드(`extensions.py`)에서는 import 하고 있었으나, `requirements.txt`에 누락되어 설치되지 않음.
* **해결:**
    1.  `requirements.txt`에 `Flask-Migrate` 추가.
    2.  `pip install -r requirements.txt` 재실행.
    3.  `nohup`을 이용해 백그라운드 실행.

### ⚠️ CI/CD 파이프라인의 함정 ("Fake Passed")
* **문제:** GitLab CI 파이프라인은 'Passed(성공)'라고 떴지만, 실제 서버는 죽어있었음.
* **이유:**
    * `nohup ... &` 명령어는 실행 요청만 하고 즉시 종료 코드 0(성공)을 반환하므로, GitLab Runner는 성공으로 판단함.
    * 실제로는 실행 직후 에러를 뱉고 프로세스가 죽어버림.
    * `ubuntu` 계정과 `gitlab-runner` 계정 간의 **폴더 권한 문제**로 `venv`에 패키지가 제대로 설치되지 않았음.
* **해결책 (Key Takeaway):**
    * `nohup` 실행 시 **가상환경의 절대 경로**를 명시하여 시스템 Python과의 혼동 방지.
        ```bash
        nohup ./venv/bin/python run.py > flask.log 2>&1 &
        ```
    * 서버 로그(`flask.log`) 확인의 생활화.

---

## 2. Robotics & AI (Jetson Orin Nano)

### 🤖 Person Following (사람 추종) 로직 설계
* **센서 퓨전 (Sensor Fusion):**
    * **Camera (YOLO):** 사람의 **방향(각도)**을 찾음.
    * **LiDAR:** 카메라가 알려준 각도(ROI)의 **거리 데이터**만 필터링해서 추출.
    * *이점:* 라이다의 정확한 거리 측정 + 카메라의 객체 식별 능력을 결합.
* **제어 알고리즘:**
    * 단순 좌표 이동이 아닌 **거리 유지(Distance Maintenance)** 방식 사용.
    * 목표 거리(예: 1.2m)를 설정하고 PID 제어를 통해 속도 조절.

### 🧠 Edge AI 모델 선정 및 아키텍처
* **엣지 vs 서버:**
    * 제어용 데이터는 **Jetson 내부(Edge)**에서 처리해야 함. 서버 오프로딩 시 **Latency(지연)**와 데이터 비동기화 문제로 로봇 제어가 불안정해짐.
* **YOLO 모델 선정:**
    * **Pick:** `YOLOv11s-pose` (Small + Pose Estimation)
    * **이유:**
        1.  `Nano`는 너무 가볍고 `Medium`은 Orin Nano에 무거움. `Small`이 최적의 타협점.
        2.  `Pose` 모델은 관절(Keypoints)을 찾으므로, 팔을 흔들어도 **몸통 중심(골반 등)**을 안정적으로 추적 가능하며, 발 위치를 통해 지면 거리 추정에 유리함.
* **최적화 필수:** PyTorch 모델을 그대로 쓰지 말고 **TensorRT (FP16)**로 변환하여 FPS 확보 필요.

---

## 3. Action Items
- [ ] 로컬 개발 환경 `requirements.txt`에 `Flask-Migrate` 추가 후 Git Push 하기.
- [ ] Jetson Orin에서 `YOLOv11s-pose` 모델 TensorRT 변환 테스트.
- [ ] 로봇 주행 시 서버 통신(영상 전송)은 모니터링 용도로만 제한적으로 사용하기.

# 📝 TIL - 2026.01.21 (수)

## 🚀 Project: Smart Cart (Jetson Orin Nano & Raspberry Pi)

### 1. Jetson Orin Nano 네트워크 환경 구축
* **SSH 접속 (개발용):**
    * 노트북 ↔ 공유기(Wi-Fi) ↔ Jetson Orin 연결.
    * VS Code Remote-SSH를 사용하여 `192.168.137.x` (Wi-Fi IP) 대역으로 접속.
    * **문제 해결:** `HostName`과 `User` 설정 오류 수정 (`ssh` 명령어 중복 입력 문제 해결).

* **Dual Network 구성 (통신 최적화):**
    * **목표:** 영상 데이터 전송의 안정성을 위해 개발은 Wi-Fi로, 기기 간 통신은 유선 LAN으로 분리.
    * **설정:**
        * Jetson (Server): `192.168.50.10` (eth0)
        * Raspberry Pi (Client): `192.168.50.20` (eth0)
    * **Troubleshooting:**
        * Jetson의 유선 랜카드 이름이 `eth0`가 아닌 `enP8p1s0`임을 확인하고 `nmcli`로 고정 IP 재설정 완료.
        * 게이트웨이 설정을 비워둠으로써 인터넷 트래픽은 Wi-Fi(`wlan0`)로 유지.

### 2. ROS 2 기반 영상 스트리밍 시스템 구축
* **시스템 구조:**
    * `usb_cam` (영상 취득) → `yolo_node` (객체 인식 & 가공) → `web_video_server` (HTTP 송출) → Vue.js (화면 표시).
* **ROS 2 패키지 및 노드 실행:**
    1. **Camera:** `ros2 run usb_cam usb_cam_node_exe ...` (/image_raw 발행)
    2. **Web Server:** `ros2 run web_video_server web_video_server` (포트 8080)
    3. **Bridge:** `ros2 launch rosbridge_server ...` (포트 9090, Vue 명령 수신)
* **Vue.js 연동 (`FollowView.vue`):**
    * 유선 LAN IP(`192.168.50.10`)를 통해 MJPEG 스트림 수신.
    * ROSBridge를 통해 `FOLLOW` / `STOP` 명령 전송 구현.

### 3. 트러블슈팅 (Bug Fix)
* **Backend (`requirements.txt`):**
    * `marshmallow-sqlalchemyFlask-Migrate` 처럼 패키지명이 붙어버린 오타 수정.
* **Frontend (Raspberry Pi Kiosk):**
    * **문제:** 터치스크린에서 버튼 클릭이 잘 안되는 현상.
    * **해결:** * `@click` 대신 `@pointerup` 이벤트 사용.
        * `:ripple="false"`로 성능 부하 방지.
        * CSS `z-index` 및 `transform: translateZ(0)` 적용으로 GPU 레이어 강제 분리.
* **YOLO Node 개발:**
    * 기존 파이썬 코드를 ROS 2 노드로 포팅 (`yolo_node.py`).
    * 하드웨어(모터/서보) 제어 부분은 주석 처리하고, 영상 처리(Detection & Bounding Box) 우선 구현.

### 4. 내일 할 일 (To-Do)
* [ ] Jetson Orin Nano PyTorch CUDA 활성화 확인.
* [ ] YOLO 노드 최적화 및 실제 사람 인식 테스트.
* [ ] (추후) 모터/서보 제어 주석 해제 및 하드웨어 연동.

# 📅 [TIL] Jetson Orin Nano 자율주행 로봇 환경 구축 로그

**Date:** 2026. 01. 22 (Thu)  
**Tags:** #SSAFY #JetsonOrinNano #Docker #ROS2 #PyTorch #Embedded #Troubleshooting

---

## 1. 🎯 오늘의 목표
SSAFY 2학기 자율주행 프로젝트 진행을 위해 **Jetson Orin Nano** 보드에 완벽한 개발 환경을 구축한다.
- **Docker 기반**의 격리된 환경 구성
- **PyTorch (GPU 가속)**, **ROS 2 Humble**, **YDLidar** 센서가 하나의 컨테이너에서 유기적으로 작동하도록 통합

---

## 2. ✅ 완료한 작업 (Achievements)

### 🏗️ Docker 환경 구축 완료
- **이미지 생성**: 수많은 시행착오 끝에 `minseo_robot_success`라는 최종 안정화 이미지를 생성하고 `commit`으로 영구 저장함.
- **컨테이너 실행**: `--runtime nvidia`, `--network host`, `-v` (볼륨 마운트) 옵션을 적절히 조합하여 하드웨어 가속과 주변기기 제어가 가능한 실행 커맨드 확립.

### 🔌 하드웨어 연동 해결
- **Lidar 센서 인식**: `/dev/ttyUSB0` 장치에 대한 권한 문제(`Permission denied`)를 해결하고, 도커 내부에서 `crwxrwxrwx` 권한으로 정상 접근 확인.

### 🧠 AI Core 설치 (Jetson 맞춤형)
- **PyTorch 2.8.0 + Torchvision 0.23.0** 설치 완료.
- **CUDA 12.6** 가속 활성화 확인 (`torch.cuda.is_available() -> True`).
- 일반 PC용 패키지가 아닌 **JetPack 6.2 호환 빌드**를 사용하여 아키텍처 호환성 확보.

---

## 3. 🔥 트러블슈팅 (Troubleshooting Log)

오늘 개발 중 마주친 치명적인 에러들과 해결 과정을 기록한다.

### 🔴 Issue 1: PyTorch 설치 후 라이브러리 로드 실패
- **증상**: `import torch` 실행 시 `OSError: libcublas.so.11 not found` 발생.
- **원인**: `pip install torch`로 설치하면 x86 아키텍처 기반의 패키지가 설치되어, ARM64 기반인 Jetson의 라이브러리 구조와 맞지 않음.
- **해결**: 기존 패키지를 삭제하고, NVIDIA 개발자(davidl-nv)가 배포하는 **Jetson 전용 Wheel 파일**을 다운로드하여 수동 설치함.

### 🔴 Issue 2: 내부 라이브러리 경로 인식 불가
- **증상**: 설치는 됐으나 `ImportError: libgloo.so.0` 에러 발생.
- **원인**: Jetson용 PyTorch는 시스템 표준 경로(`/usr/lib`)가 아닌 패키지 내부(`/usr/local/.../torch/lib`)에 의존성 파일을 둠. 시스템이 이 경로를 인지하지 못함.
- **해결**:
  ```bash
  # .bashrc에 환경변수 추가하여 영구 적용
  export LD_LIBRARY_PATH=/usr/local/lib/python3.10/dist-packages/torch/lib:$LD_LIBRARY_PATH


# TIL (Today I Learned) - 2026년 1월 23일

## 📝 오늘 작업 요약
Jetson Orin Nano 환경에서 YOLOv11 기반 객체 추적 시스템과 ROS2 기반 하드웨어 제어 환경을 통합하고, GPU 가속 최적화 및 도커 컨테이너 안정화 작업을 진행함.

## 🛠 주요 수행 내용

### 1. 도커(Docker) 기반 통합 개발 환경 구축
* **이미지 교체**: 기존 `l4t-base`에서 PyTorch와 CUDA가 최적화된 `ultralytics/ultralytics:latest-jetson-jetpack6` 이미지로 전환하여 라이브러리 충돌 문제 해결.
* **환경 통합**: USB 장치 권한(`--privileged`, `ttyUSB0`), 웹캠(`video0`), 그리고 여러 프로젝트 폴더(ROS2 워크스페이스, YOLO 코드)를 한 번에 마운트하는 통합 `run` 명령어 구성.

### 2. ROS2 Humble 및 하드웨어 드라이버 설치
* **ROS2 Humble**: 컨테이너 내부에 ROS2 Humble base 및 필수 도구(`teleop`, `slam-toolbox`, `rviz2`) 설치.
* **YDLidar S2 Pro 설정**: SDK 및 드라이버 설치 후, 가장 중요한 트러블슈팅 포인트인 `isSingleChannel: true`와 `baudrate: 128000` 설정 적용.
* **Motor HAT**: Waveshare Motor Driver HAT 제어를 위해 I2C 7번 버스 설정 및 `adafruit-circuitpython` 라이브러리 환경 구축.

### 3. YOLO 성능 최적화 (TensorRT)
* **문제**: PyTorch(`.pt`) 모델 직접 실행 시 발생하는 속도 저하 및 메모리 할당 에러(`CUBLAS_STATUS_ALLOC_FAILED`) 확인.
* **해결**: TensorRT 엔진(`.engine`) 포맷으로 모델을 Export 하여 Jetson의 Tensor 코어를 활용한 실시간 추론 속도 확보.

## 🚀 해결한 트러블슈팅 (Troubleshooting)
* **GPU 미인식**: 일반 `pip install torch`는 CPU 버전이 깔린다는 점을 확인, Jetson 전용 빌드가 포함된 이미지를 사용하여 GPU 가속 활성화.
* **포트 권한**: 도커 컨테이너 실행 시 `--device` 옵션만으로는 부족할 수 있어, 호스트에서 `chmod 666 /dev/ttyUSB0` 권한 부여 및 컨테이너 `--privileged` 모드 사용.
* **라이브러리 꼬임**: `numpy` 버전 충돌 문제를 수동 설치 대신 검증된 베이스 이미지를 사용하는 방식으로 해결.

## 📅 다음 목표
* YOLO에서 계산된 `error_x`(오차값)를 ROS2 `/cmd_vel` 토픽으로 발행하여 실시간 사람 추종 주행 테스트.
* SLAM Toolbox를 이용해 라이다 맵핑 데이터 확인 및 가짜 TF(`static_transform_publisher`) 안정화.

## 💾 작업 결과물 저장
* `docker commit`을 사용하여 ROS2와 모든 드라이버가 설치된 상태를 `robot_final` 이미지로 백업 완료.


# 📝 TIL: Jetson 엣지 디바이스를 위한 YOLO + ReID 최적화

**📅 날짜:** 2026.01.26  
**🏷️ 태그:** #YOLO #Jetson #OpenCV #Optimization #ReID

---

## 💡 배운 점 (Learnings)

### 1. 엣지 디바이스(Jetson) 성능 최적화의 핵심
- **모델 다이어트:** 무거운 `ResNet50`이나 Transformer 기반 Depth 모델은 Jetson에서 FPS를 급격히 떨어뜨린다. 이를 경량화된 `osnet_x0_25`와 **단순 박스 높이 기반 거리 추정 공식**으로 대체하여 성능을 확보했다.
- **해상도 트릭 (Input vs Process):** 넓은 시야각(FOV)이 필요하다고 해서 연산까지 고해상도로 할 필요는 없다. 카메라는 **1080p(16:9)**로 받아 화각을 확보하고, 실제 AI 연산은 **360p**로 리사이징(Resize)하여 **속도와 시야 두 마리 토끼**를 잡는 방법을 배웠다.

### 2. ReID(재식별) 데이터의 품질 관리
- **360도 데이터의 중요성:** 등록 시 정면만 학습하면 뒤돌았을 때 추적을 놓친다. 사용자가 몸을 돌리도록 유도하여 **다각도의 데이터**를 확보해야 한다.
- **코사인 유사도(Cosine Similarity) 활용:**
    - **등록 시:** 유사도가 너무 높으면(0.95 이상) "안 움직였다"고 판단해 캡처 스킵.
    - **추적 시:** 갤러리에 너무 똑같은 사진이 쌓이지 않게 중복 제거.

### 3. 하이브리드 추적 로직 (Hybrid Tracking)
- 단순히 옷(Body)만 보거나 얼굴(Face)만 보는 것이 아니라, **Face ID로 주인을 확정(Lock)** 짓고, 이후에는 **YOLO의 Tracking ID**를 신뢰하여 ReID 기준을 완화하는 **상호 보완적 로직**이 추적 안정성을 크게 높인다.

---

## 🚀 오늘 한 일 (Work Log)

### 1. 시스템 최적화 (Optimization)
- **모델 교체:** `resnet50_fc512` → `osnet_x0_25` (경량화)
- **프레임 스킵 (Frame Skipping):** 매 프레임 연산하지 않고, **3프레임마다** ReID/Face 인식을 수행하도록 캐싱 구현.
- **Depth 모델 제거:** 무거운 Deep Learning 모델 대신 `500.0 / box_height` 공식으로 거리 추정 대체.

### 2. 스마트 등록 시스템 (Smart Registration)
- **강제 회전 유도:** 이전 프레임과 유사도가 높으면 진행률이 오르지 않고, 화면에 **"TURN AROUND!"** 경고를 띄워 다양한 각도의 데이터를 수집함.
- **진행바 UI:** 사용자가 등록 상태를 직관적으로 알 수 있도록 시각화.

### 3. 동적 갤러리 (Dynamic Gallery) & ID Locking
- **Dynamic Update:** 추적 중 주인이 확실할 때, 현재 옷차림 정보를 갤러리에 실시간 추가(업데이트).
- **ID Locking:** 얼굴 인식 성공 시 해당 YOLO ID를 '주인'으로 고정하고, 등 돌림 등으로 ReID 점수가 떨어져도 추적을 유지하도록 개선.

### 4. 트러블 슈팅
- **차원 불일치 에러 해결:** `np.dot` 연산 시 `(1, 512)` 벡터끼리의 연산 오류를 `.T` (전치)와 `.item()`을 사용하여 해결.




# 2026.01.27 (화) TIL - ROS 2 자율주행 프로젝트 (트러블 슈팅 & 설계)

## 1. ROS 2 & Python 의존성 트러블 슈팅

### 🚨 문제 1: 빌드 꼬임 & 패키지 인식 불가
- **증상**: `ros2 run` 실행 시 `Package not found` 에러 발생.
- **원인**: 기존 빌드 잔여물과 새 빌드 설정 충돌.
- **해결**: 워크스페이스 초기화 후 재빌드.
  ```bash
  rm -rf build install log
  colcon build --symlink-install
  source install/setup.bash  # 터미널 켤 때마다 필수!

# 📅 [TIL] 2026-01-28: 우리 로봇이 드디어 벽을 피해가요! (YOLO + Nav2 연동)

### 📝 오늘의 목표
1. **주인 알아보기:** YOLO와 ReID로 나(주인)를 확실하게 등록하고 기억하게 만들기.
2. **똑똑하게 쫓아오기:** 장애물이 있으면 무식하게 직진하지 말고, **Nav2**를 써서 피해오게 만들기.
3. **컴퓨터 지키기:** WSL이 뻗지 않게 리소스 관리하기.

---

## 🚀 1. YOLO 노드: "주인님, 절대 안 놓쳐요!"

처음에는 그냥 YOLO만 썼더니 뒤돌면 주인을 놓치거나 다른 사람을 쫓아가는 문제가 있었다. 그래서 **ReID(재식별)** 기술을 더 빡세게 적용했다.

### 💡 배운 점 & 구현한 것
* **50장 등록 시스템:** 처음 시작할 때 로봇 앞에서 한 바퀴 돌면서 내 사진 50장을 찍어서 등록한다.
* **스마트 갤러리:** * 그냥 막 찍으면 똑같은 사진만 50장 모인다. 
    * **"유사도 검사"**를 넣어서, 기존 사진이랑 너무 비슷하면(93% 이상) 저장 안 하고 "좀 움직여보세요!"라고 경고를 띄웠다. 덕분에 다양한 각도의 내 모습이 저장됨!.
* **ID Locking (집착 모드):** 한 번 주인으로 인식된 ID는 뒤돌거나 가려져도 끝까지 주인이라고 믿는 기능을 넣었다. (확신이 들면 초록색 박스로 똭!).

---

## 🤖 2. 팔로워 노드: "직진남에서 뇌섹남으로"

이게 오늘 제일 힘들었던 부분. 원래는 주인 방향으로 무조건 직진(`cmd_vel`)만 줬더니, 사이에 의자가 있으면 의자를 밀고 가려고 했다... 😅

### 🛠️ 하이브리드 제어기 (Hybrid Controller) 구현
Nav2(자율주행)가 좋긴 한데, 계속 켜두면 로봇이 너무 신중해서 반응이 느리고 컴퓨터도 힘들어했다. 그래서 **두 가지 방식을 섞었다!**

1.  **평상시 (Direct Control):**
    * 앞이 뻥 뚫려 있으면? -> Nav2 끄고 직접 모터 제어. (반응 속도 빠름!).
2.  **장애물 감지시 (Nav2 Control):**
    * 가는 길에 장애물이 있다? -> **"Nav2야, 도와줘!"** 하고 목표 좌표를 보냄.
    * Nav2가 알아서 장애물을 피하는 꼬불꼬불한 경로를 만들어줌.
    * 장애물 피해서 다시 길이 열리면? -> 다시 직접 제어 모드로 복귀!.

### 🚧 엣지 케이스(Edge Case) 해결
* **문제:** 주인은 보이는데, 직선 경로에 벽 모서리가 살짝 걸친 경우. 로봇이 "보인다!" 하고 가다가 어깨를 벽에 박음.
* **해결:** 단순히 "앞"만 보는 게 아니라, **"주인에게 가는 직선 경로"**에 장애물이 있는지 레이저(LiDAR)로 확인함 (`check_path_safety` 함수)..

---

## ⚙️ 3. 시스템 설정 (삽질의 기록...)

### 🗺️ Nav2 파라미터 튜닝
* 로봇이 기둥을 너무 무서워해서 멀리서 멈칫거렸다.
* `my_nav2_params.yaml` 파일에서 `inflation_radius`(위험 반경)를 **0.55**로 줄였더니 기둥 옆을 쉭쉭 잘 지나간다! 
* Nav2 설정 파일에서 `critics` 에러가 나서 한참 고생함. (설정값 다 넣어줘야 함 ㅠㅠ)

### 💻 WSL 메모리 할당
* YOLO + Nav2 + RViz 다 켜니까 윈도우가 멈춤.
* `.wslconfig` 파일 만들어서 메모리랑 CPU 빵빵하게 할당해줌. 이제 쾌적하다.

---

## 🧐 오늘의 결론 (회고)
* **알고리즘 vs 라이브러리:** "장애물 회피"를 직접 `if-else`로 짜려다가 Nav2를 썼는데, 이게 정답이었다. 바퀴를 다시 발명하지 말자.
* **센서 퓨전:** 카메라는 "누군지" 알려주고, 라이다는 "어디가 막혔는지" 알려준다. 이 둘을 합치니까 진짜 자율주행 로봇 같다.
* **남은 과제:** 로봇이 턴할 때 조금 더 부드럽게 돌았으면 좋겠다. 속도 조절(PID 제어)을 좀 더 공부해야 할 듯.

### 🏃‍♂️ 실행 순서 기억하기!
1. 시뮬레이터 켜기
2. 지도 불러오기 (`localization`)
3. **네비게이션 켜기 (`navigation`)**
4. **RViz에서 초기 위치 찍어주기 (이거 안 해서 30분 날림)**
5. YOLO 노드 켜기
6. 팔로워 노드 켜기


# TIL: ROS 2 자율주행 추종 로봇 개발 (Troubleshooting & Optimization)

**날짜:** 2026년 1월 29일  
**주제:** YOLO + LiDAR 기반 하이브리드 추종 로봇 제어 및 Nav2 최적화  
**환경:** ROS 2 Humble, Ubuntu 22.04, Python 3.10

---

## 🚀 1. 주요 트러블 슈팅 (Troubleshooting)

### ① Nav2 `controller_server` 크래시 해결
- **현상:** `MapsToPose` 액션 서버가 실행되지 않고 `Waiting for service...` 무한 대기. `ros2 node list` 확인 시 `controller_server`가 보이지 않음.
- **원인:** `nav2_params.yaml`에 정의된 `DWBLocalPlanner` 플러그인이 시스템에 설치되지 않아 노드가 시작 즉시 종료됨.
- **해결:** DWB 컨트롤러 패키지 설치.
  ```bash
  sudo apt install ros-humble-nav2-dwb-controller

# TIL (Today I Learned) - 2026.01.30

## 📝 오늘 완료한 작업: 하이브리드 추종 로봇 최적화

### 1. 제어 안정화 (Anti-Oscillation)
- **PID 튜닝:** 주행 시 좌우 요동을 잡기 위해 `I(적분)` 항을 제거하여 오버슈트를 방지하고, `P` 계수를 낮춤 (`0.012`).
- **입력 지연 개선:** `ANGLE_SMOOTHING_ALPHA`를 `0.6`으로 높여 조향 반응 속도를 개선, "뒷북" 제어로 인한 진동을 해결함.
- **불감대 설정:** `6.0도` 이내의 미세 오차는 무시하여 잔진동을 제거함.

### 2. 스마트 복구 모드 (Recovery & Search)
- **하이브리드 추적:** YOLO(시각)를 놓쳐도 Lidar 클러스터링을 통해 `Blind Tracking`을 수행하도록 로직 강화.
- **SLAM 기반 복구:** 대상을 완전히 놓치면 마지막 위치보다 1.0m 더 깊은 곳을 목표로 Nav2 경로를 생성하여 코너 주행(Peek around corner) 구현.
- **탐색 및 랑데부:** 목적지 도착 후 20초간 저속 회전 탐색을 수행하고, 실패 시 제자리 대기(`WAITING`)하여 사용자와의 재회를 유도함.

### 3. Nav2 및 주행 안전성 강화
- **Planner Server 활성화:** `ComputePathToPose` 에러 해결을 위해 `my_nav2_params.yaml`에 `planner_server` 설정 추가.
- **하이브리드 주행:** Nav2로 경로(`Path`)만 생성하고, 실제 주행은 `Potential Field` 회피 로직을 적용한 직접 제어 방식으로 구현하여 좁은 기둥 사이 충돌 방지.
- **긴급 정지:** 전방 장애물 감지 거리를 `0.45m`로 확대하여 돌발 상황 대응력 강화.

### 4. 시행착오 및 해결
- **문제:** Nav2 주행 중 코너 안쪽 기둥에 부딪힘.
- **원인:** `lookahead_dist`가 너무 길어 코너를 가로지르려 함.
- **해결:** Lookahead 거리를 `0.4m`로 단축하여 생성된 곡선 경로에 밀착 주행하도록 수정.

---
**Next Step:** 수정된 맵(Keepout Zone 적용) 테스트 및 기둥 밀집 지역 실전 주행 확인.


# TIL (Today I Learned) - 2026.02.02

## 1. 작업 범위 (Scope)
- **Software**: ROS2 Humble, Gazebo Simulator, SLAM Toolbox, Navigation2 (Nav2), RViz2
- **Hardware**: NVIDIA Jetson Orin Nano, JGA25-371 DC Motor (w/ Encoder), Waveshare Motor Driver HAT
- **Task**: 가제보 시뮬레이션 맵핑(Mapping) 성공 및 실물 모터 엔코더 배선 점검

## 2. 한 일 (Work Done)

### 🛠️ ROS2 시뮬레이션 & 맵핑 트러블슈팅
- **RViz 'No map received' 에러 해결**
  - 원인: `robot_state_publisher` 노드가 실행되지 않아 TF(로봇 관절 좌표) 정보가 없었음.
  - 해결: `robot_state_publisher`를 실행하고, RViz의 Map QoS 설정을 `Transient Local`로 변경.
- **Time Sync(시간 동기화) 에러 해결**
  - 원인: 시뮬레이터는 가상 시간을 쓰는데, 노드들이 현실 시간을 써서 타임스탬프 불일치 발생.
  - 해결: 모든 실행 명령어(SLAM, State Publisher 등)에 `use_sim_time:=True` 옵션 추가.
- **맵 저장 및 Nav2 경로 에러 수정**
  - `map_saver_cli`를 이용해 `.pgm`(이미지), `.yaml`(설정) 파일 저장 성공.
  - Nav2 실행 시 `.yaml` 파일만 있고 `.pgm` 파일이 없어 발생한 로딩 에러 해결 (파일 경로 통일).

### 🔌 하드웨어(Jetson & Motor) 배선 디버깅
- **엔코더 전원 연결 및 쇼트(Short) 진단**
  - 왼쪽 모터 엔코더는 정상 작동(3.3V) 확인.
  - 오른쪽 모터 엔코더 연결 시 전체 전압이 0V로 떨어지는 현상 발견.
  - **진단 결과**: 오른쪽 모터의 VCC(3.3V)와 GND 라인이 내부적으로 합선(Short)된 상태임을 확인. (Jetson 보드 보호를 위해 연결 해제)

## 3. 배운 점 (Lessons Learned)

### 🤖 ROS2
- **`robot_state_publisher`의 중요성**: 단순히 로봇 모델(Spawn)만 불러오는 것으로는 부족하며, 로봇의 TF를 송출해주는 State Publisher가 켜져 있어야 SLAM과 내비게이션이 작동한다.
- **Simulation Time**: 가제보 환경에서는 무조건 `use_sim_time:=True`를 습관화해야 한다.
- **Nav2 Map Server**: 맵을 불러올 때는 `.yaml` 파일 안에 적힌 이미지 경로(`.pgm`)에 실제 파일이 존재해야 한다. (같은 폴더에 두는 것이 정신 건강에 이롭다.)

### ⚡ 하드웨어 & 전자회로
- **쇼트(Short) vs 단선(Open)의 차이**
  - **쇼트**: (+)와 (-)가 직접 닿아 전류가 폭주하고 전압이 0이 되는 위험한 상태.
  - **단선**: 선이 끊어져 전기가 안 통하는 상태.
- **Jetson GPIO 주의사항**: Jetson의 GPIO는 **3.3V Tolerance**이므로, 5V를 인가하면 보드가 손상될 수 있다. 엔코더 전원은 반드시 3.3V 핀(Pin 1, 17)을 사용해야 한다.
- **공통 접지(Common Ground)**: 서로 다른 전원(모터용 12V, 제어용 3.3V)을 쓰더라도 통신을 위해 GND는 하나로 묶어야 한다.


# 2026-02-03 TIL: ROS2 시뮬레이션 트러블슈팅 및 환경 설정

## 1. ROS2 & Gazebo Simulation

### 🛑 Launch File 실행 순서 동기화 (Sync Issue)
**문제:** Launch 파일에서 Gazebo 실행, 로봇 Spawn, Nav2 실행이 비동기적으로 동시에 시작되어, TF 트리가 완성되기 전에 Nav2가 켜지는 바람에 초기화 에러 발생.
**해결:** `RegisterEventHandler`와 `OnProcessExit`를 사용하여 실행 순서를 강제함.
- Gazebo 실행 & 로봇 Spawn 시작
- **Spawn 프로세스가 종료(성공)되면** → Nav2 & RViz 실행
- `TimerAction`을 추가하여 TF 안정화 시간(3~5초) 확보 후 Nav2 실행

### 📍 Nav2 초기 위치 자동 설정 (AMCL)
**문제:** Gazebo에서는 로봇을 `(-5.0, 5.0)`에 소환했으나, Nav2(AMCL)는 `(0, 0)`으로 인식하여 RViz에서 매번 `2D Pose Estimate`를 수동으로 찍어야 함.
**해결:** `bringup_launch.py` 호출 시 `initial_pose` 파라미터 전달.


# 2026-02-04 TIL: ROS2 Nav2 파라미터 튜닝 및 실전 테스트

## 1. 🎯 Nav2 파라미터 튜닝 (Costmap & DWA)

### 1.1 로컬 Costmap (Local Costmap) - 좁은 길 통과
**목표:** 좁은 통로(문, 복도)를 로봇이 부드럽게 통과하도록 설정.

* **`inflation_radius`**: `0.50` (기존 0.30 → 0.50으로 확장)
    * **의미:** 로봇 주변 50cm까지를 '위험 구역'으로 인식.
    * **효과:** 로봇이 벽에 더 바짝 붙어서 지나가도, 50cm 이내의 작은 장애물은 '통과 가능'으로 판단하여 경로를 유지함.
* **`cost_scaling_factor`**: `40.0` (기존 25.0 → 40.0으로 상향)
    * **의미:** 장애물 회피 강도.
    * **효과:** 같은 거리의 장애물이라도 더 강하게 밀어내어, 로봇이 장애물을 피해 더 넓은 공간으로 우회하도록 유도.

### 1.2 글로벌 Costmap (Global Costmap) - 전역 경로 계획
**목표:** 전체 맵 상에서 최적의 경로를 찾되, 너무 꼬불꼬불하지 않게 설정.

* **`inflation_radius`**: `0.10` (기존 0.30 → 0.10으로 축소)
    * **의미:** 전역 맵에서는 좁은 길을 피하는 것이 좋음. 10cm 정도의 여유만 두고 경로를 그림.
* **`cost_scaling_factor`**: `70.0` (기존 20.0 → 70.0으로 대폭 상향)
    * **의미:** 전역 경로 탐색 시 장애물을 **매우 강하게** 회피.
    * **효과:** 좁은 통로를 억지로 지나가려 하지 않고, 막혔다면 즉시 우회하여 먼 길이라도 돌아가는 경로를 선택함. (좁은 길에서 멈추는 현상 방지)

## 2. 🛠️ 실전 테스트 결과

### 1. 좁은 통로(문) 통과 테스트
* **결과:** **성공!** 🚪
* **상황:** 좁은 문을 통과할 때, 기존에는 벽에 닿으면 멈추거나 덜덜 떨었으나, 튜닝 후에는 50cm의 여유를 두고 부드럽게 통과함.

### 2. 장애물 회피 테스트
* **결과:** **성공!** 🔄
* **상황:** 좁은 복도에서 장애물을 만나자, 좁은 길로 진입하려다 멈추는 대신 즉시 우회하여 넓은 공간으로 돌아가는 경로를 선택함.

### 3. ⚠️ 여전히 남은 문제 (Remaining Issue)
* **문제:** 로봇이 **'문지방'**을 장애물로 인식하여 통과하지 못함.
* **원인:**
    * **Costmap:** 문지방을 '장애물(Obstacle)'로 인식.
    * **Inflation:** 문지방 주변을 '위험 구역'으로 인식.
    * **DWA:** 좁은 통로(문)를 '통과 불가능'으로 판단.
* **해결 방안:**
    * **Map Editing:** `map_server`가 인식하는 맵(PGM)에서 문지방 영역을 **흰색(비장애물)**으로 칠해야 함.
    * **Costmap Tuning:** `inflation_radius`를 더 늘리거나, `cost_scaling_factor`를 낮추는 방법도 있으나, 맵 수정이 근본적인 해결책.


# TIL: 2026-02-04 (로봇 지능형 추적 및 주행 시스템)

## 1. 개요
인공지능 기반의 시각 인식 시스템과 ROS2 기반의 자율 주행 제어 시스템을 결합하여, 특정 사용자를 인식하고 안전하게 따라가는 '사람 추종 로봇'의 핵심 로직을 학습함.

---

## 2. 학습 내용

### 🛰️ 파트 1: 로봇의 발 (주행 및 제어 시스템)
카메라와 라이다(LiDAR)를 결합하여 안정적인 주행을 구현하는 알고리즘.

* **하이브리드 추적 (Sensor Fusion):** * **카메라(YOLO):** 타겟의 방향(Angle) 식별.
    * **라이다(LiDAR):** 타겟과의 정확한 거리 측정 및 장애물 구분.
    
* **지능형 상태 관리 (FollowState):**
    * 추적(Tracking), 실종 시 복구(Recovery), 탐색(Searching) 상태를 스스로 전환.
* **부드러운 주행 제어:**
    * **Pivot Turn:** 제자리에서 방향 전환 후 직진하여 급격한 회전 방지.
    * **Potential Field:** 장애물을 밀어내는 가상의 힘을 계산해 부드럽게 회피.
    

### 👁️ 파트 2: 로봇의 눈 (시각 인식 및 학습 시스템)
단순 인식을 넘어 주인을 '학습'하고 '구별'하는 고도화된 비전 알고리즘.

* **360도 입체 등록:** * 최초 등록 시 사용자의 앞, 뒤, 옆모습을 40장의 다양한 데이터로 저장 (얼굴 + 옷차림 + 체격).
* **퓨전 판별 (Face + ReID):** * 정면은 **얼굴(InsightFace)**로, 뒷모습은 **체형(ReID)**으로 인식하여 혼잡한 곳에서도 타겟 유지.
    
* **실시간 적응 학습:** * 추적 중 변화하는 조명이나 자세 정보를 갤러리에 지속적으로 업데이트하여 환경 적응력 극대화.

---

## 3. 핵심 요약
> **"한 번 등록하면 얼굴이 안 보여도 끝까지 찾아내며(눈), 장애물을 피해 안전하고 매너 있게 운전하는(발) 로봇 시스템"**

---

## 4. 자기성찰 및 향후 계획
* **성찰:** 단순히 사람을 쫓는 것을 넘어, 타겟이 가려지거나 환경이 변할 때 어떻게 데이터가 갱신되고 복구되는지가 시스템 안정성의 핵심임을 깨달음.
* **계획:** 다수의 사람이 겹치는 'Occlusion' 상황에서 ReID 성능을 극대화할 수 있는 필터링 기법에 대해 추가 연구 예정.


# 📝 TIL: ROS2 & Nav2 자율주행 시스템 통합

**날짜:** 2026-02-05

## 🎯 프로젝트 목표

-   **자율주행 환경 구축:** Jetson Orin Nano와 LiDAR 센서를 활용한 실제
    로봇 주행 환경 조성
-   **시스템 통합:** SLAM을 이용한 지도 생성 및 Nav2를 활용한 경로
    계획(Path Planning) 연동
-   **지능형 추종:** YOLO 탐지 데이터와 내비게이션 기능을 결합하여
    사람을 따라가는 시스템 구현

## 🏗️ 핵심 학습 내용

### 1. Nav2 라이프사이클 관리 (Lifecycle)

-   **시스템 동기화:** 내비게이션 서버들이 완전히 활성화(Active)된 후
    명령을 내려야 초기 위치가 정상 설정됨을 학습함
-   **초기화 자동화:** 로봇이 시작될 때 지도상 특정 좌표를 자동으로
    잡도록 하여 수동 설정의 번거로움을 해결함

### 2. 센서 융합 및 데이터 매핑

-   **ID 핸드셰이크:** YOLO에서 탐지된 객체에 특정 ID 오프셋(예:
    +1000)을 부여하여 추종 노드가 대상을 정확히 식별하게 함
-   **좌표계(TF) 정합:** 로봇의 중심점(base_link)과 지도(map) 사이의
    좌표 변환이 끊기지 않도록 정적 변환을 추가하여 주행 안정성을 확보함

## 🛠️ 주요 문제 해결 (Troubleshooting)

-   **시뮬레이션과 실제의 차이:** 시뮬레이션 시간(use_sim_time) 설정을
    실제 로봇 환경(False)에 맞춰 통일하여 좌표계 오차를 해결함
-   **주행 부드러움 개선:** 급격한 회전으로 인해 시야를 놓치지 않도록
    회전 속도를 제한하고 PID 제어값을 세밀하게 튜닝함
-   **장애물 회피 가중치 조절:** 장애물에 너무 민감하게 반응하여 주인
    추적을 방해받지 않도록 회피 가중치를 최적화함

## 💡 오늘의 요약

-   **안정적인 시작이 중요:** 내비게이션 노드들이 다 켜질 때까지
    기다리는 '대기 로직'이 시스템 전체 신뢰성을 높임
-   **데이터 일관성:** 노드 간에 주고받는 ID와 좌표 형식을 일치시키는
    것이 복잡한 로봇 시스템 운영의 핵심임


