#!/usr/bin/env python3
"""
비밀번호 해시화 기능 테스트 스크립트
"""

import pymysql
import hashlib
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

def hash_password(password):
    """SHA-256으로 비밀번호 해시화"""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def test_registration():
    """회원가입 테스트"""
    print("=== 회원가입 테스트 ===")
    
    # 테스트용 사용자 데이터
    test_user = {
        "username": "testuser123",
        "password": "testpass123",
        "email": "testuser123@test.com",
        "name": "테스트 사용자",
        "phone": "010-1234-5678"
    }
    
    try:
        response = requests.post(
            'http://localhost:8000/api/auth/register',
            headers={'Content-Type': 'application/json'},
            data=json.dumps(test_user)
        )
        
        if response.status_code == 200:
            print("✅ 회원가입 성공!")
            print(f"응답: {response.json()}")
            return True
        else:
            print(f"❌ 회원가입 실패: {response.status_code}")
            print(f"오류: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 회원가입 요청 오류: {str(e)}")
        return False

def test_login():
    """로그인 테스트"""
    print("\n=== 로그인 테스트 ===")
    
    # 기존 사용자로 로그인 테스트
    login_data = {
        "username": "admin",
        "password": "password123"
    }
    
    try:
        response = requests.post(
            'http://localhost:8000/api/auth/login',
            headers={'Content-Type': 'application/json'},
            data=json.dumps(login_data)
        )
        
        if response.status_code == 200:
            print("✅ 기존 사용자 로그인 성공!")
            print(f"응답: {response.json()}")
            return True
        else:
            print(f"❌ 로그인 실패: {response.status_code}")
            print(f"오류: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 로그인 요청 오류: {str(e)}")
        return False

def test_new_user_login():
    """새 사용자 로그인 테스트"""
    print("\n=== 새 사용자 로그인 테스트 ===")
    
    login_data = {
        "username": "testuser123",
        "password": "testpass123"
    }
    
    try:
        response = requests.post(
            'http://localhost:8000/api/auth/login',
            headers={'Content-Type': 'application/json'},
            data=json.dumps(login_data)
        )
        
        if response.status_code == 200:
            print("✅ 새 사용자 로그인 성공!")
            print(f"응답: {response.json()}")
            return True
        else:
            print(f"❌ 새 사용자 로그인 실패: {response.status_code}")
            print(f"오류: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 새 사용자 로그인 요청 오류: {str(e)}")
        return False

def check_database():
    """데이터베이스 확인"""
    print("\n=== 데이터베이스 비밀번호 해시 확인 ===")
    
    try:
        conn = pymysql.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 3307)),
            user=os.getenv('DB_USER', 'admin'),
            password=os.getenv('DB_PASSWORD', 'STRONGMAN'),
            database='connected_car_service',
            charset='utf8mb4'
        )
        
        with conn.cursor() as cursor:
            cursor.execute("SELECT username, password FROM users WHERE username IN ('admin', 'testuser123') ORDER BY username")
            users = cursor.fetchall()
            
            for username, password in users:
                print(f"사용자 '{username}': {password[:16]}... (길이: {len(password)})")
                if len(password) == 64:
                    print(f"  ✅ SHA-256 해시 형태 (64자리)")
                else:
                    print(f"  ❌ 평문 또는 다른 형태 ({len(password)}자리)")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 데이터베이스 확인 오류: {str(e)}")

if __name__ == "__main__":
    print("🔐 비밀번호 해시화 기능 테스트")
    print("=" * 50)
    
    # 1. 데이터베이스 현재 상태 확인
    check_database()
    
    # 2. 회원가입 테스트
    registration_success = test_registration()
    
    # 3. 기존 사용자 로그인 테스트
    login_success = test_login()
    
    # 4. 새 사용자 로그인 테스트 (회원가입 성공한 경우만)
    if registration_success:
        new_login_success = test_new_user_login()
    
    # 5. 최종 데이터베이스 상태 확인
    check_database()
    
    print("\n" + "=" * 50)
    print("테스트 완료!")