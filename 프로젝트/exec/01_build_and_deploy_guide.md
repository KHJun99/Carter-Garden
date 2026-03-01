# 1) GitLab 소스 클론 이후 빌드/배포 문서

## 1. 저장소 클론
```bash
git clone <GITLAB_REPO_URL>
cd S14P11D201
```

## 2. 구성 요소 및 런타임 버전
| 구분 | 제품/프레임워크 | 버전/설정 |
|---|---|---|
| Backend WAS | Flask (Python) | `server/backend/run.py` 기준 `0.0.0.0:5001`, `debug=True` |
| Backend DB 드라이버 | PyMySQL + SQLAlchemy | `mysql+pymysql` |
| Frontend Web Server (Dev) | Vite | `vite` (dev server 기본 5173) |
| Frontend Framework | Vue 3 + Vuetify + Pinia | `raspberry_pi/frontend/package.json` 기준 |
| ROS 연동 | rosbridge websocket | `ws://<JETSON_IP>:<JETSON_ROS_PORT>` |
| 로봇 미들웨어 | ROS 2 Humble | `jetson/*README*` 기준 |
| 결제 연동 | Toss Payments | JS SDK + 서버 confirm API |
| 클라우드 | AWS S3, AWS RDS(MySQL), EC2 | README 기준 운영 |
| JVM | 사용 안 함 | N/A |

참고: OS/DE(Desktop Edition) 버전(예: Ubuntu 22.04 Desktop/Server)은 저장소에 명시가 부족하므로 실제 운영 장비에서 `lsb_release -a`로 확정 필요.

## 3. 빌드/실행 절차

### 3-1. Backend (`server/backend`)
```bash
cd server/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 run.py
```

### 3-2. Frontend (`raspberry_pi/frontend`)
```bash
cd raspberry_pi/frontend
npm install
npm run dev
# 키오스크 실행
export DISPLAY=:0 && chromium --kiosk --password-store=basic http://localhost:5173
```

### 3-3. Jetson/ROS (개요)
```bash
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
# 프로젝트 런치 파일 실행 (실장비 환경)
ros2 launch real_robot_launch.py
```

## 4. 빌드/실행 환경 변수 상세

### 4-1. Backend `.env` 키 (`server/backend/app/config.py`)
- `DB_USER`
- `DB_PASSWORD` (필수)
- `DB_HOST`
- `DB_PORT` (로컬 실행 시 사용 가능)
- `DB_NAME`
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION` (기본 `ap-northeast-2`)
- `AWS_BUCKET_NAME`
- `SECRET_KEY`
- `GMS_API_URL`
- `GMS_API_KEY`
- `GMS_MODEL` (기본 `gpt-5.2`)
- `TOSS_SECRET_KEY` (필수)

### 4-2. Frontend `.env` 키 (`raspberry_pi/frontend/src/config.js`)
- `VITE_API_URL`
- `VITE_JETSON_IP`
- `VITE_JETSON_VIDEO_PORT`
- `VITE_JETSON_ROS_PORT`
- `VITE_TOSS_CLIENT_KEY`

## 5. 배포 시 특이사항
- GitLab CI 파일(`.gitlab-ci.yml`)에서 배포 경로와 실제 프로젝트 경로가 다를 수 있으니 운영 서버 디렉터리 구조를 먼저 맞춰야 함.
- Backend는 `run.py`에서 debug 모드로 실행되므로 운영 배포 시에는 WSGI 서버(gunicorn 등) 전환 권장.
- 결제/클라우드 연동은 키 누락 시 즉시 예외 발생(`DB_PASSWORD`, `TOSS_SECRET_KEY` 체크 로직 존재).
- 키오스크는 X11/HDMI/해상도 설정 영향을 받음(README 가이드 참조).

## 6. DB 접속 정보/ERD 관련 주요 계정/프로퍼티 파일 목록

### 6-1. 접속 및 프로퍼티 정의 파일
- `server/backend/app/config.py`
- `server/backend/.env` (실배포 시 생성)
- `server/backend/README.md` (`~/.my.cnf` 예시 포함)

### 6-2. 스키마/데이터/그래프 SQL
- `server/backend/smartcartDB/0.3/Smart_Cart_DB.sql`
- `server/backend/smartcartDB/0.3/Smart_Cart_DataSample.sql`
- `server/backend/smartcartDB/0.3/Smart_Cart_Graph_DataSample.sql`

### 6-3. 샘플 계정 (DataSample 기준)
- 로그인 ID: `test`
- 비밀번호: 해시 저장(`scrypt...`), 평문 미포함
