import json
import os
import hashlib
from datetime import datetime

class UserModel:
    def __init__(self):
        self.data_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'users.json')
        self._load_data()
    
    def _load_data(self):
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                self.users = json.load(f)
        except FileNotFoundError:
            self.users = []
    
    def get_user_by_id(self, user_id):
        for user in self.users:
            if user['id'] == user_id:
                return user
        return None
    
    def get_user_by_username(self, username):
        for user in self.users:
            if user['username'] == username:
                return user
        return None
    
    def _save_data(self):
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.users, f, ensure_ascii=False, indent=2)
    
    def _hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, username, password):
        user = self.get_user_by_username(username)
        if user:
            hashed_password = self._hash_password(password)
            return user.get('password') == hashed_password or user.get('password') == password  # 기존 평문도 지원
        return False
    
    def register_user(self, username, password, email, name="", phone=""):
        if self.get_user_by_username(username):
            return None  # 이미 존재하는 사용자
        
        new_user = {
            'id': max([u['id'] for u in self.users], default=0) + 1,
            'username': username,
            'password': self._hash_password(password),
            'email': email,
            'name': name,
            'phone': phone,
            'owned_cars': [],
            'registered_cards': [],
            'created_at': datetime.now().isoformat()
        }
        
        self.users.append(new_user)
        self._save_data()
        
        # 패스워드 제외하고 반환
        user_response = new_user.copy()
        del user_response['password']
        return user_response
    
    def add_car_to_user(self, user_id, car_id):
        user = self.get_user_by_id(user_id)
        if user:
            if 'owned_cars' not in user:
                user['owned_cars'] = []
            if car_id not in user['owned_cars']:
                user['owned_cars'].append(car_id)
                self._save_data()
                return True
        return False
    
    def get_user_profile(self, user_id):
        user = self.get_user_by_id(user_id)
        if user:
            # 패스워드 제외하고 반환
            profile = user.copy()
            del profile['password']
            return profile
        return None
    
    def update_user_profile(self, user_id, name=None, phone=None, email=None):
        user = self.get_user_by_id(user_id)
        if not user:
            return None
        
        if name is not None:
            user['name'] = name
        if phone is not None:
            user['phone'] = phone  
        if email is not None:
            user['email'] = email
            
        self._save_data()
        
        # 패스워드 제외하고 반환
        profile = user.copy()
        del profile['password']
        return profile
    
    def add_payment_card(self, user_id, card_number, card_name, expiry_date):
        user = self.get_user_by_id(user_id)
        if not user:
            return None
        
        if 'registered_cards' not in user:
            user['registered_cards'] = []
        
        # 새 카드 ID 생성
        existing_card_ids = [card['id'] for card in user['registered_cards']]
        new_card_id = max(existing_card_ids, default=0) + 1
        
        # 카드 번호 마스킹 (마지막 4자리만 표시)
        masked_number = f"**** **** **** {card_number[-4:]}"
        
        new_card = {
            'id': new_card_id,
            'card_number': masked_number,
            'card_name': card_name,
            'expiry_date': expiry_date,
            'is_default': len(user['registered_cards']) == 0,  # 첫 번째 카드는 기본 카드
            'created_at': datetime.now().isoformat()
        }
        
        user['registered_cards'].append(new_card)
        self._save_data()
        return new_card
    
    def remove_payment_card(self, user_id, card_id):
        user = self.get_user_by_id(user_id)
        if not user or 'registered_cards' not in user:
            return False
        
        for i, card in enumerate(user['registered_cards']):
            if card['id'] == card_id:
                removed_card = user['registered_cards'].pop(i)
                
                # 기본 카드를 삭제한 경우 다른 카드를 기본으로 설정
                if removed_card.get('is_default') and user['registered_cards']:
                    user['registered_cards'][0]['is_default'] = True
                
                self._save_data()
                return True
        return False
    
    def set_default_card(self, user_id, card_id):
        user = self.get_user_by_id(user_id)
        if not user or 'registered_cards' not in user:
            return False
        
        # 모든 카드의 기본 설정 해제
        for card in user['registered_cards']:
            card['is_default'] = False
        
        # 선택한 카드를 기본으로 설정
        for card in user['registered_cards']:
            if card['id'] == card_id:
                card['is_default'] = True
                self._save_data()
                return True
        return False
    
    def get_payment_cards(self, user_id):
        user = self.get_user_by_id(user_id)
        if user and 'registered_cards' in user:
            return user['registered_cards']
        return []