# MySQL 기반 인증 컨트롤러

from flask import Blueprint, request, jsonify, session
from utils.database import UserDatabase
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
        user = UserDatabase.get_user_by_username(username)
        if not user:
            return jsonify({'error': 'Invalid username or password'}), 401
        
        # 비밀번호 검증 (실제로는 해시 비교해야 함)
        if user['password'] != password:
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
        existing_user = UserDatabase.get_user_by_username(username)
        if existing_user:
            return jsonify({'error': 'Username already exists'}), 409
        
        # 새 사용자 생성
        user_id = UserDatabase.create_user(username, password, email, name, phone)
        
        return jsonify({
            'message': 'Registration successful',
            'status': 'success',
            'user_id': user_id
        })
        
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
        user = UserDatabase.get_user_by_id(session['user_id'])
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
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
        return jsonify({'error': f'사용자 정보 조회 중 오류 발생: {str(e)}'}), 500

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
