-- 1. 데이터베이스 생성 및 선택
CREATE DATABASE IF NOT EXISTS SMART_CART CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE SMART_CART;

-- 2. 초기화 (기존 테이블 삭제 - FK 의존성 역순)
SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS location_paths; -- 경로 테이블 추가
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS carts;
DROP TABLE IF EXISTS coupons;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS locations;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS park_info;
SET FOREIGN_KEY_CHECKS = 1;

-- ==========================================
-- 3. 테이블 생성 (DDL)
-- ==========================================

-- (1) 회원 정보
CREATE TABLE users (
    user_id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '회원번호',
    user_name VARCHAR(50) NOT NULL COMMENT '회원명',
    login_id VARCHAR(50) NOT NULL UNIQUE COMMENT '로그인아이디',
    password VARCHAR(255) NOT NULL COMMENT '비밀번호(암호화 권장)',
    profile_image_url VARCHAR(255) COMMENT '프로필 이미지 URL',
    phone_number VARCHAR(20) COMMENT '전화번호',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '가입일'
);

-- (2) 카테고리 정보
CREATE TABLE categories (
    category_id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '카테고리 번호',
    category_name VARCHAR(50) NOT NULL COMMENT '카테고리명(식품, 생활용품 등)'
);

-- (3) 위치 정보
CREATE TABLE locations (
    location_id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '위치정보 아이디',
    location_code VARCHAR(20) NOT NULL UNIQUE COMMENT '위치 코드 (PARK-001)',
    category VARCHAR(20) NOT NULL COMMENT '장소 분류(주차장, 진열대 등)',
    pos_x DOUBLE NOT NULL COMMENT 'X 좌표',
    pos_y DOUBLE NOT NULL COMMENT 'Y 좌표'
);

-- (4) 경로 정보 - 다익스트라용 (추후 사용)
CREATE TABLE location_paths (
    path_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    start_node_id BIGINT NOT NULL,
    end_node_id BIGINT NOT NULL,
    distance DOUBLE NOT NULL COMMENT '거리 가중치',
    FOREIGN KEY (start_node_id) REFERENCES locations(location_id),
    FOREIGN KEY (end_node_id) REFERENCES locations(location_id)
);

-- (5) 상품 정보
CREATE TABLE products (
    product_id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '상품번호',
    category_id BIGINT NOT NULL COMMENT '카테고리 FK',
    location_id BIGINT NOT NULL COMMENT '진열 위치 FK',
    product_name VARCHAR(100) NOT NULL COMMENT '상품명',
    price INT NOT NULL COMMENT '상품가격',
    image_url VARCHAR(255) COMMENT '상품 이미지 URL',
    description TEXT COMMENT '상품설명',
    amount INT DEFAULT 0 COMMENT '재고수량',
    FOREIGN KEY (category_id) REFERENCES categories(category_id),
    FOREIGN KEY (location_id) REFERENCES locations(location_id)
);

-- (6) 쿠폰 정보
CREATE TABLE coupons (
    coupon_id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '쿠폰번호',
    user_id BIGINT NOT NULL COMMENT '소유 회원 FK',
    coupon_name VARCHAR(100) NOT NULL COMMENT '쿠폰명',
    discount_amount INT NOT NULL COMMENT '할인금액',
    is_used BOOLEAN DEFAULT FALSE COMMENT '사용여부',
    expire_date DATETIME COMMENT '유효기간',
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- (7) 카트 정보
CREATE TABLE carts (
    cart_id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '카트 번호(하드웨어 ID)',
    user_id BIGINT NULL COMMENT '사용 중인 회원(대기 시 NULL)',
    status VARCHAR(20) DEFAULT 'WAITING' COMMENT 'USED, WAITING, RETURN, ERROR',
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- (8) 주차 정보
CREATE TABLE park_info (
	park_info_id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '주차 정보 PK',
    location_id BIGINT NULL COMMENT '주차 위치 FK',
    car_number VARCHAR(20) NOT NULL COMMENT '차량 번호 (예: 123가4567)',
    entry_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '입차 시간',
    FOREIGN KEY (location_id) REFERENCES locations(location_id)
);

-- ==========================================
-- 아래 데이터들은 사용 안할수도 있음.
-- ==========================================

-- (9) 결제 내역 (Order)
CREATE TABLE orders (
    order_id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '주문 번호',
    user_id BIGINT NOT NULL COMMENT '사용자 FK',
    cart_id BIGINT NOT NULL COMMENT '사용 카트 FK',
    coupon_id BIGINT NULL COMMENT '사용 쿠폰 FK (NULL 허용)',
    total_price INT NOT NULL COMMENT '할인 전 총액',
    final_price INT NOT NULL COMMENT '최종 결제액',
    ordered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '결제 일시',
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (cart_id) REFERENCES carts(cart_id),
    FOREIGN KEY (coupon_id) REFERENCES coupons(coupon_id)
);

-- (10) 결제 상세 (Order Item)
CREATE TABLE order_items (
    ordered_item_id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '상세 ID',
    order_id BIGINT NOT NULL COMMENT '주문 번호 FK',
    product_id BIGINT NOT NULL COMMENT '구매 상품 FK',
    quantity INT NOT NULL COMMENT '수량',
    total_price INT NOT NULL COMMENT '총 가격(단가*수량)',
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);