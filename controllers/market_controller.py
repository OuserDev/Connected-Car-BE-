# controllers/market_controller.py - 중고장터 게시판 CRUD
from flask import Blueprint, request, jsonify, session
from utils.auth import login_required
from models.base import DatabaseHelper, DatabaseConnection
import pymysql
from datetime import datetime

market_bp = Blueprint('market', __name__)

# 간편한 DB 연결 함수
def get_db_connection():
    """데이터베이스 연결 반환"""
    return pymysql.connect(
        host='localhost',
        port=3307,
        user='admin',
        password='STRONGMAN',
        database='connected_car_service',
        charset='utf8mb4',
        autocommit=True,
        cursorclass=pymysql.cursors.DictCursor
    )

@market_bp.route('/api/market/posts', methods=['GET'])
def get_market_posts():
    """중고장터 게시글 목록 조회 (로그인 불필요)"""
    try:
        # 페이지네이션 파라미터
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        status = request.args.get('status', 'all')  # all, sale, reserved, sold
        
        offset = (page - 1) * limit
        
        # 상태별 필터링
        status_condition = ""
        params = []
        if status != 'all':
            status_condition = "WHERE status = %s"
            params.append(status)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # 전체 개수 조회
            count_query = f"SELECT COUNT(*) as total FROM used_market {status_condition}"
            cursor.execute(count_query, params)
            total_count = cursor.fetchone()['total']
        except Exception as e:
            # 테이블이 없으면 빈 결과 반환
            if "doesn't exist" in str(e) or "Table" in str(e):
                cursor.close()
                conn.close()
                return jsonify({
                    'success': True,
                    'posts': [],
                    'pagination': {
                        'current_page': page,
                        'total_count': 0,
                        'total_pages': 0,
                        'has_next': False,
                        'has_prev': False
                    }
                })
            else:
                raise e
        
        # 게시글 목록 조회 (최신순)
        list_query = f"""
            SELECT 
                um.id, um.title, um.body, um.price, um.status, um.view_count, um.created_at,
                u.username, u.name as seller_name
            FROM used_market um
            JOIN users u ON um.user_id = u.id
            {status_condition}
            ORDER BY um.created_at DESC
            LIMIT %s OFFSET %s
        """
        
        list_params = params + [limit, offset]
        cursor.execute(list_query, list_params)
        posts = cursor.fetchall()
        
        # 게시글 데이터 포맷팅
        formatted_posts = []
        for post in posts:
            formatted_posts.append({
                'id': post['id'],
                'title': post['title'],
                'body': post['body'][:100] + ('...' if len(post['body']) > 100 else ''),  # 미리보기용 요약
                'price': post['price'],
                'status': post['status'],
                'view_count': post['view_count'],
                'seller': post['seller_name'] or post['username'],
                'created_at': post['created_at'].isoformat(),
            })
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'posts': formatted_posts,
            'pagination': {
                'current_page': page,
                'total_count': total_count,
                'total_pages': (total_count + limit - 1) // limit,
                'has_next': offset + limit < total_count,
                'has_prev': page > 1
            }
        })
        
    except Exception as e:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
        return jsonify({'error': f'게시글 목록 조회 실패: {str(e)}'}), 500

