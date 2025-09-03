from flask import Flask, jsonify, render_template
from flask_cors import CORS
from datetime import timedelta
from controllers.user_controller import user_bp
from controllers.vehicle_controller import vehicle_bp
from controllers.auth_controller import auth_bp
from controllers.vehicle_api_controller import vehicle_api_bp

app = Flask(__name__)

# CORS 설정 - 개발 환경용 (credentials 포함, origins 허용)
CORS(app, supports_credentials=True, origins=['http://192.168.201.221:8000', 'http://localhost:8000'])

# Session configuration - Flask 2.0.3 방식
app.secret_key = 'connected-car-secret-key-for-testing'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)  # 1시간
app.config['SESSION_COOKIE_SECURE'] = False  # 개발 환경용
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Blueprint 등록
app.register_blueprint(user_bp)
app.register_blueprint(vehicle_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(vehicle_api_bp)

@app.route('/')
def hello():
    return render_template('1.html')

@app.route('/vehicles')
def vehicles_page():
    return render_template('vehicles.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)