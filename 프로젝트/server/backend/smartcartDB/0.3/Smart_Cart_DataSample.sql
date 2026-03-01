-- ==========================================
-- 데이터 입력 (DML) - 이미지 경로 수정됨
-- ==========================================
USE SMART_CART;
-- [1] 회원
INSERT INTO users (user_name, login_id, password, phone_number) VALUES 
('테스트유저', 'test', 'scrypt:32768:8:1$ZpGs6rTpKeQiVwIQ$cb602fc46b9eebc85e63c5ea0d10737bee0a3a118d938efcb78becda6a918c60a4ce34b632f08f0307e8d2462bcf323b40fe4e9ff112e0a4b146b31733761a8e', '010-1234-5678');

-- [2] 카테고리
INSERT INTO categories (category_name) VALUES 
('식품'), ('생활용품'), ('문구완구'), ('패션'), ('디지털');

-- [3] 위치 정보 (Nav2 Waypoint Test Optimized)

-- 1. 주차장
INSERT INTO locations (location_code, category, pos_x, pos_y) VALUES 

-- 1. 출입구 & 카트 보관소
('GATE-001', '출입구',  1.650,   0.51),  -- 상단 출입구
('GATE-002', '출입구',  1.650,  -1.56),  -- 하단 출입구
('STOR-001', '카트보관함', 1.400, 1.46),  -- 카트 보관함

-- 2. 매장 진열 (로봇 정차 위치)
('SHELF-001', '진열대', -0.245,  1.60),  -- 상단 중앙
('SHELF-002', '진열대', -0.245, -1.55),  -- 하단 중앙
('SHELF-003', '진열대', -1.295,  0.83),  -- 상단 좌측
('SHELF-004', '진열대', -0.245,  0.83),  -- 상단 중앙
('SHELF-005', '진열대',  0.800,  0.83),  -- 상단 우측
('SHELF-006', '진열대', -1.295, -0.77),  -- 하단 좌측
('SHELF-007', '진열대', -0.245, -0.77),  -- 하단 중앙
('SHELF-008', '진열대',  0.800, -0.77),  -- 하단 우측

-- 4. 코너 / 일반 경로 (Waypoints)
('PTH-001', '센터', -0.245,  0.03),  -- 맵 정중앙
('PTH-002', '코너', -1.295,  1.60),  -- 좌상단 코너
('PTH-003', '코너',  0.800,  1.60),  -- 우상단 코너
('PTH-004', '코너', -1.295, -1.55),  -- 좌하단 코너
('PTH-005', '코너',  0.800, -1.55),  -- 우하단 코너
('PTH-006', '코너', -1.295,  0.03),  -- 중앙 좌측
('PTH-007', '코너',  0.800,  0.03),  -- 중앙 우측
('PTH-008', '코너',  1.400,  0.51),  -- 상단 출입구 진입점
('PTH-009', '코너',  1.400, -1.56),  -- 하단 출입구 진입점

-- 4. 주차장 (우측 Red Box 공간: X=2.25 라인 정렬)
('PARK-001', '주차장',  2.250,  0.50),  -- 주차 1 (위쪽 문 높이)
('PARK-002', '주차장',  2.250, -0.20),  -- 주차 2
('PARK-003', '주차장',  2.250, -0.90),  -- 주차 3
('PARK-004', '주차장',  2.250, -1.60);  -- 주차 4 (아래쪽 문 높이)

-- [4] 상품 데이터 (경로: /카테고리명/상품명.jpg)

