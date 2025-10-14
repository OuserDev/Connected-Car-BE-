-- Connected Car Service Database Initialization Script
-- 작성일: 2024-01-15
-- 설명: 데이터베이스 및 테이블 생성, 샘플 데이터 삽입

-- 1. 데이터베이스 생성
CREATE DATABASE IF NOT EXISTS connected_car_service
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE connected_car_service;

-- 3. 테이블 생성

-- 3.1 사용자 테이블
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL COMMENT 'SHA-256 해시',
    email VARCHAR(100) NOT NULL,
    name VARCHAR(100),
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3.2 차량 스펙 테이블
CREATE TABLE vehicle_specs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    model VARCHAR(100) NOT NULL COMMENT '차량 모델명',
    category VARCHAR(50) COMMENT '차량 카테고리',
    segment VARCHAR(50) COMMENT '차량 세그먼트',
    engine_type VARCHAR(50) COMMENT '엔진 타입',
    displacement VARCHAR(50) COMMENT '배기량',
    power VARCHAR(50) COMMENT '최고 출력',
    torque VARCHAR(50) COMMENT '최대 토크',
    fuel_efficiency VARCHAR(50) COMMENT '연비',
    transmission VARCHAR(50) COMMENT '변속기',
    drive_type VARCHAR(50) COMMENT '구동 방식',
    voltage VARCHAR(50) COMMENT '전압 시스템',
    fuel_capacity VARCHAR(50) COMMENT '연료/배터리 용량',
    length VARCHAR(50) COMMENT '전장',
    width VARCHAR(50) COMMENT '전폭',
    height VARCHAR(50) COMMENT '전고',
    wheelbase VARCHAR(50) COMMENT '축거',
    weight VARCHAR(50) COMMENT '공차 중량',
    max_speed VARCHAR(50) COMMENT '최고 속도',
    acceleration VARCHAR(50) COMMENT '제로백',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3.3 등록 차량 테이블
