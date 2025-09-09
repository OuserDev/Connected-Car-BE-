#!/usr/bin/env python3
"""
기존 평문 비밀번호를 해시화하는 스크립트
"""

import pymysql
import hashlib
import os
from dotenv import load_dotenv

load_dotenv()

def hash_password(password):
    """SHA-256으로 비밀번호 해시화"""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def get_db_connection():
    """connected_car_service 데이터베이스 연결"""
    return pymysql.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 3307)),
        user=os.getenv('DB_USER', 'admin'),
        password=os.getenv('DB_PASSWORD', 'STRONGMAN'),
        database='connected_car_service',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

def update_passwords():
    """기존 평문 비밀번호를 해시화하여 업데이트"""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # 현재 사용자 목록 조회
            cursor.execute("SELECT id, username, password FROM users")
            users = cursor.fetchall()
            
            print(f"총 {len(users)}명의 사용자 비밀번호를 해시화합니다...")
            
            # 각 사용자의 비밀번호 해시화
            for user in users:
                user_id = user['id']
                username = user['username']
                plaintext_password = user['password']
                
                # 이미 해시화된 비밀번호인지 확인 (SHA-256는 64자리)
                if len(plaintext_password) == 64:
                    print(f"사용자 '{username}'의 비밀번호는 이미 해시화되어 있습니다.")
                    continue
                
                # 비밀번호 해시화
                hashed_password = hash_password(plaintext_password)
                
                # 데이터베이스 업데이트
                cursor.execute(
                    "UPDATE users SET password = %s WHERE id = %s",
                    (hashed_password, user_id)
                )
                
                print(f"✓ 사용자 '{username}': '{plaintext_password}' → '{hashed_password[:16]}...'")
            
            # 변경사항 커밋
            conn.commit()
            print("\n✅ 모든 비밀번호가 성공적으로 해시화되었습니다!")
            
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    print("=== 비밀번호 해시화 스크립트 ===")
    update_passwords()