-- 1. 식품 (상단 선반 3개 꽉 채움: ID 6, 7, 8)
-- 1-1. 가공/스낵 (좌측: ID 6)
INSERT INTO products (category_id, location_id, product_name, price, image_url, description) VALUES
(1, 6, 'CJ 햇반 210g', 1500, '/식품/CJ 햇반 210g.webp', '갓 지은 밥맛 그대로'),
(1, 6, '농심 새우깡', 1200, '/식품/농심 새우깡.webp', '손이 가요 손이 가'),
(1, 6, '농심 신라면 5입', 4500, '/식품/농심 신라면 5입.webp', '사나이 울리는 매운맛'),
(1, 6, '동원 참치캔', 2500, '/식품/동원 참치캔.webp', 'DHA가 풍부한 참치'),
(1, 6, '비비고 왕교자', 9000, '/식품/비비고 왕교자.webp', '속이 꽉 찬 왕만두'),
(1, 6, '스팸 클래식', 5500, '/식품/스팸 클래식.webp', '따끈한 밥에 스팸 한 조각'),
(1, 6, '오뚜기 3분 카레', 1800, '/식품/오뚜기 3분 카레.webp', '데우기만 하면 끝'),
(1, 6, '오뚜기 진라면 매운맛 컵', 1100, '/식품/오뚜기 진라면 매운맛.webp', '쫄깃한 면발'),
(1, 6, '포카칩 오리지널', 1500, '/식품/포카칩 오리지널.webp', '생감자의 풍미'),
(1, 6, '해찬들 쌈장', 4500, '/식품/해찬들 쌈장.webp', '고기 먹을 때 필수'),
(1, 13, '광천 파래김 16봉', 5500, '/식품/광천 파래김 16봉.webp', '바삭하고 고소한 밥도둑'),		-- 실제 사용
(1, 13, '현미녹차 50티백', 4000, '/식품/현미녹차 50티백.webp', '구수한 풍미의 깔끔한 차'); 		-- 실제 사용

-- 1-2. 신선/유제품 (중앙: ID 7)
INSERT INTO products (category_id, location_id, product_name, price, image_url, description) VALUES
(1, 7, '계란 30구', 8900, '/식품/계란 30구.webp', '신선한 특란 30구'),
(1, 7, '국내산 삼겹살 생고기', 15000, '/식품/국내산 삼겹살 생고기.webp', '육즙 가득 한돈'),
(1, 7, '빙그레 바나나 우유', 1400, '/식품/빙그레 바나나우유.webp', '달콤한 뚱바'),
(1, 7, '서울우유 1L', 2800, '/식품/서울우유 1L.webp', '신선함이 살아있는 우유'),
(1, 7, '신선한 상추', 1500, '/식품/신선한 상추.webp', '아삭아삭한 식감');

-- 1-3. 음료/주류 (우측: ID 8)
INSERT INTO products (category_id, location_id, product_name, price, image_url, description) VALUES
(1, 8, '삼다수 2L', 1000, '/식품/삼다수 2L.webp', '제주 화산 암반수'),
(1, 8, '참이슬 후레쉬', 1300, '/식품/참이슬 후레쉬.webp', '깨끗한 아침'),
(1, 8, '칠성 사이다 1.5L', 2500, '/식품/칠성사이다 1.5L.webp', '맑고 깨끗한 맛'),
(1, 8, '카스 맥주 캔', 2000, '/식품/카스 맥주 캔.webp', '톡 쏘는 청량감'),
(1, 8, '코카콜라 1.5L', 2800, '/식품/코카콜라 1.5L.webp', '오리지널의 짜릿함');

-- 2. 생활용품 (하단 좌측: ID 9)
INSERT INTO products (category_id, location_id, product_name, price, image_url, description) VALUES
(2, 9, '고무장갑', 2000, '/생활용품/고무장갑.webp', '내구성 좋은 고무장갑'),
(2, 9, '다우니 섬유유연제', 8500, '/생활용품/다우니 섬유유연제.webp', '오래가는 향기'),
(2, 9, '물티슈 100매', 1500, '/생활용품/물티슈 100매.webp', '도톰한 엠보싱'),
(2, 9, '주방세제 퐁퐁', 3500, '/생활용품/주방세제 퐁퐁.webp', '기름기 제거 탁월'),
(2, 9, '지퍼백', 2500, '/생활용품/지퍼백.webp', '신선 보관의 필수품'),					-- 실제 사용
(2, 9, '칫솔 세트', 4000, '/생활용품/칫솔 세트.webp', '미세모 4개입'),
(2, 5, '크리넥스 두루마리 휴지', 18000, '/생활용품/크리넥스 두루마리 휴지.webp', '부드러운 3겹'),		-- 실제 사용
(2, 9, '페리오 치약', 1200, '/생활용품/페리오 치약.webp', '상쾌한 구강 관리'),
(2, 14, '일회용 나무젓가락 50입', 2500, '/생활용품/일회용 나무젓가락 50입.webp', '캠핑 및 배달용 필수 아이템');		-- 실제 사용

