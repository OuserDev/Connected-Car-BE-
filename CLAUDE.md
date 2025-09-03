# Connected-Car Service 침투테스트 랩

## 🚗 핵심 목표: 실제 커넥티드카 앱서비스와 동일한 서비스 구현
**이 프로젝트의 최우선 목표는 실제 커넥티드카 앱서비스(현대/기아 블루링크, 테슬라 앱 등)와 매우 유사한 완전한 서비스를 구현하는 것입니다.**

- **실제 커넥티드카 기능 구현**: 원격 시동, 문 잠금/해제, 차량 상태 확인, GPS 위치 추적 등
- **완전한 사용자 경험**: 회원가입/로그인, 차량 등록, 소유권 관리, 실시간 제어
- **실무급 웹서비스**: 프론트엔드-백엔드-데이터베이스 완전 분리, RESTful API 설계
- **보안 취약점 포함**: 침투테스트 목적의 의도적 취약점 내재

## 프로젝트 개요
실제와 동일한 네트워크 환경에서 Connected-Car Service의 보안 취약점을 분석하고 침투테스트를 수행하는 랩

**대상:** 관리자, 보안담당자, 침투테스터, 해커 (IT보안 20년 1급)

## 프로젝트 구조
1. 실제 차량과 유사한 커넥티드카 서비스 구현
2. 각종 보안설정, 인증 및 Connected-Car Service의 보안 취약점 분석 환경 제공
3. 침투 테스트에 필요한 다양한 시나리오와 취약점 환경 제공
4. 실 침투테스트 시나리오 및 대응 방법, 모의해킹 실습

## 시스템 구성요소

### VM 구성 (총 6개)
- **pfSense VM:** 방화벽/라우팅
- **웹서버 VM:** 커넥티드카 웹 서비스 (Flask + VanillaJS)
- **DB서버 VM:** 사용자/차량 정보 저장 (MySQL)
- **공격자 VM:** 취약점 스캔도구 시스템
- **차량API VM:** 차량 제어 API 시스템

### 네트워크 구성 (6개 세그먼트)
- pfSense 방화벽: WAN 세그먼트
- ExterServers: 취약 웹서비스가 세그먼트
- InterServers: 내부 시스템 (관리자용 웹서버, 관리용 PC)의 세그먼트
- DBServers: 내부 DB의 세그먼트
- APIServers: 내부 API의 세그먼트

## 기술 스택
- **Backend:** Python Flask
- **Frontend:** HTML/CSS/Vanilla JavaScript
- **Database:** MySQL
- **Network:** pfSense, VMware Workstation
- **침투테스트:** Kali Linux

## 구현 기능

### 1. 웹서비스 구현
- **1-1. 사용자 관리 (인증 시스템)**
- **1-2. 차량 관리**
  - 차량 등록/삭제, 원격시동/끄기, 잠금, 위치 각종 정보
- **1-3. 차량 제어**
  - 실시간 제어, 상태값 모니터링, 원격 제어, 긴급상황 대응 기능, 차량 위치 기능
- **1-4. 관리 기능**
  - 로그 수집, 통계 제공

**중요: 차량 데이터 Mock**
- 차량 API는 JSON 형태로 제공
- 실 차량 연동 대신 모의 정보를 제공하여
- "실시간 관제", "원격 제어" 등 실 상황과 유사한 경험 제공

### 2. 취약점 시스템 (침투 테스트 환경)
- **2-1. 웹 차량 스캔도구**
- **2-2. 사용자 권한 상승**
- **2-3. 시스템 침투 취약점**

## 실습 과정
1. **환경 구축**
   - 웹 서비스 구현
   - 네트워크 세그먼테이션 및 환경 구축
2. **취약점 진단**
   - KISA 가이드라인에 따른 기본 취약점 진단 및 분석 과정
3. **침투테스트 실습**
   - 실 취약점을 통한 실제 시나리오 기반 침투테스트 실습
