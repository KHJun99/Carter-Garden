# 🛒 Smart Cart Server Guide (AWS EC2)

이 문서는 AWS EC2 서버 환경에서 MySQL 데이터베이스 관리, SQL 스크립트 실행, Flask 서버 수동 구동 방법을 정리한 가이드입니다.

---
## backend 폴더 구조
```
  backend/
  ├── run.py                 # 앱 실행 엔트리 포인트 (Flask Runner)
  ├── config.py              # 환경 설정 (DB URI, AWS Keys, Secret Keys 등)
  ├── .env                   # 환경변수 (Git 제외 대상, 민감 정보)
  ├── requirements.txt       # 의존성 패키지 목록
  └── app/                   # 애플리케이션 핵심 로직
      ├── __init__.py        # 앱 팩토리(create_app), Blueprint 등록
      ├── extensions.py      # Flask 확장 객체(SQLAlchemy, Migrate, CORS 등) 관리
      ├── errors.py          # 전역 예외 처리(Error Handlers) 정의
      │
      ├── models/            # [DB 계층] 데이터베이스 테이블 모델 (SQLAlchemy)
      │   ├── __init__.py    # 모델 통합 관리
      │   ├── user.py, product.py, cart.py, order.py, ...
      │
      ├── services/          # [비즈니스 로직 계층] 핵심 기능 구현 (Service Layer)
      │   ├── __init__.py    # 서비스 함수 통합 Export
      │   ├── user_service.py    # 로그인, 토큰 검증
      │   ├── product_service.py # 상품 검색 및 조회
      │   ├── cart_service.py    # 장바구니 대여/반납 로직
      │   ├── coupon_service.py  # 쿠폰 발급/사용 로직
      │   ├── rfid_service.py    # RFID 태그 유효성 검사
      │   └── s3_service.py      # AWS S3 파일 업로드/관리
      │
      ├── routes/            # [API 컨트롤러 계층] HTTP 엔드포인트 및 Blueprint
      │   ├── __init__.py    # 블루프린트 통합 관리
      │   ├── auth_route.py, product_route.py, cart_route.py, ...
      │
      ├── schemas/           # [검증/직렬화 계층] 요청 데이터 검증 및 응답 포맷 (Marshmallow)
      │   ├── __init__.py
      │   ├── auth_schema.py, product_schema.py, coupon_schema.py, ...
      │
      └── utils/             # [유틸리티] 공통 도구 모음
          ├── __init__.py
          ├── validators.py  # 공통 입력값 검증기
          ├── response.py    # 표준 응답 포맷 정의
          └── time.py        # 시간 및 타임스탬프 유틸리티
```

## 1. 서버 접속 (SSH)

내 컴퓨터(로컬)에서 AWS 서버 터미널에 접속하는 방법입니다.

```bash
# pem 키가 있는 폴더에서 실행
ssh -i "I14D201T.pem" ubuntu@i14d201.p.ssafy.io

```

## 1-1. 사전 설정 (최초 1회)

서버에 접속 후, 매번 비밀번호를 입력하지 않도록 자동 로그인 설정을 권장합니다.

```bash
# 1. 홈 디렉토리에 설정 파일 생성
nano ~/.my.cnf

# 2. 아래 내용 붙여넣기 (본인 비번 입력)
[client]
user=root
password=0000

(`Ctrl + X` -> `Y` -> `Enter` 로 저장)

# 3. 보안 권한 설정 (필수)
chmod 600 ~/.my.cnf

```

> **이제부터 `mysql` 명령어 사용 시 비밀번호를 묻지 않습니다.**
mysql
# 또는
mysql < script.sql
# 명령어 입력시 바로 mysql 실행.

---

## 2. MySQL 데이터베이스 관리

### 2-1. MySQL 서버 켜기/끄기

MySQL이 꺼져있다면 다음 명령어로 관리합니다.

```bash
# 실행 상태 확인
sudo systemctl status mysql

# MySQL 켜기
sudo systemctl start mysql

# MySQL 끄기
sudo systemctl stop mysql

# MySQL 재시작
sudo systemctl restart mysql

```

### 2-2. MySQL 접속 (CLI)

직접 DB에 들어가서 데이터를 확인할 때 사용합니다.
(사전 설정이 되어 있다면 비밀번호 입력 없이 접속됩니다.)

