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

-- [3] 위치 정보
INSERT INTO locations (location_code, category, pos_x, pos_y) VALUES 
('PARK-001', '주차장', 0.0, 0.0),      -- ID 1
('PARK-002', '주차장', 0.0, 1.5),      -- ID 2
('PARK-003', '주차장', 0.0, 3.0),
('PARK-004', '주차장', 0.0, 4.5),
('PARK-005', '주차장', 0.0, 6.0),
('PARK-006', '주차장', 0.0, 7.5),
('PARK-007', '주차장', 0.0, 9.0),
('PARK-008', '주차장', 0.0, 10.5),
('PARK-009', '주차장', 0.0, 12.0),
('PARK-010', '주차장', 0.0, 13.5),     -- ID 10
('GATE-001', '출입구', 2.0, 0.0),      -- ID 11
('STOR-001', '카트보관함', 1.0, 0.0),   -- ID 12
('SHELF-F01', '진열대', 5.0, 5.0),     -- ID 13 (식품)
('SHELF-L01', '진열대', 10.0, 5.0),    -- ID 14 (생활)
('SHELF-T01', '진열대', 15.0, 5.0),    -- ID 15 (문구)
('SHELF-C01', '진열대', 20.0, 5.0),    -- ID 16 (패션)
('SHELF-D01', '진열대', 25.0, 5.0);    -- ID 17 (디지털)

-- [4] 상품 데이터 (경로: /카테고리명/상품명.jpg)

-- 1. 식품 (category_id: 1, location_id: 4)
INSERT INTO products (category_id, location_id, product_name, price, image_url, description) VALUES
(1, 13, 'CJ 햇반 210g', 1500, '/식품/CJ 햇반 210g.webp', '갓 지은 밥맛 그대로'),
(1, 13, '계란 30구', 8900, '/식품/계란 30구.webp', '신선한 특란 30구'),
(1, 13, '국내산 삼겹살 생고기', 15000, '/식품/국내산 삼겹살 생고기.webp', '육즙 가득 한돈'),
(1, 13, '농심 새우깡', 1200, '/식품/농심 새우깡.webp', '손이 가요 손이 가'),
(1, 13, '농심 신라면 5입', 4500, '/식품/농심 신라면 5입.webp', '사나이 울리는 매운맛'),
(1, 13, '동원 참치캔', 2500, '/식품/동원 참치캔.webp', 'DHA가 풍부한 참치'),
(1, 13, '비비고 왕교자', 9000, '/식품/비비고 왕교자.webp', '속이 꽉 찬 왕만두'),
(1, 13, '빙그레 바나나 우유', 1400, '/식품/빙그레 바나나우유.webp', '달콤한 뚱바'),
(1, 13, '삼다수 2L', 1000, '/식품/삼다수 2L.webp', '제주 화산 암반수'),
(1, 13, '서울우유 1L', 2800, '/식품/서울우유 1L.webp', '신선함이 살아있는 우유'),
(1, 13, '스팸 클래식', 5500, '/식품/스팸 클래식.webp', '따끈한 밥에 스팸 한 조각'),
(1, 13, '신선한 상추', 1500, '/식품/신선한 상추.webp', '아삭아삭한 식감'),
(1, 13, '오뚜기 3분 카레', 1800, '/식품/오뚜기 3분 카레.webp', '데우기만 하면 끝'),
(1, 13, '오뚜기 진라면 매운맛 컵', 1100, '/식품/오뚜기 진라면 매운맛.webp', '쫄깃한 면발'),
(1, 13, '참이슬 후레쉬', 1300, '/식품/참이슬 후레쉬.webp', '깨끗한 아침'),
(1, 13, '칠성 사이다 1.5L', 2500, '/식품/칠성사이다 1.5L.webp', '맑고 깨끗한 맛'),
(1, 13, '카스 맥주 캔', 2000, '/식품/카스 맥주 캔.webp', '톡 쏘는 청량감'),
(1, 13, '코카콜라 1.5L', 2800, '/식품/코카콜라 1.5L.webp', '오리지널의 짜릿함'),
(1, 13, '포카칩 오리지널', 1500, '/식품/포카칩 오리지널.webp', '생감자의 풍미'),
(1, 13, '해찬들 쌈장', 4500, '/식품/해찬들 쌈장.webp', '고기 먹을 때 필수');

-- 2. 생활용품 (category_id: 2, location_id: 14)
INSERT INTO products (category_id, location_id, product_name, price, image_url, description) VALUES
(2, 14, '고무장갑', 2000, '/생활용품/고무장갑.webp', '내구성 좋은 고무장갑'),
(2, 14, '다우니 섬유유연제', 8500, '/생활용품/다우니 섬유유연제.webp', '오래가는 향기'),
(2, 14, '물티슈 100매', 1500, '/생활용품/물티슈 100매.webp', '도톰한 엠보싱'),
(2, 14, '주방세제 퐁퐁', 3500, '/생활용품/주방세제 퐁퐁.webp', '기름기 제거 탁월'),
(2, 14, '지퍼백', 2500, '/생활용품/지퍼백.webp', '신선 보관의 필수품'),
(2, 14, '칫솔 세트', 4000, '/생활용품/칫솔 세트.webp', '미세모 4개입'),
(2, 14, '크리넥스 두루마리 휴지', 18000, '/생활용품/크리넥스 두루마리 휴지.webp', '부드러운 3겹'),
(2, 14, '페리오 치약', 1200, '/생활용품/페리오 치약.webp', '상쾌한 구강 관리');

