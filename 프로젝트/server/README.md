# Server

스마트 카트 서버(백엔드) 관련 문서입니다.

## 폴더 구조
```text
server/
└── backend/                        # [Server] Flask API + AWS + DB
    ├── .env                        # 환경변수 (DB, AWS, JWT 등)
    ├── requirements.txt            # 파이썬 의존성 패키지 목록
    ├── run.py                      # 서버 실행 엔트리 포인트
    ├── app/
    │   ├── models/                 # DB 모델
    │   ├── routes/                 # API 라우트
    │   ├── schemas/                # 검증/직렬화
    │   ├── services/               # 비즈니스 로직
    │   └── utils/                  # 공통 유틸
    └── smartcartDB/                # DB 초기화/샘플 SQL
```

## 프로젝트 실행 가이드 (AWS + Local)

### 사전 준비 (AWS 리소스)
1. **RDS (MySQL)**
   - 데이터베이스 생성 (`SMART_CART` 권장)
   - 보안 그룹에서 3306 포트 허용
   - 엔드포인트 주소 확인
2. **S3 버킷**
   - 이미지 업로드용 버킷 생성
   - Access Key / Secret Key 준비
3. **DB 스키마 초기화**
   - RDS 접속 후 `Smart_Cart_DB.sql` 실행

### EC2 서버 접속 후 백엔드 실행
```bash
ssh -i "I14D201T.pem" ubuntu@i14d201.p.ssafy.io
cd /home/ubuntu/server-app/server/backend
source venv/bin/activate
pip install -r requirements.txt
python3 run.py
# 또는 nohup python run.py > flask.log 2>&1 &
```

### 로컬/타깃 장비에서 백엔드 실행
```bash
cd ~/S14P11D201/server/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
nohup python run.py > flask.log 2>&1 &
```

## 참고
- 프론트엔드(키오스크 UI) 설명/실행은 `raspberry_pi/frontend/README.md`를 참고하세요.