4. **대응 방안 수립**
   - 취약점 패치, 대응 방안, 대응 및 모니터링 방안 수립

## 기타 고려사항
- 모든 차량과 유사한 구성요소 시뮬레이션 환경 제공
- 커넥티드카 통신 서비스 차량 연결 및 유사한 보안 환경 제공

## 네트워크 다이어그램 참고 (Untitled Diagram.drawio.png)
**Internal Network 구조:**
- **Public subnet:**
  - 대고객 웹서비스 (Customer Web Service)
- **Private subnet:**
  - 관리자용 웹서비스 (Administrator Web Service)
  - MySQL DB
  - 차량 API 서버 (Vehicle API Server)
- **pfSense Firewall:** Web 트래픽을 Internal Network로 연결

## 개발 환경 설정

### Python 환경
- **micromamba 환경:** connected_car
- **Python 버전:** 3.6.15
- **Flask 버전:** 2.0.3 (현대적이고 안정적인 버전 - 실제 커넥티드카 서비스와 동일한 수준)

### 환경 실행 방법
```bash
# 환경 활성화 후 실행
micromamba run -n connected_car python app.py

# 또는 환경 활성화 후
micromamba activate connected_car
python app.py
```

### 개발 환경 정보
- Flask 2.0.3는 최신 보안 패치가 적용된 안정적인 버전
- Debug 모드 활성화로 개발 편의성 제공 (운영 환경에서는 비활성화 필요)
- 서버 실행: http://0.0.0.0:8000 (모든 인터페이스에서 접근 가능)
- 현대적인 Flask 기능 활용: 향상된 세션 관리, JSON 처리, 보안 설정

### Claude 작업 시 주의사항
- **포트 체크 필수**: API 테스트나 디버깅 전에 반드시 8000번 포트가 사용 중인지 확인
- 사용자가 별도로 `python app.py` 실행 중일 수 있으므로, 포트 충돌 방지 필요
- 디버깅이 필요한 경우에만 서버 재시작
- **Bash 도구 자동 승인**: `start http://localhost:8000/test` 같은 브라우저 명령에 대해 항상 자동 Yes 처리

## 네트워크 토폴로지

### 토폴로지 개요
인터넷 → pfSense 방화벽 → (격리된) Public Subnet의 대고객 웹서비스, Private Subnet의 관리자용 웹서비스·차량 API 서버·MySQL DB로 구성된 2계층 내부망 구조

### 핵심 구성 요소

#### 경계(Perimeter)
- **pfSense 방화벽**: 외부 트래픽 수용/차단, NAT·포트포워딩·VPN 담당

#### 네트워크 영역
- **Public Subnet**: 대고객 웹서비스 (공개 엔드포인트 보유)
- **Private Subnet**: 관리자용 웹서비스, 차량 API 서버, MySQL DB (비공개, 내부통신 전용)
- **신뢰 구역**: Public < Private (Private가 더 높은 신뢰/제한적 접근)

#### 네트워크 상세 구성
```yaml
topology:
  edge:
    firewall: pfSense
    exposes:
      - service: public-web
        subnet: public
        ports: [80, 443]
  subnets:
    - name: public
      cidr: "PUBLIC_CIDR"
      nodes:
        - id: public-web
          role: web-frontend
          exposure: internet-facing
    - name: private
      cidr: "PRIVATE_CIDR"
      nodes:
        - id: admin-web
          role: web-admin
          exposure: internal-only
        - id: vehicle-api
          role: app-api
          exposure: internal-only
        - id: mysql-db
          role: database
          engine: mysql
          port: 3306
  allowed_flows:
    - src: internet
      dst: public-web
      proto: tcp
      ports: [80, 443]
      via: pfSense
    - src: admin-vpn
      dst: [admin-web, vehicle-api, mysql-db]
      proto: tcp
      ports: "as-needed"
      via: pfSense-vpn
    - src: admin-web
      dst: [vehicle-api, mysql-db]
      proto: tcp
      ports: [80, 443, 3306]
    - src: vehicle-api
      dst: mysql-db
      proto: tcp
      ports: [3306]
  denied_by_default: true
  logging:
    - pfSense: ingress/egress
    - public-web: access/error
    - vehicle-api: request/response
    - mysql-db: audit/slowlog
```

