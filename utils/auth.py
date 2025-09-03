from functools import wraps
from flask import session, jsonify

# 로그인 필수 데코레이터
# 이 데코레이터가 적용된 함수는 로그인된 사용자만 접근 가능
# 세션에 user_id가 없으면 401 Unauthorized 응답 반환
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

# 현재 로그인한 사용자 정보 조회
# 세션에서 사용자 정보(id, username) 반환
# 로그인 안된 경우 None 반환
def get_current_user():
    if 'user_id' in session:
        return {
            'id': session['user_id'],
            'username': session['username']
        }
    return None