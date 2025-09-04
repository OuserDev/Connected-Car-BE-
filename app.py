from flask import Flask, jsonify, render_template
from flask_cors import CORS
from datetime import timedelta
import os
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

from controllers.auth_controller import auth_bp
from controllers.vehicle_controller import vehicle_bp
from controllers.vehicle_api_controller import vehicle_api_bp
from controllers.user_controller import user_bp

# 데이터베이스 연결 테스트
from models.base import test_database_connection

app = Flask(__name__)

# 로깅 설정
def setup_logging(app):
    """로깅 설정 함수"""
    # logs 디렉토리 생성
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # 로그 포맷 설정
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    )
    
    # 파일 핸들러 설정 (최대 10MB, 백업 5개)
    file_handler = RotatingFileHandler(
        'logs/connected_car.log', 
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    
    # 에러 로그 파일 핸들러
    error_file_handler = RotatingFileHandler(
        'logs/connected_car_error.log',
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    error_file_handler.setFormatter(formatter)
    error_file_handler.setLevel(logging.ERROR)
    
    # Flask 앱 로거에 핸들러 추가
    app.logger.addHandler(file_handler)
    app.logger.addHandler(error_file_handler)
    app.logger.setLevel(logging.INFO)
    
    # Werkzeug 로그도 파일로 저장
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.addHandler(file_handler)
    werkzeug_logger.setLevel(logging.INFO)

# 로깅 설정 적용
setup_logging(app)

# 요청 로깅 미들웨어
@app.before_request
def log_request_info():
    """모든 요청을 로그에 기록"""
    from flask import request
    app.logger.info(f'Request: {request.method} {request.url} - IP: {request.remote_addr}')

@app.after_request
def log_response_info(response):
    """모든 응답을 로그에 기록"""
    from flask import request
    app.logger.info(f'Response: {response.status_code} for {request.method} {request.url}')
    return response

# CORS 설정 - 개발 환경용 (credentials 포함, origins 허용)
CORS(app, supports_credentials=True, origins=['http://192.168.201.221:8000', 'http://localhost:8000'])

# Session configuration - Flask 2.0.3 방식 (환경변수 사용)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'connected-car-secret-key-for-testing')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)  # 1시간
app.config['SESSION_COOKIE_SECURE'] = False  # 개발 환경용
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Blueprint 등록
app.register_blueprint(auth_bp)
app.register_blueprint(user_bp)
app.register_blueprint(vehicle_bp)
app.register_blueprint(vehicle_api_bp)

@app.route('/')
def hello():
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
    # 서버 시작 로그
    startup_message = "🚗 커넥티드카 BE 서버 시작 중..."
    print(startup_message)
    app.logger.info(startup_message)
    
    db_message = "📊 MySQL 기반 데이터 관리"
    print(db_message)
    app.logger.info(db_message)
    
    api_message = "🔗 car-api 서버 연동 (localhost:9000)"
    print(api_message)
    app.logger.info(api_message)
    
    # 데이터베이스 연결 확인
    if test_database_connection():
        success_message = "✅ MySQL 데이터베이스 연결 성공"
        print(success_message)
        app.logger.info(success_message)
    else:
        error_message = "❌ MySQL 데이터베이스 연결 실패"
        warning_message = "⚠️  로컬 MySQL 서버가 실행 중인지 확인하세요"
        print(error_message)
        print(warning_message)
        app.logger.error(error_message)
        app.logger.warning(warning_message)
    
    # 서버 시작 시간 기록
    app.logger.info("Flask 개발 서버 시작: http://0.0.0.0:8000")
    
    app.run(debug=True, host='0.0.0.0', port=8000)