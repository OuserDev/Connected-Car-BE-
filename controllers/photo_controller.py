# controllers/photo_controller.py - 차량 사진 업로드 관리 (MySQL 기반)
import os
import uuid
import base64
from datetime import datetime
from flask import Blueprint, request, jsonify, session
from PIL import Image
from io import BytesIO
from utils.auth import login_required
from models.base import DatabaseHelper, DatabaseConnection
import pymysql

photo_bp = Blueprint('photo', __name__)

# 간편한 DB 연결 함수
def get_db_connection():
    """데이터베이스 연결 반환"""
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

# 설정 상수
UPLOAD_FOLDER = 'static/uploads/car_photos'
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB
MAX_PHOTOS_PER_USER = 12
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_IMAGE_WIDTH = 1600
MIN_IMAGE_WIDTH = 320

# 업로드 폴더 생성
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def resize_image(image_data, max_width=MAX_IMAGE_WIDTH):
    """이미지 리사이징 처리"""
    try:
        # base64 데이터에서 이미지 추출
        if isinstance(image_data, str) and image_data.startswith('data:image'):
            # data:image/jpeg;base64,... 형태에서 실제 데이터 추출
            image_data = image_data.split(',')[1]
        
        # base64 디코딩
        img_bytes = base64.b64decode(image_data)
        image = Image.open(BytesIO(img_bytes))
        
        # 크기 검증
        if image.width < MIN_IMAGE_WIDTH:
            raise ValueError(f'이미지 가로폭이 너무 작습니다. 최소 {MIN_IMAGE_WIDTH}px 이상이어야 합니다.')
        
        # 원본 크기 정보 저장
        original_width = image.width
        original_height = image.height
        
        # 리사이징 필요한지 확인
        if image.width > max_width:
            ratio = max_width / image.width
            new_height = int(image.height * ratio)
            image = image.resize((max_width, new_height), Image.Resampling.LANCZOS)
        
        # JPEG로 변환 (압축)
        output = BytesIO()
        if image.mode in ('RGBA', 'LA', 'P'):
            # 투명도가 있는 이미지는 배경을 흰색으로 변환
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = background
        
        image.save(output, format='JPEG', quality=85, optimize=True)
        processed_bytes = output.getvalue()
        
        return processed_bytes, image.width, image.height, original_width, original_height
    
    except Exception as e:
        raise ValueError(f'이미지 처리 실패: {str(e)}')