-- 3. 문구완구 (category_id: 3, location_id: 15)
INSERT INTO products (category_id, location_id, product_name, price, image_url, description) VALUES
(3, 15, '둥근 가위', 1000, '/문구완구/둥근 가위.webp', '안전한 어린이 가위'),
(3, 15, '모나미 볼펜', 500, '/문구완구/모나미 볼펜.webp', '국민 볼펜 153'),
(3, 15, '미니 레고 자동차', 9900, '/문구완구/미니 레고 자동차.webp', '조립하는 재미'),
(3, 15, '뽀로로 색연필', 4500, '/문구완구/뽀로로 색연필.webp', '부드러운 12색'),
(3, 15, '스케치북 8절', 1500, '/문구완구/스케치북 8절.webp', '그림 그리기 좋은 종이'),
(3, 15, '아모스 딱풀', 800, '/문구완구/아모스 딱풀.webp', '강력한 접착력'),
(3, 15, '캐릭터 필통', 5000, '/문구완구/캐릭터 필통.webp', '귀여운 캐릭터 디자인'),
(3, 15, '클레이 점토', 3000, '/문구완구/클레이 점토.webp', '말랑말랑 창의력 쑥쑥');

-- 4. 패션 (category_id: 4, location_id: 16)
INSERT INTO products (category_id, location_id, product_name, price, image_url, description) VALUES
(4, 16, '남성 기본 반팔티', 9900, '/패션/남성 기본 반팔티.webp', '면 100% 데일리룩'),
(4, 16, '남성 런닝구', 5000, '/패션/남성 런닝구.webp', '시원한 이너웨어'),
(4, 16, '삼선 슬리퍼', 3500, '/패션/삼선 슬리퍼.webp', '편안한 착용감'),
(4, 16, '스포츠 양말', 2000, '/패션/스포츠 양말.webp', '도톰한 바닥 쿠션'),
(4, 16, '여성 수면바지', 7900, '/패션/여성 수면바지.webp', '보들보들 꿀잠 예약'),
(4, 16, '일회용 우비', 1000, '/패션/일회용 우비.webp', '비 오는 날 필수템');

-- 5. 디지털 (category_id: 5, location_id: 17)
INSERT INTO products (category_id, location_id, product_name, price, image_url, description) VALUES
(5, 17, 'AA 건전지', 2000, '/디지털/AA 건전지.webp', '오래가는 파워'),
(5, 17, 'AAA 건전지', 2000, '/디지털/AAA 건전지.webp', '리모컨용 건전지'),
(5, 17, 'C타입 충전 케이블', 4500, '/디지털/C타입 충전 케이블.webp', '고속 충전 지원'),
(5, 17, '삼성 이어폰', 15000, '/디지털/삼성 이어폰.webp', '맑은 음질'),
(5, 17, '휴대용 선풍기', 12000, '/디지털/휴대용 선풍기.webp', '여름 필수품');

-- [5] 쿠폰
INSERT INTO coupons (user_id, coupon_name, discount_amount, expire_date) VALUES 
(1, '신규가입 2000원 쿠폰', 2000, '2025-12-31 23:59:59');
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
((SELECT location_id FROM locations WHERE location_code='PARK-001'), '12가 3456', NOW()),
((SELECT location_id FROM locations WHERE location_code='PARK-002'), '34나 5678', DATE_SUB(NOW(), INTERVAL 30 MINUTE)),
((SELECT location_id FROM locations WHERE location_code='PARK-003'), '서울 30바 1234', DATE_SUB(NOW(), INTERVAL 1 HOUR)),
((SELECT location_id FROM locations WHERE location_code='PARK-004'), '99허 9999', DATE_SUB(NOW(), INTERVAL 120 MINUTE)),
((SELECT location_id FROM locations WHERE location_code='PARK-005'), '56오 0707', DATE_SUB(NOW(), INTERVAL 15 MINUTE)),
((SELECT location_id FROM locations WHERE location_code='PARK-006'), '28구 8282', DATE_SUB(NOW(), INTERVAL 1 DAY)),
((SELECT location_id FROM locations WHERE location_code='PARK-007'), '19서 1919', DATE_SUB(NOW(), INTERVAL 45 MINUTE)),
((SELECT location_id FROM locations WHERE location_code='PARK-008'), '88하 1004', DATE_SUB(NOW(), INTERVAL 210 MINUTE)),
((SELECT location_id FROM locations WHERE location_code='PARK-009'), '52가 3355', DATE_SUB(NOW(), INTERVAL 5 MINUTE)),
((SELECT location_id FROM locations WHERE location_code='PARK-010'), '01우 0101', DATE_SUB(NOW(), INTERVAL 10 MINUTE));


-- 1. 식품 (category_id: 1, location_id: 13)
INSERT INTO products (category_id, location_id, product_name, price, image_url, description) VALUES
(1, 13, '광천 파래김 16봉', 5500, '/식품/광천 파래김 16봉.webp', '바삭하고 고소한 밥도둑'),
(1, 13, '현미녹차 50티백', 4000, '/식품/현미녹차 50티백.webp', '구수한 풍미의 깔끔한 차');

-- 2. 생활용품 (category_id: 2, location_id: 14)
INSERT INTO products (category_id, location_id, product_name, price, image_url, description) VALUES
(2, 14, '일회용 나무젓가락 50입', 2500, '/생활용품/일회용 나무젓가락 50입.webp', '캠핑 및 배달용 필수 아이템');

-- 최종 확인
SELECT product_id, category_name, product_name, image_url, location_code 
FROM products 
JOIN categories ON products.category_id = categories.category_id
JOIN locations ON products.location_id = locations.location_id;