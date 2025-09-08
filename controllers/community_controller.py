# 커뮤니티 (공지사항/FAQ) API 컨트롤러
from flask import Blueprint, jsonify
import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

community_bp = Blueprint('community', __name__)

def get_admin_db_connection():
    """admin_db 데이터베이스 연결"""
    return pymysql.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 3306)),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', 'student'),
        database=os.getenv('admin_db'),
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

@community_bp.route('/api/community/notices', methods=['GET'])
def get_notices():
    """공지사항 조회"""
    try:
        conn = get_admin_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, title, content, created_at, updated_at 
                FROM community 
                WHERE type = 'notice' 
                ORDER BY created_at DESC 
                LIMIT 10
            """)
            notices = cursor.fetchall()
            
        conn.close()
        
        return jsonify({
            'success': True,
            'data': notices
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'공지사항 조회 실패: {str(e)}'
        }), 500

@community_bp.route('/api/community/faqs', methods=['GET'])
def get_faqs():
    """FAQ 조회"""
    try:
        conn = get_admin_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, title, content, created_at, updated_at 
                FROM community 
                WHERE type = 'faq' 
                ORDER BY created_at DESC 
                LIMIT 10
            """)
            faqs = cursor.fetchall()
            
        conn.close()
        
        return jsonify({
            'success': True,
            'data': faqs
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'FAQ 조회 실패: {str(e)}'
        }), 500

@community_bp.route('/api/community/all', methods=['GET'])
def get_all_community():
    """공지사항과 FAQ 모두 조회"""
    try:
        conn = get_admin_db_connection()
        with conn.cursor() as cursor:
            # 공지사항 조회
            cursor.execute("""
                SELECT id, title, content, created_at, updated_at 
                FROM community 
                WHERE type = 'notice' 
                ORDER BY created_at DESC 
                LIMIT 5
            """)
            notices = cursor.fetchall()
            
            # FAQ 조회
            cursor.execute("""
                SELECT id, title, content, created_at, updated_at 
                FROM community 
                WHERE type = 'faq' 
                ORDER BY created_at DESC 
                LIMIT 5
            """)
            faqs = cursor.fetchall()
            
        conn.close()
        
        return jsonify({
            'success': True,
            'data': {
                'notices': notices,
                'faqs': faqs
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'커뮤니티 데이터 조회 실패: {str(e)}'
        }), 500