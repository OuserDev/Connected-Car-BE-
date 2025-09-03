from flask import Flask, jsonify, render_template
from flask_cors import CORS
from datetime import timedelta

# JSON 기반 컨트롤러 (기존 - 주석 처리)
# from controllers.user_controller import user_bp
# from controllers.vehicle_controller import vehicle_bp
# from controllers.auth_controller import auth_bp
# from controllers.vehicle_api_controller import vehicle_api_bp

# MySQL 기반 컨트롤러 (신규)
from controllers.auth_controller import auth_bp  # 인증은 그대로 유지
from controllers.vehicle_controller import vehicle_bp  # MySQL 기반 차량 컨트롤러
from controllers.vehicle_api_controller import vehicle_api_bp  # MySQL 기반 차량 API 컨트롤러
from controllers.user_controller import user_bp  # 수정된 사용자 컨트롤러

# 데이터베이스 연결 테스트
from utils.database import test_database_connection

app = Flask(__name__)

# CORS 설정 - 개발 환경용 (credentials 포함, origins 허용)
CORS(app, supports_credentials=True, origins=['http://192.168.201.221:8000', 'http://localhost:8000'])

# Session configuration - Flask 2.0.3 방식
app.secret_key = 'connected-car-secret-key-for-testing'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)  # 1시간
app.config['SESSION_COOKIE_SECURE'] = False  # 개발 환경용
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Blueprint 등록 (MySQL 기반)
app.register_blueprint(auth_bp)  # 인증 컨트롤러
app.register_blueprint(user_bp)  # 사용자 컨트롤러 (MySQL 기반)
app.register_blueprint(vehicle_bp)  # 차량 컨트롤러 (MySQL 기반)
app.register_blueprint(vehicle_api_bp)  # 차량 API 컨트롤러 (MySQL 기반)

# 기존 JSON 기반 컨트롤러 (주석 처리)
# app.register_blueprint(user_bp)
# app.register_blueprint(vehicle_bp)
# app.register_blueprint(vehicle_api_bp)

@app.route('/')
def hello():
    return render_template('1.html')

@app.route('/vehicles')
def vehicles_page():
    return render_template('vehicles.html')

@app.route('/api/health', methods=['GET'])
def health_check():
    """애플리케이션 및 데이터베이스 상태 확인"""
    try:
        # 데이터베이스 연결 테스트
        db_status = test_database_connection()
        
        return jsonify({
            'status': 'healthy',
            'message': 'BE 애플리케이션이 정상 작동 중입니다',
            'database': 'connected' if db_status else 'disconnected',
            'version': '2.0.0-mysql',
            'features': [
                'MySQL 기반 데이터 관리',
                'car-api 서버 연동',
                'dual controller pattern'
            ]
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("🚗 커넥티드카 BE 서버 시작 중...")
    print("📊 MySQL 기반 데이터 관리")
    print("🔗 car-api 서버 연동 (localhost:9000)")
    
    # 데이터베이스 연결 확인
    if test_database_connection():
        print("✅ MySQL 데이터베이스 연결 성공")
    else:
        print("❌ MySQL 데이터베이스 연결 실패")
        print("⚠️  로컬 MySQL 서버가 실행 중인지 확인하세요")
    
    app.run(debug=True, host='0.0.0.0', port=8000)