@photo_bp.route('/api/car-photos/upload', methods=['POST'])
@login_required
def upload_car_photos():
    """차량 사진 업로드 (MySQL 저장)"""
    try:
        user_id = session.get('user_id')
        
        # 현재 사진 개수 확인
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as count FROM car_photos WHERE user_id = %s", (user_id,))
        current_count = cursor.fetchone()['count']
        
        if current_count >= MAX_PHOTOS_PER_USER:
            cursor.close()
            conn.close()
            return jsonify({
                'error': f'최대 {MAX_PHOTOS_PER_USER}장까지만 저장할 수 있습니다.'
            }), 400
        
        uploaded_count = 0
        
        # Case 1: base64 데이터로 업로드 (프론트엔드에서 처리된 이미지)
        if request.is_json:
            data = request.get_json()
            images = data.get('images', [])
            
            for img_data in images:
                if current_count + uploaded_count >= MAX_PHOTOS_PER_USER:
                    break
                
                try:
                    # 이미지 처리
                    processed_img, width, height, orig_w, orig_h = resize_image(img_data)
                    
                    # 고유 ID 생성
                    photo_id = str(uuid.uuid4())
                    filename = f"{user_id}_{photo_id}.jpg"
                    filepath = os.path.join(UPLOAD_FOLDER, filename)
                    
                    # 파일 저장
                    with open(filepath, 'wb') as f:
                        f.write(processed_img)
                    
                    # DB에 메타데이터 저장
                    file_url = f'/static/uploads/car_photos/{filename}'
                    cursor.execute("""
                        INSERT INTO car_photos 
                        (user_id, photo_id, filename, file_path, file_url, file_size, width, height, mime_type)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        user_id, photo_id, filename, filepath, file_url,
                        len(processed_img), width, height, 'image/jpeg'
                    ))
                    
                    uploaded_count += 1
                    
                except Exception as e:
                    print(f"Image processing error: {e}")
                    continue  # 개별 이미지 실패 시 다음 이미지 처리 계속
        
        # Case 2: 일반 파일 업로드
        else:
            files = request.files.getlist('photos')
            
            for file in files:
                if current_count + uploaded_count >= MAX_PHOTOS_PER_USER:
                    break
                
                if file and file.filename:
                    try:
                        # 파일 크기 검증
                        file.seek(0, os.SEEK_END)
                        file_size = file.tell()
                        file.seek(0)
                        
                        if file_size > MAX_FILE_SIZE:
                            continue  # 큰 파일은 스킵
                        
                        # 이미지 처리
                        img_bytes = file.read()
                        img_b64 = base64.b64encode(img_bytes).decode()
                        processed_img, width, height, orig_w, orig_h = resize_image(img_b64)
                        
                        # 고유 ID 생성
                        photo_id = str(uuid.uuid4())
                        filename = f"{user_id}_{photo_id}.jpg"
                        filepath = os.path.join(UPLOAD_FOLDER, filename)
                        
                        # 파일 저장
                        with open(filepath, 'wb') as f:
                            f.write(processed_img)
                        
                        # DB에 메타데이터 저장
                        file_url = f'/static/uploads/car_photos/{filename}'
                        cursor.execute("""
                            INSERT INTO car_photos 
                            (user_id, photo_id, filename, original_filename, file_path, file_url, file_size, width, height, mime_type)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            user_id, photo_id, filename, file.filename, filepath, file_url,
                            len(processed_img), width, height, 'image/jpeg'
                        ))
                        
                        uploaded_count += 1
                        
                    except Exception as e:
                        print(f"File processing error: {e}")
                        continue
        
        # 트랜잭션 커밋
        conn.commit()
        
        # 업데이트된 사진 목록 조회
        cursor.execute("""
            SELECT photo_id, filename, file_url, file_size, width, height, created_at
            FROM car_photos 
            WHERE user_id = %s 
            ORDER BY created_at DESC
        """, (user_id,))
        
        photos = []
        for row in cursor.fetchall():
            photos.append({
                'id': row['photo_id'],
                'filename': row['filename'],
                'url': row['file_url'],
                'file_size': row['file_size'],
                'width': row['width'],
                'height': row['height'],
                'created_at': row['created_at'].isoformat()
            })
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'{uploaded_count}장의 사진이 업로드되었습니다.',
            'photos': photos,
            'uploaded_count': uploaded_count
        })
        
    except Exception as e:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
        return jsonify({'error': f'업로드 실패: {str(e)}'}), 500

@photo_bp.route('/api/car-photos', methods=['GET'])
@login_required
def get_car_photos():
    """사용자의 차량 사진 목록 조회"""
    try:
        user_id = session.get('user_id')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 사진 목록 조회 (최신순)
        cursor.execute("""
            SELECT photo_id, filename, original_filename, file_url, file_size, width, height, is_main, created_at
            FROM car_photos 
            WHERE user_id = %s 
            ORDER BY created_at DESC
        """, (user_id,))
        
        photos = []
        main_photo_id = None
        
        for row in cursor.fetchall():
            photo_data = {
                'id': row['photo_id'],
                'filename': row['filename'],
                'original_filename': row['original_filename'],
                'url': row['file_url'],
                'file_size': row['file_size'],
                'width': row['width'],
                'height': row['height'],
                'created_at': row['created_at'].isoformat()
            }
            photos.append(photo_data)
            
            if row['is_main']:
                main_photo_id = row['photo_id']
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'photos': photos,
            'main_photo_id': main_photo_id,
            'total_count': len(photos)
        })
        
    except Exception as e:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
        return jsonify({'error': f'사진 조회 실패: {str(e)}'}), 500