@market_bp.route('/api/market/posts/<int:post_id>', methods=['GET'])
def get_market_post(post_id):
    """중고장터 게시글 상세 조회 (조회수 증가)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 조회수 증가
        cursor.execute("UPDATE used_market SET view_count = view_count + 1 WHERE id = %s", (post_id,))
        
        # 게시글 상세 정보 조회
        cursor.execute("""
            SELECT 
                um.id, um.user_id, um.title, um.body, um.price, um.status, um.view_count, 
                um.created_at, um.updated_at,
                u.username, u.name as seller_name
            FROM used_market um
            JOIN users u ON um.user_id = u.id
            WHERE um.id = %s
        """, (post_id,))
        
        post = cursor.fetchone()
        
        if not post:
            cursor.close()
            conn.close()
            return jsonify({'error': '게시글을 찾을 수 없습니다.'}), 404
        
        # 현재 사용자가 작성자인지 확인
        current_user_id = session.get('user_id')
        is_author = current_user_id == post['user_id']
        
        post_data = {
            'id': post['id'],
            'title': post['title'],
            'body': post['body'],
            'price': post['price'],
            'status': post['status'],
            'view_count': post['view_count'],
            'seller': post['seller_name'] or post['username'],
            'seller_id': post['user_id'],
            'created_at': post['created_at'].isoformat(),
            'updated_at': post['updated_at'].isoformat() if post['updated_at'] else None,
            'is_author': is_author  # 수정/삭제 권한 확인용
        }
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'post': post_data
        })
        
    except Exception as e:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
        return jsonify({'error': f'게시글 조회 실패: {str(e)}'}), 500

@market_bp.route('/api/market/posts', methods=['POST'])
@login_required
def create_market_post():
    """중고장터 게시글 작성"""
    try:
        user_id = session.get('user_id')
        data = request.get_json()
        
        print(f"[DEBUG] Market post creation attempt by user_id: {user_id}")
        print(f"[DEBUG] Request data: {data}")
        
        # 입력 데이터 검증
        title = data.get('title', '').strip()
        body = data.get('body', '').strip()
        price = data.get('price', 0)
        
        print(f"[DEBUG] Parsed data - title: '{title}', body length: {len(body)}, price: {price}")
        
        if not title:
            return jsonify({'error': '제목을 입력해주세요.'}), 400
        
        if len(title) > 200:
            return jsonify({'error': '제목은 200자 이내로 입력해주세요.'}), 400
            
        if len(body) > 5000:
            return jsonify({'error': '내용은 5000자 이내로 입력해주세요.'}), 400
        
        # 가격 처리 개선
        try:
            if isinstance(price, str):
                # 문자열에서 숫자만 추출
                price_str = ''.join(filter(str.isdigit, price))
                price = int(price_str) if price_str else 0
            else:
                price = int(price) if price else 0
                
            if price < 0:
                return jsonify({'error': '가격은 0원 이상으로 입력해주세요.'}), 400
        except (ValueError, TypeError) as e:
            print(f"[ERROR] Price parsing error: {e}")
            return jsonify({'error': '올바른 가격을 입력해주세요.'}), 400
        
        print("[DEBUG] Attempting database connection...")
        conn = get_db_connection()
        cursor = conn.cursor()
        print("[DEBUG] Database connection successful")
        
        # 게시글 생성
        print(f"[DEBUG] Inserting post: user_id={user_id}, title='{title}', price={price}")
        cursor.execute("""
            INSERT INTO used_market (user_id, title, body, price)
            VALUES (%s, %s, %s, %s)
        """, (user_id, title, body, price))
        
        post_id = cursor.lastrowid
        print(f"[DEBUG] Post created with ID: {post_id}")
        
        # 생성된 게시글 정보 반환
        cursor.execute("""
            SELECT 
                um.id, um.title, um.body, um.price, um.status, um.view_count, um.created_at,
                u.username, u.name as seller_name
            FROM used_market um
            JOIN users u ON um.user_id = u.id
            WHERE um.id = %s
        """, (post_id,))
        
        post = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': '게시글이 작성되었습니다.',
            'post': {
                'id': post['id'],
                'title': post['title'],
                'body': post['body'],
                'price': post['price'],
                'status': post['status'],
                'view_count': post['view_count'],
                'seller': post['seller_name'] or post['username'],
                'created_at': post['created_at'].isoformat()
            }
        }), 201
        
    except Exception as e:
        print(f"[ERROR] Market post creation error: {str(e)}")
        print(f"[ERROR] Error type: {type(e).__name__}")
        import traceback
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
        return jsonify({'error': f'게시글 작성 실패: {str(e)}'}), 500

@market_bp.route('/api/market/posts/<int:post_id>', methods=['PUT'])
@login_required
def update_market_post(post_id):
    """중고장터 게시글 수정 (작성자만 가능)"""
    try:
        user_id = session.get('user_id')
        data = request.get_json()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 작성자 권한 확인
        cursor.execute("SELECT user_id FROM used_market WHERE id = %s", (post_id,))
        post = cursor.fetchone()
        
        if not post:
            cursor.close()
            conn.close()
            return jsonify({'error': '게시글을 찾을 수 없습니다.'}), 404
        
        if post['user_id'] != user_id:
            cursor.close()
            conn.close()
            return jsonify({'error': '수정 권한이 없습니다.'}), 403
        
        # 입력 데이터 검증
        title = data.get('title', '').strip()
        body = data.get('body', '').strip()
        price = data.get('price')
        status = data.get('status')
        
        update_fields = []
        update_params = []
        
        if title:
            if len(title) > 200:
                cursor.close()
                conn.close()
                return jsonify({'error': '제목은 200자 이내로 입력해주세요.'}), 400
            update_fields.append("title = %s")
            update_params.append(title)
        
        if body is not None:  # 빈 문자열도 허용
            if len(body) > 5000:
                cursor.close()
                conn.close()
                return jsonify({'error': '내용은 5000자 이내로 입력해주세요.'}), 400
            update_fields.append("body = %s")
            update_params.append(body)
        
        if price is not None:
            try:
                price = int(price)
                if price < 0:
                    cursor.close()
                    conn.close()
                    return jsonify({'error': '가격은 0원 이상으로 입력해주세요.'}), 400
                update_fields.append("price = %s")
                update_params.append(price)
            except (ValueError, TypeError):
                cursor.close()
                conn.close()
                return jsonify({'error': '올바른 가격을 입력해주세요.'}), 400
        
        if status and status in ['sale', 'reserved', 'sold']:
            update_fields.append("status = %s")
            update_params.append(status)
        
        if not update_fields:
            cursor.close()
            conn.close()
            return jsonify({'error': '수정할 내용이 없습니다.'}), 400
        
        # 게시글 업데이트
        update_query = f"UPDATE used_market SET {', '.join(update_fields)} WHERE id = %s"
        update_params.append(post_id)
        
        cursor.execute(update_query, update_params)
        
        # 업데이트된 게시글 정보 반환
        cursor.execute("""
            SELECT 
                um.id, um.title, um.body, um.price, um.status, um.view_count, 
                um.created_at, um.updated_at,
                u.username, u.name as seller_name
            FROM used_market um
            JOIN users u ON um.user_id = u.id
            WHERE um.id = %s
        """, (post_id,))
        
        updated_post = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': '게시글이 수정되었습니다.',
            'post': {
                'id': updated_post['id'],
                'title': updated_post['title'],
                'body': updated_post['body'],
                'price': updated_post['price'],
                'status': updated_post['status'],
                'view_count': updated_post['view_count'],
                'seller': updated_post['seller_name'] or updated_post['username'],
                'created_at': updated_post['created_at'].isoformat(),
                'updated_at': updated_post['updated_at'].isoformat() if updated_post['updated_at'] else None
            }
        })
        
    except Exception as e:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
        return jsonify({'error': f'게시글 수정 실패: {str(e)}'}), 500

@market_bp.route('/api/market/posts/<int:post_id>', methods=['DELETE'])
@login_required
def delete_market_post(post_id):
    """중고장터 게시글 삭제 (작성자만 가능)"""
    try:
        user_id = session.get('user_id')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 작성자 권한 확인
        cursor.execute("SELECT user_id, title FROM used_market WHERE id = %s", (post_id,))
        post = cursor.fetchone()
        
        if not post:
            cursor.close()
            conn.close()
            return jsonify({'error': '게시글을 찾을 수 없습니다.'}), 404
        
        if post['user_id'] != user_id:
            cursor.close()
            conn.close()
            return jsonify({'error': '삭제 권한이 없습니다.'}), 403
        
        # 게시글 삭제
        cursor.execute("DELETE FROM used_market WHERE id = %s", (post_id,))
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': '게시글이 삭제되었습니다.'
        })
        
    except Exception as e:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
        return jsonify({'error': f'게시글 삭제 실패: {str(e)}'}), 500

@market_bp.route('/api/market/my-posts', methods=['GET'])
@login_required
def get_my_market_posts():
    """내가 작성한 중고장터 게시글 목록 조회"""
    try:
        user_id = session.get('user_id')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 내 게시글 목록 조회
        cursor.execute("""
            SELECT id, title, body, price, status, view_count, created_at, updated_at
            FROM used_market 
            WHERE user_id = %s 
            ORDER BY created_at DESC
        """, (user_id,))
        
        posts = cursor.fetchall()
        
        formatted_posts = []
        for post in posts:
            formatted_posts.append({
                'id': post['id'],
                'title': post['title'],
                'body': post['body'][:100] + ('...' if len(post['body']) > 100 else ''),
                'price': post['price'],
                'status': post['status'],
                'view_count': post['view_count'],
                'created_at': post['created_at'].isoformat(),
                'updated_at': post['updated_at'].isoformat() if post['updated_at'] else None
            })
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'posts': formatted_posts,
            'total_count': len(formatted_posts)
        })
        
    except Exception as e:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
        return jsonify({'error': f'내 게시글 조회 실패: {str(e)}'}), 500
