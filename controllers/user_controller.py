from flask import Blueprint, jsonify, session, request
from models.user import User
from models.car import Car
from utils.auth import login_required

user_bp = Blueprint('user', __name__)

# 사용자 정보 조회 API (MySQL 기반)
@user_bp.route('/api/user/profile', methods=['GET'])
@login_required
def get_user_profile():
    """로그인한 사용자의 프로필 정보 조회"""
    try:
        user_id = session.get('user_id')
        
        # 사용자 기본 정보 조회
        user = User.get_by_id(user_id)
        if not user:
            return jsonify({'error': '사용자를 찾을 수 없습니다'}), 404
        
        # 사용자 소유 차량 목록 조회
        cars = Car.get_by_owner(user_id)
        
        # 등록된 카드 정보 조회
        cards = User.get_cards(user_id)
        
        # 비밀번호 제외하고 응답
        user_profile = {
            'id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'name': user['name'],
            'phone': user['phone'],
            'created_at': user['created_at'].isoformat() if user['created_at'] else None,
            'owned_cars': cars,
            'registered_cards': cards
        }
        
        return jsonify({
            'success': True,
            'data': user_profile
        })
        
    except Exception as e:
        return jsonify({'error': f'사용자 정보 조회 실패: {str(e)}'}), 500

# 사용자 목록 조회 API (관리자용 - 주석 처리)
# @user_bp.route('/api/users', methods=['GET'])
# @login_required
# def get_all_users():
#     """모든 사용자 목록 조회 (관리자 전용)"""
#     # 관리자 기능은 별도 관리자 VM에서 구현
#     pass

# 사용자 카드 등록 API
@user_bp.route('/api/user/cards', methods=['POST'])
@login_required
def register_card():
    """사용자 카드 등록"""
    try:
        user_id = session.get('user_id')
        data = request.get_json()
        
        # 필수 필드 검증
        required_fields = ['card_number', 'card_name', 'expiry_date']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field}는 필수 입력 항목입니다'}), 400
        
        # 카드 등록
        card_id = User.add_card(
            user_id,
            data['card_number'],
            data['card_name'],
            data['expiry_date'],
            data.get('is_default', False)
        )
        
        if not card_id:
            return jsonify({'error': '카드 등록 실패'}), 500
        
        return jsonify({
            'success': True,
            'message': '카드가 성공적으로 등록되었습니다',
            'card_id': card_id
        })
        
    except Exception as e:
        return jsonify({'error': f'카드 등록 실패: {str(e)}'}), 500