# controllers/card_controller.py - 결제 카드 관리
from flask import Blueprint, request, jsonify, session
from utils.auth import login_required
import pymysql
from datetime import datetime
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

card_bp = Blueprint('card', __name__)

# DB 연결 함수
def get_db_connection():
    """데이터베이스 연결 반환 - 환경변수 기반"""
    return pymysql.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 3306)),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', 'student'),
        database=os.getenv('DB_NAME', 'connected_car_service'),
        charset='utf8mb4',
        autocommit=True,
        cursorclass=pymysql.cursors.DictCursor
    )

# 카드번호 마스킹 함수
def mask_card_number(card_number, is_test_card=False):
    """카드번호 마스킹 처리"""
    if is_test_card:
        return card_number  # 테스트 카드는 전체 표시
    
    # 실제 카드는 마스킹 (**** **** **** 1234)
    if len(card_number) >= 4:
        return '**** **** **** ' + card_number[-4:]
    return '**** **** **** ****'

# 카드 브랜드 감지 함수
def detect_card_brand(card_number):
    """카드번호로 브랜드 감지"""
    number = card_number.replace(' ', '').replace('-', '')
    
    if number.startswith('4'):
        return 'VISA'
    elif number.startswith(('51', '52', '53', '54', '55')) or number.startswith(('2221', '2222', '2223', '2224', '2225', '2226', '2227')):
        return 'Mastercard'
    elif number.startswith(('34', '37')):
        return 'American Express'
    elif number.startswith('6011') or number.startswith('65'):
        return 'Discover'
    else:
        return 'Unknown'

@card_bp.route('/api/cards', methods=['GET'])
@login_required
def get_user_cards():
    """사용자의 등록된 카드 목록 조회"""
    try:
        user_id = session.get('user_id')
        print(f"[DEBUG] Get cards for user_id: {user_id}")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 사용자의 카드 목록 조회 (기본 카드 우선 정렬)
        cursor.execute("""
            SELECT id, card_number, card_name, expiry_date, is_default, created_at
            FROM registered_cards 
            WHERE user_id = %s 
            ORDER BY is_default DESC, created_at DESC
        """, (user_id,))
        
        cards = cursor.fetchall()
        print(f"[DEBUG] Found {len(cards)} cards: {cards}")
        
        # 카드 정보 포맷팅
        formatted_cards = []
        for card in cards:
            # 테스트 카드 여부 확인 (4242로 끝나거나 0077로 끝나는 경우)
            is_test_card = card['card_number'].endswith('4242') or card['card_number'].endswith('0077')
            
            # 마지막 4자리 추출
            last4 = card['card_number'][-4:] if len(card['card_number']) >= 4 else '****'
            
            formatted_cards.append({
                'id': card['id'],
                'brand': detect_card_brand(card['card_number']),
                'last4': last4,  # 프론트엔드에서 기대하는 필드명
                'exp': card['expiry_date'],  # 프론트엔드에서 기대하는 필드명
                'holder': card['card_name'],  # 프론트엔드에서 기대하는 필드명
                'isTest': is_test_card,  # 프론트엔드에서 기대하는 필드명
                'fullNumber': card['card_number'] if is_test_card else None,  # 테스트 카드만 전체 번호 제공
                'isDefault': bool(card['is_default']),
                'createdAt': card['created_at'].isoformat(),
                # 백엔드용 추가 필드들
                'maskedNumber': mask_card_number(card['card_number'], is_test_card),
                'expiryDate': card['expiry_date'],
                'holderName': card['card_name'],
                'isTestCard': is_test_card,
            })
        
        cursor.close()
        conn.close()
        
        print(f"[DEBUG] Returning formatted cards: {formatted_cards}")
        
        return jsonify({
            'success': True,
            'cards': formatted_cards,
            'totalCount': len(formatted_cards)
        })
        
    except Exception as e:
        print(f"[ERROR] Get user cards failed: {str(e)}")
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
        return jsonify({'error': f'카드 목록 조회 실패: {str(e)}'}), 500