@photo_bp.route('/api/car-photos/<photo_id>/set-main', methods=['POST'])
@login_required
def set_main_photo(photo_id):
    """메인 사진 설정 (트리거가 자동으로 다른 사진들을 is_main=FALSE로 변경)"""
    try:
        user_id = session.get('user_id')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 해당 사진이 사용자의 것인지 확인
        cursor.execute("""
            SELECT id FROM car_photos 
            WHERE user_id = %s AND photo_id = %s
        """, (user_id, photo_id))
        
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'error': '존재하지 않는 사진이거나 접근 권한이 없습니다.'}), 404
        
        # 메인 사진으로 설정 (트리거가 자동으로 다른 사진들 처리)
        cursor.execute("""
            UPDATE car_photos 
            SET is_main = TRUE 
            WHERE user_id = %s AND photo_id = %s
        """, (user_id, photo_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': '메인 사진이 설정되었습니다.',
            'main_photo_id': photo_id
        })
        
    except Exception as e:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
        return jsonify({'error': f'메인 사진 설정 실패: {str(e)}'}), 500

@photo_bp.route('/api/car-photos/<photo_id>', methods=['DELETE'])
@login_required
def delete_car_photo(photo_id):
    """차량 사진 삭제"""
    try:
        user_id = session.get('user_id')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 해당 사진 정보 조회 (파일 삭제를 위해)
        cursor.execute("""
            SELECT filename, file_path, is_main 
            FROM car_photos 
            WHERE user_id = %s AND photo_id = %s
        """, (user_id, photo_id))
        
        photo_info = cursor.fetchone()
        if not photo_info:
            cursor.close()
            conn.close()
            return jsonify({'error': '존재하지 않는 사진이거나 접근 권한이 없습니다.'}), 404
        
        # DB에서 삭제
        cursor.execute("""
            DELETE FROM car_photos 
            WHERE user_id = %s AND photo_id = %s
        """, (user_id, photo_id))
        
        # 실제 파일 삭제
        try:
            if os.path.exists(photo_info['file_path']):
                os.remove(photo_info['file_path'])
        except:
            pass  # 파일 삭제 실패해도 DB 삭제는 유지
        
        # 메인 사진이 삭제된 경우, 남은 사진 중 가장 최근 것을 메인으로 설정
        if photo_info['is_main']:
            cursor.execute("""
                UPDATE car_photos 
                SET is_main = TRUE 
                WHERE user_id = %s 
                ORDER BY created_at DESC 
                LIMIT 1
            """, (user_id,))
        
        conn.commit()
        
        # 업데이트된 사진 목록 반환
        cursor.execute("""
            SELECT photo_id, filename, file_url, file_size, is_main, created_at
            FROM car_photos 
            WHERE user_id = %s 
            ORDER BY created_at DESC
        """, (user_id,))
        
        photos = []
        main_photo_id = None
        
        for row in cursor.fetchall():
            photo_data = {
                'id': row['photo_id'],
                'filename': row['filename'],
                'url': row['file_url'],
                'file_size': row['file_size'],
                'created_at': row['created_at'].isoformat()
            }
            photos.append(photo_data)
            
            if row['is_main']:
                main_photo_id = row['photo_id']
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': '사진이 삭제되었습니다.',
            'photos': photos,
            'main_photo_id': main_photo_id
        })
        
    except Exception as e:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
        return jsonify({'error': f'사진 삭제 실패: {str(e)}'}), 500

@photo_bp.route('/api/car-photos/clear', methods=['DELETE'])
@login_required
def clear_all_photos():
    """모든 차량 사진 삭제"""
    try:
        user_id = session.get('user_id')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 삭제할 파일들 목록 조회
        cursor.execute("""
            SELECT file_path FROM car_photos WHERE user_id = %s
        """, (user_id,))
        
        file_paths = [row['file_path'] for row in cursor.fetchall()]
        
        # DB에서 모든 사진 삭제
        cursor.execute("DELETE FROM car_photos WHERE user_id = %s", (user_id,))
        conn.commit()
        
        # 실제 파일들 삭제
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except:
                pass
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'{len(file_paths)}개의 사진이 모두 삭제되었습니다.',
            'photos': [],
            'main_photo_id': None
        })
        
    except Exception as e:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
        return jsonify({'error': f'전체 삭제 실패: {str(e)}'}), 500
