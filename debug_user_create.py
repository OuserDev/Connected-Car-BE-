#!/usr/bin/env python3
"""
User.create() 메서드 디버깅 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.user import User
import hashlib

def test_hash_function():
    """해시 함수 테스트"""
    print("=== 해시 함수 테스트 ===")
    test_password = "test123"
    expected_hash = hashlib.sha256(test_password.encode('utf-8')).hexdigest()
    user_hash = User.hash_password(test_password)
    
    print(f"Original password: {test_password}")
    print(f"Expected hash: {expected_hash}")
    print(f"User.hash_password(): {user_hash}")
    print(f"Match: {'✅' if expected_hash == user_hash else '❌'}")
    
    return expected_hash == user_hash

def test_user_create():
    """User.create() 메서드 테스트"""
    print("\n=== User.create() 메서드 테스트 ===")
    
    test_username = "debug_test_user"
    test_password = "debug123"
    test_email = "debug@test.com"
    test_name = "Debug User"
    
    try:
        # 기존 사용자가 있다면 삭제 (테스트용)
        existing = User.get_by_username(test_username)
        if existing:
            print(f"기존 사용자 {test_username} 존재 - 테스트 계속 진행")
            return False
        
        # 새 사용자 생성
        print(f"Creating user: {test_username}, password: {test_password}")
        user_id = User.create(test_username, test_password, test_email, test_name, "010-0000-0000")
        
        if user_id:
            print(f"✅ 사용자 생성 성공! ID: {user_id}")
            
            # 생성된 사용자 조회
            created_user = User.get_by_id(user_id)
            if created_user:
                stored_password = created_user.get('password')
                expected_hash = User.hash_password(test_password)
                
                print(f"Stored password: {stored_password}")
                print(f"Expected hash: {expected_hash}")
                print(f"Password length: {len(stored_password)}")
                print(f"Is hashed: {'✅' if len(stored_password) == 64 else '❌'}")
                print(f"Hash match: {'✅' if stored_password == expected_hash else '❌'}")
                
                return stored_password == expected_hash
            else:
                print("❌ 생성된 사용자를 조회할 수 없음")
                return False
        else:
            print("❌ 사용자 생성 실패")
            return False
            
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        return False

def test_verify_password():
    """비밀번호 검증 테스트"""
    print("\n=== 비밀번호 검증 테스트 ===")
    
    # 기존 사용자로 테스트
    test_username = "admin"
    test_password = "password123"
    
    try:
        result = User.verify_password(test_username, test_password)
        print(f"Username: {test_username}")
        print(f"Password: {test_password}")
        print(f"Verification result: {'✅' if result else '❌'}")
        
        return result
        
    except Exception as e:
        print(f"❌ 검증 오류: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔍 User 모델 디버깅")
    print("=" * 50)
    
    # 1. 해시 함수 테스트
    hash_ok = test_hash_function()
    
    # 2. User.create() 테스트
    create_ok = test_user_create()
    
    # 3. 비밀번호 검증 테스트
    verify_ok = test_verify_password()
    
    print("\n" + "=" * 50)
    print("테스트 결과:")
    print(f"Hash function: {'✅' if hash_ok else '❌'}")
    print(f"User.create(): {'✅' if create_ok else '❌'}")
    print(f"Password verify: {'✅' if verify_ok else '❌'}")
    
    if all([hash_ok, create_ok, verify_ok]):
        print("\n🎉 모든 테스트 통과!")
    else:
        print("\n⚠️  일부 테스트 실패 - 문제 해결 필요")