### 보안 제어
- **WAF**: Public Web 서비스에 적용
- **TLS**: 내부 통신 전체 적용
- **데이터베이스 접근**: Private Subnet 허용 목록만
- **비밀정보**: Vault 관리, 하드코딩 금지
- **백업**: DB 일일 전체 백업 + 시간별 증분 백업, 오프사이트 저장
- **모니터링**: Uptime, APM, 메트릭, Syslog 중앙집중화

### 데이터 흐름 (권장)
1. **외부 접근**: 인터넷 → pfSense → 대고객 웹서비스 (80/443)
2. **관리자 접근**: pfSense VPN 또는 Jump Server → Private Subnet
3. **내부 통신**: 차량 API 서버 ↔ MySQL (포트 3306)
4. **관리 통신**: 관리자용 웹서비스 ↔ 차량 API/DB (내부만)
5. **API 경유**: 대고객 웹서비스 → 차량 API → DB (직접 DB 연결 지양)

## 현대차 차량 데이터베이스 업데이트 (2024-2025)

### 차량 데이터 구조 변경사항
- **브랜드 통합**: 모든 차량을 현대(Hyundai)로 통합 (브랜드 선택 불가)
- **주소 제거**: 위도/경도 좌표만 유지하여 정확한 GPS 위치 추적
- **전압 시스템 추가**: 차종별 전압 정보 (12V/400V/800V) 포함

### 현대차 차종 라인업
**승용차**: Sonata, Avante, Grandeur
**SUV**: Tucson, Santa Fe, Palisade, Kona, Casper  
**전기차**: IONIQ 5 (800V/12V), IONIQ 6 (400V/12V)

### 전압 시스템 분류
- **12V**: 일반 승용차/SUV (아반떼, 소나타, 그랜저, 투싼, 산타페, 팰리세이드, 코나, 캐스퍼)
- **고전압+12V**: 전기차 (IONIQ 5: 800V/12V, IONIQ 6: 400V/12V)
- **24V**: 대형 상용차 (엑시언트, 유니버스) - 향후 추가 예정
- **48V**: 2029년부터 전환 예정 (미래 계획)

# important-instruction-reminders
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.

## 차량 스펙 데이터베이스 시스템 구축 (2024-12-03)

### 새로운 데이터 구조 최적화
- **brand 필드 제거**: cars.json에서 모든 차량이 현대차이므로 불필요한 brand 필드 완전 제거
- **차량 스펙 분리**: `data/vehicle_specs.json` 별도 파일로 상세 스펙 관리
- **동적 연동**: Vehicle 모델에서 model명 기반으로 스펙 정보 자동 매칭

### 상세 스펙 정보 포함 항목
**기본 정보**: 카테고리, 세그먼트, 엔진 타입, 배기량, 출력, 토크
**효율성**: 연비(내연기관) / 주행거리(전기차), 충전시간(전기차)
**제원**: 길이/폭/높이/휠베이스, 중량, 최고속도, 가속성능
**기술**: 변속기, 구동방식, 전압시스템

### API 응답 구조 개선
- `get_cars_by_owner()`, `get_unregistered_cars()`, `get_car_status()` 모든 함수에서 스펙 정보 포함
- 프론트엔드에서 실시간 스펙 정보 표시 (분류, 엔진, 출력, 연비/주행거리)

## Claude 작업 지시사항 추가
**작업 완료 시 CLAUDE.md 업데이트 필수**: 향후 모든 중요한 변경사항이나 새로운 기능 구현 시에는 반드시 CLAUDE.md 파일 마지막 부분에 해당 내용을 추가하여 프로젝트 문서를 최신 상태로 유지한다.