# MySQL 기반 인증 컨트롤러

from flask import Blueprint, request, jsonify, session
from models.user import User
from models.vehicle_spec import VehicleSpec
from models.car import Car
import json

# 인증 관련 Blueprint 생성
auth_bp = Blueprint('auth', __name__)

# 사용자 로그인 처리 (MySQL 기반)
@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    """사용자 로그인 (MySQL 기반)"""
    try:
        data = request.get_json() or {}
        username = data.get('username')
        password = data.get('password')
        
        # 필수 필드 검증
        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400
        
        # MySQL에서 사용자 조회
        user = User.get_by_username(username)
        if not user:
            return jsonify({'error': 'Invalid username or password'}), 401
        
        # 사용자 상태 확인
        if user.get('status') == 'suspended':
            return jsonify({
                'error': '계정이 정지되었습니다. 관리자에게 문의하세요.',
                'status': 'suspended'
            }), 403
        elif user.get('status') == 'deleted':
            return jsonify({'error': 'Invalid username or password'}), 401
        
        # 비밀번호 검증 (해시 비교)
        if not User.verify_password(username, password):
            return jsonify({'error': 'Invalid username or password'}), 401
        
        # 세션에 사용자 정보 저장
        session['user_id'] = user['id']
        session['username'] = user['username']
        session.permanent = True
        
        # 로그인 성공 응답
        return jsonify({
            'message': 'Login successful',
            'status': 'success',
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user.get('email', ''),
                'name': user.get('name', ''),
                'phone': user.get('phone', '')
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'로그인 처리 중 오류 발생: {str(e)}'}), 500

# 사용자 로그아웃 처리
@auth_bp.route('/api/auth/logout', methods=['POST'])
def logout():
    """사용자 로그아웃"""
    try:
        # 세션 정리
        session.clear()
        
        return jsonify({
            'message': 'Logout successful',
            'status': 'success'
        })
        
    except Exception as e:
        return jsonify({'error': f'로그아웃 처리 중 오류 발생: {str(e)}'}), 500

# 사용자 회원가입 처리 (MySQL 기반)
@auth_bp.route('/api/auth/register', methods=['POST'])
def register():
    """사용자 회원가입 (MySQL 기반)"""
    try:
        data = request.get_json() or {}
        
        # 필수 필드 검증
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        name = data.get('name')
        phone = data.get('phone', '')
        
        if not all([username, password, email, name]):
            return jsonify({'error': 'Username, password, email, and name are required'}), 400
        
        # 중복 사용자 검사
        existing_user = User.get_by_username(username)
        if existing_user:
            return jsonify({'error': 'Username already exists'}), 409
        
        # 새 사용자 생성
        user_id = User.create(username, password, email, name, phone)

        # 자동 차량 등록 로직
        car_info = None
        try:
            # 1. vehicle_specs에서 랜덤으로 차량 모델 선택
            random_vehicle_spec = VehicleSpec.get_random()

            if random_vehicle_spec:
                model_id = random_vehicle_spec['id']

                # 2. 랜덤 VIN 및 번호판 생성 (중복 확인)
                max_attempts = 10
                vin = None
                license_plate = None

                for _ in range(max_attempts):
                    # VIN 생성 및 중복 확인
                    temp_vin = Car.generate_random_vin()
                    if not Car.get_by_vin(temp_vin):
                        vin = temp_vin
                        break

                for _ in range(max_attempts):
                    # 번호판 생성 및 중복 확인
                    temp_license_plate = Car.generate_random_license_plate()
                    if not Car.get_by_license_plate(temp_license_plate):
                        license_plate = temp_license_plate
                        break

                # 3. 차량 등록
                if vin and license_plate:
                    car_id = Car.register(
                        owner_id=user_id,
                        model_id=model_id,
                        license_plate=license_plate,
                        vin=vin
                    )

                    if car_id:
                        # 등록된 차량 정보 조회
                        car_info = Car.get_by_id(car_id)
                        print(f"Auto-registered car for user {user_id}: car_id={car_id}, model={random_vehicle_spec.get('model')}, vin={vin}, license_plate={license_plate}")

        except Exception as car_error:
            # 차량 등록 실패 시 로그만 남기고 회원가입은 성공 처리
            print(f"Auto car registration failed for user {user_id}: {str(car_error)}")

        response_data = {
            'message': 'Registration successful',
            'status': 'success',
            'user_id': user_id
        }

        # 차량 정보가 있으면 응답에 포함
        if car_info:
            response_data['auto_registered_car'] = {
                'car_id': car_info['id'],
                'model_name': car_info.get('model_name'),
                'license_plate': car_info['license_plate'],
                'vin': car_info['vin'],
                'category': car_info.get('category'),
                'engine_type': car_info.get('engine_type')
            }

        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({'error': f'회원가입 처리 중 오류 발생: {str(e)}'}), 500

# 현재 사용자 정보 조회
@auth_bp.route('/api/auth/me', methods=['GET'])
def get_current_user():
    """현재 로그인한 사용자 정보 조회"""
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        
        # 사용자 정보 조회
        user = User.get_by_id(session['user_id'])
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # 사용자 상태 확인
        if user.get('status') == 'suspended':
            # 정지된 사용자는 세션 정리
            session.clear()
            return jsonify({
                'error': '계정이 정지되었습니다. 관리자에게 문의하세요.',
                'status': 'suspended'
            }), 403
        elif user.get('status') == 'deleted':
            # 삭제된 사용자는 세션 정리
            session.clear()
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'status': 'success',
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user.get('email', ''),
                'name': user.get('name', ''),
                'phone': user.get('phone', ''),
                'status': user.get('status', 'active')
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'사용자 정보 조회 중 오류 발생: {str(e)}'}), 500

# 비밀번호 변경 처리
@auth_bp.route('/api/auth/change-password', methods=['POST'])
def change_password():
    """비밀번호 변경"""
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        
        data = request.get_json() or {}
        old_password = data.get('old_password')
        new_password = data.get('new_password')
        
        if not old_password or not new_password:
            return jsonify({'error': 'Old password and new password are required'}), 400
        
        # 비밀번호 변경
        if User.change_password(session['user_id'], old_password, new_password):
            return jsonify({
                'message': 'Password changed successfully',
                'status': 'success'
            })
        else:
            return jsonify({'error': 'Invalid old password'}), 400
        
    except Exception as e:
        return jsonify({'error': f'비밀번호 변경 중 오류 발생: {str(e)}'}), 500

# 세션 상태 확인
@auth_bp.route('/api/auth/status', methods=['GET'])
def check_auth_status():
    """인증 상태 확인"""
    try:
        if 'user_id' in session:
            return jsonify({
                'authenticated': True,
                'user_id': session['user_id'],
                'username': session.get('username', '')
            })
        else:
            return jsonify({
                'authenticated': False
            })
            
    except Exception as e:
        return jsonify({'error': f'인증 상태 확인 중 오류 발생: {str(e)}'}), 500