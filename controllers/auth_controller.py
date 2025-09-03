from flask import Blueprint, request, jsonify, session
from models.user import UserModel
import json

# 인증 관련 Blueprint 생성
auth_bp = Blueprint('auth', __name__)
# 사용자 모델 인스턴스 생성
user_model = UserModel()

# 사용자 로그인 처리
# POST /api/auth/login
# JSON 또는 form 데이터로 username, password 받음
# 성공시 세션에 사용자 정보 저장하고 200 반환
# 실패시 401 반환
@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    # JSON 또는 form 데이터 처리
    data = request.get_json() or request.form.to_dict()
    
    username = data.get('username')
    password = data.get('password')
    
    # 필수 필드 검증
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    
    # 비밀번호 검증
    if user_model.verify_password(username, password):
        user = user_model.get_user_by_username(username)
        
        # 세션에 사용자 정보 저장
        session['user_id'] = user['id']
        session['username'] = user['username']
        session.permanent = True
        
        # 로그인 성공 응답 (비밀번호 제외)
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
    
    # 인증 실패
    return jsonify({'error': 'Invalid credentials'}), 401

# 사용자 로그아웃 처리
# POST /api/auth/logout
# 세션 정보 모두 삭제
@auth_bp.route('/api/auth/logout', methods=['POST'])
def logout():
    session.clear()  # 모든 세션 데이터 삭제
    return jsonify({'message': 'Logout successful'})

# 사용자 회원가입 처리
# POST /api/auth/register
# username, password, email 필수 필드
# 성공시 201, 중복 사용자명 시 409 반환
@auth_bp.route('/api/auth/register', methods=['POST'])
def register():
    # JSON 또는 form 데이터 처리
    data = request.get_json() or request.form.to_dict()
        
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    
    # 필수 필드 검증
    if not username or not password or not email:
        return jsonify({'error': 'Username, password and email required'}), 400
    
    # 추가 필드 처리
    name = data.get('name', '')
    phone = data.get('phone', '')
    
    # 사용자 등록 시도
    user = user_model.register_user(username, password, email, name, phone)
    if user:
        return jsonify({
            'message': 'Registration successful',
            'user': user
        }), 201
    
    # 사용자명 중복 등 등록 실패
    return jsonify({'error': 'Username already exists'}), 409

# 사용자 프로필 조회
# GET /api/auth/profile
# 로그인된 사용자의 프로필 정보 반환 (비밀번호 제외)
# 로그인 안됨: 401, 사용자 없음: 404
@auth_bp.route('/api/auth/profile')
def get_profile():
    # 로그인 상태 확인
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    # 사용자 정보 조회
    user = user_model.get_user_by_id(session['user_id'])
    if user:
        user_response = user.copy()
        del user_response['password']  # 패스워드 제외하고 반환
        return jsonify(user_response)
    
    return jsonify({'error': 'User not found'}), 404

# 인증 상태 확인
# GET /api/auth/status  
# 현재 로그인 상태와 사용자 기본 정보 반환
@auth_bp.route('/api/auth/status')
def auth_status():
    if 'user_id' in session:
        return jsonify({
            'authenticated': True,
            'user': {
                'id': session['user_id'],
                'username': session['username']
            }
        })
    
    # 로그인되지 않은 상태
    return jsonify({'authenticated': False})

# 사용자 프로필 업데이트
# PUT /api/auth/profile
# 이름, 전화번호, 이메일 업데이트
@auth_bp.route('/api/auth/profile', methods=['PUT'])
def update_profile():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'JSON data required'}), 400
    
    name = data.get('name')
    phone = data.get('phone')
    email = data.get('email')
    
    updated_user = user_model.update_user_profile(session['user_id'], name, phone, email)
    if updated_user:
        return jsonify({
            'message': 'Profile updated successfully',
            'user': updated_user
        })
    
    return jsonify({'error': 'User not found'}), 404

# 결제 카드 목록 조회
# GET /api/auth/cards
@auth_bp.route('/api/auth/cards')
def get_payment_cards():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    cards = user_model.get_payment_cards(session['user_id'])
    return jsonify({'cards': cards})

# 결제 카드 추가
# POST /api/auth/cards
@auth_bp.route('/api/auth/cards', methods=['POST'])
def add_payment_card():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'JSON data required'}), 400
    
    card_number = data.get('card_number')
    card_name = data.get('card_name')
    expiry_date = data.get('expiry_date')
    
    if not card_number or not card_name or not expiry_date:
        return jsonify({'error': 'Card number, name and expiry date required'}), 400
    
    # 카드 번호 길이 검증
    if len(card_number) < 4:
        return jsonify({'error': 'Invalid card number'}), 400
    
    new_card = user_model.add_payment_card(session['user_id'], card_number, card_name, expiry_date)
    if new_card:
        return jsonify({
            'message': 'Card added successfully',
            'card': new_card
        }), 201
    
    return jsonify({'error': 'Failed to add card'}), 500

# 결제 카드 삭제
# DELETE /api/auth/cards/<card_id>
@auth_bp.route('/api/auth/cards/<int:card_id>', methods=['DELETE'])
def remove_payment_card(card_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    if user_model.remove_payment_card(session['user_id'], card_id):
        return jsonify({'message': 'Card removed successfully'})
    
    return jsonify({'error': 'Card not found'}), 404

# 기본 결제 카드 설정
# PUT /api/auth/cards/<card_id>/default
@auth_bp.route('/api/auth/cards/<int:card_id>/default', methods=['PUT'])
def set_default_card(card_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    if user_model.set_default_card(session['user_id'], card_id):
        return jsonify({'message': 'Default card updated successfully'})
    
    return jsonify({'error': 'Card not found'}), 404