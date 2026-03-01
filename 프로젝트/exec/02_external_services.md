# 2) 프로젝트 외부 서비스 정리 문서

## 외부 서비스 목록

### 1. Toss Payments (결제)
- 사용 위치
  - 프론트 SDK: `raspberry_pi/frontend/src/composables/useTossPayment.js`
  - 백엔드 승인 API: `server/backend/app/services/payment_service.py`
- 필요한 정보
  - 프론트: `VITE_TOSS_CLIENT_KEY`
  - 백엔드: `TOSS_SECRET_KEY`
- 동작
  - 프론트에서 결제 요청 -> 백엔드에서 `https://api.tosspayments.com/v1/payments/confirm` 호출

### 2. AWS S3 (이미지 업로드/정적 URL)
- 사용 위치: `server/backend/app/services/s3_service.py`
- 필요한 정보
  - `AWS_ACCESS_KEY_ID`
  - `AWS_SECRET_ACCESS_KEY`
  - `AWS_REGION`
  - `AWS_BUCKET_NAME`
- 비고
  - 업로드 후 `https://<bucket>.s3.<region>.amazonaws.com/<object>` URL 반환

### 3. AWS RDS / EC2 (인프라)
- 사용 위치: `server/README.md`, `server/backend/README.md`
- 필요한 정보
  - RDS 접속 정보 (`DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`)
  - EC2 SSH 키(`.pem`) 및 접속 계정

### 4. GMS(OpenAI 호환 API 형태) 추천 모델 호출
- 사용 위치: `server/backend/app/services/product_service.py`
- 필요한 정보
  - `GMS_API_URL`
  - `GMS_API_KEY`
  - `GMS_MODEL`
- 비고
  - 장바구니 기반 추천 상품 1개 생성

### 5. ROS Bridge WebSocket (로봇 제어 연동)
- 사용 위치: `raspberry_pi/frontend/src/api/rosManager.js`
- 필요한 정보
  - `VITE_JETSON_IP`
  - `VITE_JETSON_ROS_PORT`
- 동작
  - 브라우저에서 ROS 토픽 publish/subscribe

### 6. Jetson 비디오 스트림 HTTP
- 사용 위치: `RegisterYoloView.vue`, `FollowView.vue`
- 필요한 정보
  - `VITE_JETSON_IP`
  - `VITE_JETSON_VIDEO_PORT`

## 요청 항목별 확인 결과
- 소셜 인증: 현재 저장소 코드 기준 별도 OAuth/Social Login 연동 없음
- 포톤 클라우드(Photon Cloud): 현재 저장소 코드 기준 사용 흔적 없음
- 코드 컴파일 외부 서비스: 클라우드 빌드 서비스 연동 없음(로컬/장비 직접 빌드)