@card_bp.route('/api/cards', methods=['POST'])
@login_required
def add_card():
    """새 카드 등록"""
    try:
        user_id = session.get('user_id')
        data = request.get_json()
        
        # 입력 데이터 검증
        card_number = data.get('cardNumber', '').replace(' ', '').replace('-', '')
        card_name = data.get('cardName', '').strip()
        expiry_date = data.get('expiryDate', '').strip()
        set_as_default = data.get('setAsDefault', False)
        
        if not card_number or len(card_number) < 13:
            return jsonify({'error': '유효한 카드번호를 입력해주세요.'}), 400
            
        if not card_name:
            return jsonify({'error': '카드 소유자명을 입력해주세요.'}), 400
            
        if not expiry_date or '/' not in expiry_date:
            return jsonify({'error': '유효한 만료일을 입력해주세요. (MM/YY)'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 이미 등록된 카드인지 확인
        '''
        cursor.execute("""
            SELECT id FROM registered_cards 
            WHERE user_id = %s AND card_number = %s
        """, (user_id, card_number))
        '''

        sql = (
            "SELECT id FROM registered_cards "
            f"WHERE user_id = {user_id} AND card_number = '{card_number}'"
        )
        cursor.execute(sql)
        
        existing_card = cursor.fetchone()
        if existing_card:
            cursor.close()
            conn.close()
            return jsonify({'error': '이미 등록된 카드입니다.'}), 400
        
        # 첫 번째 카드인 경우 자동으로 기본 카드로 설정
        cursor.execute("SELECT COUNT(*) as count FROM registered_cards WHERE user_id = %s", (user_id,))
        card_count = cursor.fetchone()['count']
        
        if card_count == 0:
            set_as_default = True
        
        # 기본 카드로 설정하는 경우 기존 기본 카드 해제
        if set_as_default:
            cursor.execute("""
                UPDATE registered_cards 
                SET is_default = FALSE 
                WHERE user_id = %s
            """, (user_id,))
        
        # 새 카드 등록
        cursor.execute("""
            INSERT INTO registered_cards (user_id, card_number, card_name, expiry_date, is_default)
            VALUES (%s, %s, %s, %s, %s)
        """, (user_id, card_number, card_name, expiry_date, set_as_default))
        
        card_id = cursor.lastrowid
        
        # 등록된 카드 정보 반환
        cursor.execute("""
            SELECT id, card_number, card_name, expiry_date, is_default, created_at
            FROM registered_cards 
            WHERE id = %s
        """, (card_id,))
        
        card = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        # 테스트 카드 여부 확인
        is_test_card = card['card_number'].endswith('4242') or card['card_number'].endswith('0077')
        
        return jsonify({
            'success': True,
            'message': '카드가 성공적으로 등록되었습니다.',
            'card': {
                'id': card['id'],
                'brand': detect_card_brand(card['card_number']),
                'maskedNumber': mask_card_number(card['card_number'], is_test_card),
                'fullNumber': card['card_number'] if is_test_card else None,
                'holderName': card['card_name'],
                'expiryDate': card['expiry_date'],
                'isDefault': bool(card['is_default']),
                'isTestCard': is_test_card,
                'createdAt': card['created_at'].isoformat(),
            }
        }), 201
        
    except Exception as e:
        print(f"[ERROR] Add card failed: {str(e)}")
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
        return jsonify({'error': f'카드 등록 실패: {str(e)}'}), 500

@card_bp.route('/api/cards/<int:card_id>/set-default', methods=['POST'])
@login_required
def set_default_card(card_id):
    """기본 카드 설정"""
    try:
        user_id = session.get('user_id')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 카드 소유권 확인
        cursor.execute("""
            SELECT id FROM registered_cards 
            WHERE id = %s AND user_id = %s
        """, (card_id, user_id))
        
        card = cursor.fetchone()
        if not card:
            cursor.close()
            conn.close()
            return jsonify({'error': '카드를 찾을 수 없습니다.'}), 404
        
        # 기존 기본 카드 해제
        cursor.execute("""
            UPDATE registered_cards 
            SET is_default = FALSE 
            WHERE user_id = %s
        """, (user_id,))
        
        # 새 기본 카드 설정
        cursor.execute("""
            UPDATE registered_cards 
            SET is_default = TRUE 
            WHERE id = %s
        """, (card_id,))
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': '기본 카드가 설정되었습니다.',
            'defaultCardId': card_id
        })
        
    except Exception as e:
        print(f"[ERROR] Set default card failed: {str(e)}")
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
        return jsonify({'error': f'기본 카드 설정 실패: {str(e)}'}), 500

@card_bp.route('/api/cards/<int:card_id>', methods=['DELETE'])
@login_required
def delete_card(card_id):
    """카드 삭제"""
    try:
        user_id = session.get('user_id')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 카드 소유권 확인
        cursor.execute("""
            SELECT is_default FROM registered_cards 
            WHERE id = %s AND user_id = %s
        """, (card_id, user_id))
        
        card = cursor.fetchone()
        if not card:
            cursor.close()
            conn.close()
            return jsonify({'error': '카드를 찾을 수 없습니다.'}), 404
        
        # 카드 삭제
        cursor.execute("""
            DELETE FROM registered_cards 
            WHERE id = %s
        """, (card_id,))
        
        # 삭제된 카드가 기본 카드였다면 다른 카드를 기본으로 설정
        if card['is_default']:
            cursor.execute("""
                SELECT id FROM registered_cards 
                WHERE user_id = %s 
                ORDER BY created_at ASC 
                LIMIT 1
            """, (user_id,))
            
            next_card = cursor.fetchone()
            if next_card:
                cursor.execute("""
                    UPDATE registered_cards 
                    SET is_default = TRUE 
                    WHERE id = %s
                """, (next_card['id'],))
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': '카드가 삭제되었습니다.'
        })
        
    except Exception as e:
        print(f"[ERROR] Delete card failed: {str(e)}")
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
        return jsonify({'error': f'카드 삭제 실패: {str(e)}'}), 500