```bash
mysql

```

```sql
-- 자주 쓰는 명령어
USE SMART_CART;   -- DB 선택 (대문자 주의)
SHOW TABLES;      -- 테이블 목록 보기
SELECT * FROM users; -- 사용자 데이터 조회
EXIT;             -- 나가기

```

---

## 3. SQL 스크립트 실행 (DB 초기화)

서버에 저장된 `.sql` 파일을 실행하여 테이블을 생성하거나 데이터를 넣는 방법입니다.

* **파일 위치:** `/home/ubuntu/server-app/server/backend/smartcartDB/0.3/Smart_Cart_DB.sql`

### 방법 A: 터미널에서 명령어 한 줄로 실행 (추천)

```bash
# 비밀번호 입력 불필요 (자동 로그인)
mysql < /home/ubuntu/server-app/server/backend/smartcartDB/0.3/Smart_Cart_DB.sql
mysql < /home/ubuntu/server-app/server/backend/smartcartDB/0.3/Smart_Cart_DataSample.sql
mysql < /home/ubuntu/server-app/server/backend/smartcartDB/0.3/Smart_Cart_Graph_DataSample.sql
```

> **주의:** SQL 파일 내부에 `USE SMART_CART;`가 포함되어 있어 자동으로 해당 DB에 적용됩니다.

### 방법 B: GitLab CI/CD 파이프라인 사용 (가장 추천)

GitLab 웹페이지 **Build > Pipelines** 메뉴에서 **`reset-db`** 스테이지의 **재생 버튼(▶)**을 누르면 자동으로 초기화됩니다.

---

## 4. Flask 서버 수동 실행 (`run.py`)

자동 배포(CI/CD)가 아니라, 테스트를 위해 **수동으로 서버를 껐다 켜야 할 때** 사용합니다.

### 4-1. 프로젝트 폴더로 이동

```bash
cd /home/ubuntu/server-app/server/backend

```

### 4-2. 가상환경(venv) 활성화

파이썬 패키지가 설치된 가상환경을 켭니다. (프롬프트 앞에 `(venv)`가 떠야 함)

```bash
# 가상환경이 없다면 생성: python3 -m venv venv
source venv/bin/activate

```

### 4-3. 패키지 설치 (필요시)

`requirements.txt`가 변경되었다면 실행합니다.

```bash
pip install -r requirements.txt

```

### 4-4. 서버 실행

**옵션 1: 터미널 켜놓은 상태로 실행 (로그 바로 확인)**

```bash
python3 run.py
# 끄려면 Ctrl + C

```

**옵션 2: 백그라운드 실행 (터미널 꺼도 계속 돌아감)**

```bash
# 1. 기존에 돌고 있는 서버 죽이기
pkill -f 'python3 run.py'

# 2. 백그라운드 실행 (로그는 flask.log에 저장)
nohup python3 run.py > flask.log 2>&1 &

# 3. 잘 실행됐는지 확인
ps -ef | grep python3

```

#### API 명세서 확인 - flasger
다음 주소로 접속하여 확인 가능하다. 로컬 실행 시 앞 주소를  localhost:포트번호 로 바꿔 접속 가능.
http://i14d201.p.ssafy.io/apidocs/

---

## 5. 로그 확인 및 디버깅

서버가 에러가 났을 때 로그를 확인하는 방법입니다.

```bash
# 1. 프로젝트 폴더 이동
cd /home/ubuntu/server-app/server/backend

# 2. 로그 파일 실시간 보기 (마지막 50줄)
tail -f -n 50 flask.log
# (빠져나오려면 Ctrl + C)

```

---

## 6. 요약 (치트시트)

| 작업 | 명령어 |
| --- | --- |
| **SSH 접속** | `ssh -i "I14D201T.pem" ubuntu@i14d201.p.ssafy.io` |
| **폴더 이동** | `cd /home/ubuntu/server-app/server/backend` |
| **가상환경 켜기** | `source venv/bin/activate` |
| **서버 켜기(배경)** | `nohup python3 run.py > flask.log 2>&1 &` |
| **서버 끄기** | `pkill -f 'python3 run.py'` |
| **DB 접속** | `mysql` (설정 완료 시 비번 불필요) |
| **로그 보기** | `tail -f flask.log` |
