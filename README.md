# 🚗 Connected Car Backend Application

커넥티드카 서비스의 백엔드 애플리케이션입니다. 사용자 인증, 차량 관리, 원격 제어 기능을 제공합니다.

## 📋 프로젝트 개요

실제 커넥티드카 앱서비스와 동일한 서비스를 구현하여 원격 시동, 문 잠금/해제, 차량 상태 확인, GPS 위치 추적 등의 기능을 제공합니다.

### 🎯 주요 기능

-   **사용자 관리**: 회원가입, 로그인, 세션 관리
-   **차량 등록**: VIN, 번호판 기반 차량 소유권 관리
-   **실시간 상태 조회**: 엔진, 도어, 연료, 배터리, 기후제어, 타이어압력, 주행거리, GPS
-   **원격 제어**: 시동, 도어, 에어컨/히터 제어
-   **보안**: 본인 소유 차량만 제어 가능

## 🏗️ 기술 스택

-   **Backend**: Python Flask 2.0.3
-   **Frontend**: HTML/CSS/Vanilla JavaScript
-   **Database**: MySQL 기반
-   **Python**: 3.6.15
-   **환경 관리**: micromamba (connected_car 환경)

## 📁 프로젝트 구조

```
BE/
├── controllers/           # API 라우트 핸들러
│   ├── auth_controller.py      # 인증 관련 API
│   ├── user_controller.py      # 사용자 관리 API
│   ├── vehicle_controller.py   # 차량 관리 API
│   └── vehicle_api_controller.py # 실시간 차량 상태 API
├── data/                 # 데이터 저장소 (백업용 JSON 파일들)
│   └── backup_json/           # 기존 JSON 파일 백업
├── templates/            # HTML 템플릿
│   ├── 1.html                # 메인 페이지
│   └── vehicles.html         # 차량 관리 페이지
├── utils/                # 유틸리티 함수
│   ├── auth.py               # 인증 헬퍼
│   └── database.py           # MySQL 데이터베이스 클래스들
├── app.py                # Flask 애플리케이션 진입점
├── requirements.txt      # Python 의존성
└── wsgi.py              # WSGI 설정
```

## 🔧 설치 및 실행

### 환경 설정

```bash
# micromamba 환경 활성화
micromamba activate connected_car

# 의존성 설치
micromamba run -n connected_car pip install -r requirements.txt
```

### 서버 실행

```bash
# Flask 개발 서버 (개발용)
micromamba run -n connected_car python app.py

# Uvicorn 서버 (프로덕션용)
micromamba run -n connected_car uvicorn wsgi:app --host 127.0.0.1 --port 8000 --reload
```

서버 실행 후 http://localhost:8000 에서 접속 가능합니다.

## 📚 API 명세

### 인증 API

| Method | Endpoint        | Description     |
| ------ | --------------- | --------------- |
| POST   | `/api/login`    | 사용자 로그인   |
| POST   | `/api/logout`   | 사용자 로그아웃 |
| POST   | `/api/register` | 사용자 회원가입 |

### 차량 관리 API

| Method | Endpoint                    | Description           |
| ------ | --------------------------- | --------------------- |
| GET    | `/api/cars`                 | 내 차량 목록 조회     |
| GET    | `/api/cars/available`       | 등록 가능한 차량 조회 |
| POST   | `/api/cars/register`        | 차량 등록             |
| GET    | `/api/car/{car_id}/status`  | 차량 상태 조회        |
| POST   | `/api/car/{car_id}/command` | 차량 원격 제어        |

### 실시간 차량 API

| Method | Endpoint                            | Description             |
| ------ | ----------------------------------- | ----------------------- |
| GET    | `/api/vehicle/{vehicle_id}/status`  | 실시간 차량 상태        |
| POST   | `/api/vehicle/{vehicle_id}/control` | 고급 차량 제어          |
| GET    | `/api/vehicles/status`              | 전체 차량 상태 (관제용) |

## 🔒 보안 특징

### 사용자 인증

-   세션 기반 인증 시스템
-   비밀번호 해싱 저장
-   세션 만료 관리 (1시간)

### 권한 관리

-   본인 소유 차량만 제어 가능
-   차량 소유권 검증
-   관리자 기능 분리 (별도 관리자 VM)

### 데이터 분리

-   **정적 데이터**: 차량 등록 정보, VIN, 번호판 (DB)
-   **동적 데이터**: 실시간 차량 상태 (외부 API)

## 🎨 주요 기능 상세

### 차량 상태 데이터

```json
{
  "engine_state": "off|on",
  "door_state": "locked|unlocked",
  "fuel": 75,
  "battery": 12.6,
  "voltage": "12V|400V|800V",
  "climate": {
    "ac_state": "off|on",
    "heater_state": "off|on",
    "target_temp": 22,
    "current_temp": 20,
    "fan_speed": 0-5,
    "auto_mode": true|false
  },
  "tire_pressure": {
    "front_left": 2.3,
    "front_right": 2.2,
    "rear_left": 2.4,
    "rear_right": 2.3,
    "recommended": 2.3,
    "unit": "bar",
    "warning_threshold": 1.8
  },
  "odometer": {
    "total_km": 15420,
    "trip_a_km": 523.7,
    "trip_b_km": 87.3
  },
  "location": {
    "lat": 37.5665,
    "lng": 126.978
  }
}
```

### 원격 제어 명령

-   `start_engine` / `stop_engine`: 시동 제어
-   `lock_door` / `unlock_door`: 도어 제어
-   `start_ac` / `stop_ac`: 에어컨 제어
-   `start_heater` / `stop_heater`: 히터 제어

## 🔗 연동 시스템

### car-api 서버 연동

-   실시간 차량 상태는 별도 car-api 서버에서 관리
-   HTTP API 통신으로 실시간 데이터 조회
-   Mock 데이터로 실제 차량 하드웨어 시뮬레이션

## 🚀 개발 환경

### 필수 요구사항

-   Python 3.6.15
-   micromamba 또는 conda
-   Flask 2.0.3

### 개발 도구

-   VS Code (권장)
-   Postman (API 테스트)
-   Git (버전 관리)

## 📝 개발 가이드

### 코딩 스타일

-   Python 파일에서는 `#` 주석만 사용
-   함수별 상세한 주석 작성
-   각 함수의 역할, 매개변수, 반환값 명시

### 새로운 기능 추가

1. `controllers/`에 라우트 핸들러 작성
2. `models/`에 데이터 모델 정의
3. `utils/`에 공통 함수 구현
4. `templates/`에 프론트엔드 구현

## 🐛 트러블슈팅

### 포트 충돌

-   8000번 포트가 사용 중인 경우 다른 포트 사용
-   `netstat -ano | findstr :8000`으로 포트 확인

### 환경 문제

-   micromamba 환경이 활성화되었는지 확인
-   `micromamba list`로 패키지 설치 상태 확인

## 📄 라이센스

이 프로젝트는 교육 및 모의해킹 연습 목적으로 개발되었습니다.

## 🤝 기여

버그 리포트나 기능 제안은 Issues를 통해 제출해 주세요.

---

**⚠️ 주의사항**: 이 애플리케이션은 침투테스트 목적의 의도적 취약점을 포함하고 있습니다. 실제 프로덕션 환경에서는 사용하지 마세요.
