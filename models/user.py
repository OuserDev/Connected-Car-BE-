# User 모델 - 사용자 데이터 관리

from typing import Dict, List, Optional, Any
from .base import DatabaseHelper
import hashlib
from datetime import datetime

class User:
    """사용자 모델 클래스"""
    
    @staticmethod
    def create(username: str, password: str, email: str, name: str = '', phone: str = '') -> Optional[int]:
        """새 사용자 생성"""
        try:
            # 비밀번호 해시
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            
            query = """
            INSERT INTO users (username, password_hash, email, name, phone, created_at) 
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            user_id = DatabaseHelper.execute_insert(query, (
                username, hashed_password, email, name, phone, datetime.now()
            ))
            return user_id
        except Exception as e:
            print(f"User creation error: {e}")
            return None
    
    @staticmethod
    def get_by_id(user_id: int) -> Optional[Dict]:
        """ID로 사용자 조회"""
        query = "SELECT * FROM users WHERE id = %s"
        result = DatabaseHelper.execute_query(query, (user_id,))
        return result[0] if result else None
    
    @staticmethod
    def get_by_username(username: str) -> Optional[Dict]:
        """사용자명으로 사용자 조회"""
        query = "SELECT * FROM users WHERE username = %s"
        result = DatabaseHelper.execute_query(query, (username,))
        return result[0] if result else None
    
    @staticmethod
    def verify_password(username: str, password: str) -> bool:
        """비밀번호 확인"""
        user = User.get_by_username(username)
        if not user:
            return False
        
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        return user.get('password_hash') == hashed_password
    
    @staticmethod
    def update_profile(user_id: int, **kwargs) -> bool:
        """사용자 프로필 업데이트"""
        try:
            # 업데이트할 필드 동적 생성
            update_fields = []
            params = []
            
            for field, value in kwargs.items():
                if field in ['name', 'phone', 'email']:
                    update_fields.append(f"{field} = %s")
                    params.append(value)
            
            if not update_fields:
                return False
            
            params.append(user_id)
            query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = %s"
            
            return DatabaseHelper.execute_update(query, tuple(params)) > 0
        except Exception as e:
            print(f"Profile update error: {e}")
            return False
    
    @staticmethod
    def get_cards(user_id: int) -> List[Dict]:
        """사용자의 등록된 카드 목록 조회"""
        query = """
        SELECT id, card_number, card_name, expiry_date, is_default, created_at 
        FROM registered_cards 
        WHERE user_id = %s 
        ORDER BY is_default DESC, created_at DESC
        """
        return DatabaseHelper.execute_query(query, (user_id,))
    
    @staticmethod
    def add_card(user_id: int, card_number: str, card_name: str, expiry_date: str, is_default: bool = False) -> Optional[int]:
        """카드 등록"""
        try:
            # 카드 번호 마스킹
            if len(card_number) > 4:
                masked_number = '**** **** **** ' + card_number[-4:]
            else:
                masked_number = card_number
            
            query = """
            INSERT INTO registered_cards (user_id, card_number, card_name, expiry_date, is_default, created_at) 
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            card_id = DatabaseHelper.execute_insert(query, (
                user_id, masked_number, card_name, expiry_date, is_default, datetime.now()
            ))
            return card_id
        except Exception as e:
            print(f"Card registration error: {e}")
            return None
    
    @staticmethod
    def remove_card(user_id: int, card_id: int) -> bool:
        """카드 삭제"""
        query = "DELETE FROM registered_cards WHERE id = %s AND user_id = %s"
        return DatabaseHelper.execute_update(query, (card_id, user_id)) > 0