CREATE TABLE cars (
    id INT AUTO_INCREMENT PRIMARY KEY,
    owner_id INT COMMENT '소유자 ID (NULL이면 미등록)',
    model_id INT COMMENT '차량 모델 ID',
    license_plate VARCHAR(20) UNIQUE COMMENT '차량 번호',
    vin VARCHAR(50) UNIQUE COMMENT '차대번호',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (model_id) REFERENCES vehicle_specs(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3.4 등록 카드 테이블
CREATE TABLE registered_cards (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    card_number VARCHAR(100) NOT NULL COMMENT '카드 번호 (마스킹)',
    card_name VARCHAR(100) COMMENT '카드 이름',
    expiry_date VARCHAR(10) COMMENT '유효기간',
    is_default BOOLEAN DEFAULT FALSE COMMENT '기본 카드 여부',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3.5 차량 제어 이력 테이블
CREATE TABLE car_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    car_id INT NOT NULL,
    action VARCHAR(100) NOT NULL COMMENT '수행된 작업',
    user_id INT COMMENT '작업 수행 사용자',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    details TEXT COMMENT '상세 정보',
    FOREIGN KEY (car_id) REFERENCES cars(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3.6 커뮤니티 테이블
CREATE TABLE community (
    id INT AUTO_INCREMENT PRIMARY KEY,
    type ENUM('notice', 'faq') NOT NULL DEFAULT 'notice' COMMENT '게시글 타입',
    title VARCHAR(255) NOT NULL COMMENT '제목',
    content TEXT NOT NULL COMMENT '내용',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. 샘플 데이터 삽입

-- 4.1 사용자 데이터 (비밀번호: SHA-256 해시)
INSERT INTO users (username, password, email, name, phone) VALUES
('admin', SHA2('admin123', 256), 'admin@connectedcar.com', '관리자', '010-1234-5678'),
('user1', SHA2('password1', 256), 'user1@example.com', '김철수', '010-1111-2222'),
('user2', SHA2('password2', 256), 'user2@example.com', '이영희', '010-2222-3333'),
('user3', SHA2('password3', 256), 'user3@example.com', '박민수', '010-3333-4444'),
('user4', SHA2('password4', 256), 'user4@example.com', '정수진', '010-4444-5555'),
('testuser', SHA2('test1234', 256), 'test@test.com', '테스트유저', '010-9999-8888');

-- 4.2 차량 스펙 데이터 (현대/기아 전기차 모델)
INSERT INTO vehicle_specs (model, category, segment, engine_type, displacement, power, torque, fuel_efficiency, transmission, drive_type, voltage, fuel_capacity, length, width, height, wheelbase, weight, max_speed, acceleration) VALUES
-- 현대 아이오닉 5
('IONIQ 5', 'Electric', 'Mid-size SUV', 'Electric', 'N/A', '225kW (306PS)', '605Nm', '5.1km/kWh', 'Single-speed', 'AWD', '800V', '77.4kWh', '4,635mm', '1,890mm', '1,605mm', '3,000mm', '2,130kg', '185km/h', '5.2sec'),

-- 현대 아이오닉 6
('IONIQ 6', 'Electric', 'Mid-size Sedan', 'Electric', 'N/A', '239kW (325PS)', '605Nm', '6.2km/kWh', 'Single-speed', 'AWD', '800V', '77.4kWh', '4,855mm', '1,880mm', '1,495mm', '2,950mm', '2,050kg', '185km/h', '5.1sec'),

-- 기아 EV6
('EV6', 'Electric', 'Mid-size SUV', 'Electric', 'N/A', '239kW (325PS)', '605Nm', '5.2km/kWh', 'Single-speed', 'AWD', '800V', '77.4kWh', '4,680mm', '1,880mm', '1,550mm', '2,900mm', '2,080kg', '185km/h', '5.2sec'),

-- 제네시스 GV60
('GV60', 'Electric', 'Luxury SUV', 'Electric', 'N/A', '240kW (326PS)', '605Nm', '4.9km/kWh', 'Single-speed', 'AWD', '800V', '77.4kWh', '4,515mm', '1,890mm', '1,580mm', '2,900mm', '2,155kg', '185km/h', '5.0sec'),

-- 현대 코나 일렉트릭
('KONA Electric', 'Electric', 'Compact SUV', 'Electric', 'N/A', '150kW (204PS)', '395Nm', '5.5km/kWh', 'Single-speed', 'FWD', '400V', '64kWh', '4,355mm', '1,825mm', '1,575mm', '2,660mm', '1,765kg', '167km/h', '7.6sec'),

-- 기아 니로 EV
('Niro EV', 'Electric', 'Compact SUV', 'Electric', 'N/A', '150kW (204PS)', '395Nm', '5.3km/kWh', 'Single-speed', 'FWD', '400V', '64.8kWh', '4,420mm', '1,825mm', '1,570mm', '2,720mm', '1,795kg', '167km/h', '7.8sec'),

-- 기아 EV9
('EV9', 'Electric', 'Large SUV', 'Electric', 'N/A', '283kW (385PS)', '700Nm', '4.5km/kWh', 'Single-speed', 'AWD', '800V', '99.8kWh', '5,010mm', '1,980mm', '1,780mm', '3,100mm', '2,650kg', '200km/h', '5.3sec'),

-- 제네시스 G80 전동화
('GENESIS G80 Electrified', 'Electric', 'Luxury Sedan', 'Electric', 'N/A', '272kW (370PS)', '700Nm', '4.3km/kWh', 'Single-speed', 'AWD', '400V', '87.2kWh', '4,995mm', '1,925mm', '1,465mm', '3,010mm', '2,310kg', '225km/h', '4.9sec'),

-- 현대 캐스퍼 일렉트릭
('Casper Electric', 'Electric', 'Mini SUV', 'Electric', 'N/A', '84kW (114PS)', '255Nm', '5.9km/kWh', 'Single-speed', 'FWD', '400V', '49kWh', '3,595mm', '1,595mm', '1,575mm', '2,400mm', '1,330kg', '145km/h', '10.5sec'),

-- 현대 아이오닉 5 N
('IONIQ 5 N', 'Electric', 'Performance SUV', 'Electric', 'N/A', '448kW (609PS)', '740Nm', '4.2km/kWh', 'Single-speed', 'AWD', '800V', '84kWh', '4,715mm', '1,940mm', '1,585mm', '3,000mm', '2,235kg', '260km/h', '3.4sec');

-- 4.3 등록 차량 데이터
INSERT INTO cars (owner_id, model_id, license_plate, vin) VALUES
-- user1(김철수) 소유 차량
(2, 1, '12가3456', 'KMHFG4JG5MU123456'),  -- IONIQ 5
(2, 5, '34나5678', 'KNDC1A51XN7234567'),  -- KONA Electric

-- user2(이영희) 소유 차량
(3, 3, '56다7890', 'KNDP3AA39R7345678'),  -- EV6

-- user3(박민수) 소유 차량
(4, 2, '78라1234', 'KMHFG4JG7MU456789'),  -- IONIQ 6

-- user4(정수진) 소유 차량
(5, 4, '90마5678', 'KMHH381CANA567890'),  -- GV60

-- 미등록 차량 (owner_id = NULL)
(NULL, 6, '11바2233', 'KNDC2D51XN7678901'),  -- Niro EV
(NULL, 7, '22사4455', 'KMHG381CANA789012');  -- EV9

-- 4.4 커뮤니티 게시글 데이터
INSERT INTO community (type, title, content) VALUES
-- 공지사항
('notice', '시스템 점검 안내', '2024년 1월 15일 02:00~06:00 사이에 시스템 점검이 예정되어 있습니다. 점검 시간 동안 일부 서비스 이용이 제한될 수 있습니다.'),
('notice', '새로운 기능 추가', '차량 원격 제어 기능이 업데이트되었습니다. 이제 스마트폰에서 차량 상태를 실시간으로 확인하고 원격으로 시동, 문 잠금/해제, 에어컨 제어가 가능합니다.'),

-- FAQ
('faq', '로그인이 안 돼요', '비밀번호를 잊으셨다면 로그인 화면에서 "비밀번호 재설정"을 이용해주세요. 아이디를 잊으신 경우 고객센터(1588-1234)로 문의하시기 바랍니다.'),
('faq', '차량 등록 방법', '차량 등록은 다음 순서로 진행됩니다: 1) 마이페이지 접속 2) "차량 관리" 메뉴 선택 3) "차량 등록" 버튼 클릭 4) 차량번호와 차대번호(VIN) 입력 5) 등록 완료');

-- 5. 데이터 확인
SELECT '=== 사용자 목록 ===' AS '';
SELECT id, username, email, name, phone FROM users;

SELECT '=== 차량 스펙 목록 ===' AS '';
SELECT id, model, category, engine_type, voltage, power FROM vehicle_specs;

SELECT '=== 등록 차량 목록 ===' AS '';
SELECT c.id, c.license_plate, u.name AS owner_name, vs.model AS model_name
FROM cars c
LEFT JOIN users u ON c.owner_id = u.id
LEFT JOIN vehicle_specs vs ON c.model_id = vs.id;

SELECT '=== 커뮤니티 게시글 ===' AS '';
SELECT id, type, title FROM community;

SELECT '=== 데이터베이스 초기화 완료 ===' AS '';
SELECT
    (SELECT COUNT(*) FROM users) AS users_count,
    (SELECT COUNT(*) FROM vehicle_specs) AS vehicle_specs_count,
    (SELECT COUNT(*) FROM cars) AS cars_count,
    (SELECT COUNT(*) FROM community) AS community_count;