-- 3. 문구완구 (하단 중앙 선반: ID 10)
INSERT INTO products (category_id, location_id, product_name, price, image_url, description) VALUES
(3, 10, '둥근 가위', 1000, '/문구완구/둥근 가위.webp', '안전한 어린이 가위'),
(3, 10, '모나미 볼펜', 500, '/문구완구/모나미 볼펜.webp', '국민 볼펜 153'),
(3, 10, '미니 레고 자동차', 9900, '/문구완구/미니 레고 자동차.webp', '조립하는 재미'),
(3, 10, '뽀로로 색연필', 4500, '/문구완구/뽀로로 색연필.webp', '부드러운 12색'),
(3, 10, '스케치북 8절', 1500, '/문구완구/스케치북 8절.webp', '그림 그리기 좋은 종이'),
(3, 10, '아모스 딱풀', 800, '/문구완구/아모스 딱풀.webp', '강력한 접착력'),
(3, 10, '캐릭터 필통', 5000, '/문구완구/캐릭터 필통.webp', '귀여운 캐릭터 디자인'),
(3, 10, '클레이 점토', 3000, '/문구완구/클레이 점토.webp', '말랑말랑 창의력 쑥쑥');

-- 4. 패션 (하단 우측 선반: ID 11) - 디지털 이사 가서 혼자 씁니다!
INSERT INTO products (category_id, location_id, product_name, price, image_url, description) VALUES
(4, 11, '남성 기본 반팔티', 9900, '/패션/남성 기본 반팔티.webp', '면 100% 데일리룩'),
(4, 11, '남성 런닝구', 5000, '/패션/남성 런닝구.webp', '시원한 이너웨어'),
(4, 11, '삼선 슬리퍼', 3500, '/패션/삼선 슬리퍼.webp', '편안한 착용감'),
(4, 11, '스포츠 양말', 2000, '/패션/스포츠 양말.webp', '도톰한 바닥 쿠션'),
(4, 11, '여성 수면바지', 7900, '/패션/여성 수면바지.webp', '보들보들 꿀잠 예약'),
(4, 11, '일회용 우비', 1000, '/패션/일회용 우비.webp', '비 오는 날 필수템');

-- 5. 디지털 (하단 중앙 벽면: ID 5) - *여기로 이사 완료!*
INSERT INTO products (category_id, location_id, product_name, price, image_url, description) VALUES
(5, 5, 'AA 건전지', 2000, '/디지털/AA 건전지.webp', '오래가는 파워'),
(5, 5, 'AAA 건전지', 2000, '/디지털/AAA 건전지.webp', '리모컨용 건전지'),
(5, 5, 'C타입 충전 케이블', 4500, '/디지털/C타입 충전 케이블.webp', '고속 충전 지원'),
(5, 5, '삼성 이어폰', 15000, '/디지털/삼성 이어폰.webp', '맑은 음질'),
(5, 5, '휴대용 선풍기', 12000, '/디지털/휴대용 선풍기.webp', '여름 필수품');

-- [5] 쿠폰
INSERT INTO coupons (user_id, coupon_name, discount_amount, expire_date) VALUES 
(1, '신규가입 2000원 쿠폰', 2000, '2026-03-03 23:59:59');
INSERT INTO coupons (user_id, coupon_name, discount_amount, expire_date, is_used)
VALUES (1, '2026 상반기 깜짝 할인 쿠폰', 5000, '2026-06-30 23:59:59', 0);

-- [6] 카트
-- cart_id는 1, 2, 3으로 자동 생성되며, 모두 대기 상태(WAITING)로 시작합니다.
INSERT INTO carts (status) VALUES 
('WAITING'),
('WAITING'),
('WAITING');

-- [7] 주차정보
-- 차량 번호는 문자열(VARCHAR)이며, 입차 시간은 현재 시간 기준 랜덤하게 설정
INSERT INTO park_info (location_id, car_number, entry_time) VALUES
((SELECT location_id FROM locations WHERE location_code='PARK-001'), '12가 3456', DATE_SUB(NOW(), INTERVAL 30 MINUTE)),
((SELECT location_id FROM locations WHERE location_code='PARK-002'), '34나 5678', DATE_SUB(NOW(), INTERVAL 30 MINUTE)),
((SELECT location_id FROM locations WHERE location_code='PARK-003'), '서울 30바 1234', DATE_SUB(NOW(), INTERVAL 1 HOUR)),
((SELECT location_id FROM locations WHERE location_code='PARK-004'), '99허 9999', DATE_SUB(NOW(), INTERVAL 120 MINUTE));

-- 최종 확인
SELECT product_id, category_name, product_name, image_url, location_code 
FROM products 
JOIN categories ON products.category_id = categories.category_id
JOIN locations ON products.location_id = locations.location_id;

SELECT * from locations;
