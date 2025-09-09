# controllers/photo_controller.py - 차량 사진 업로드 관리 (MySQL 기반)
import os
import uuid
import base64
from datetime import datetime
from flask import Blueprint, request, jsonify, session, current_app, send_from_directory
from PIL import Image
from io import BytesIO
from utils.auth import login_required
from models.base import DatabaseHelper, DatabaseConnection
import pymysql
from werkzeug.utils import secure_filename  # 경로 탈출 방지용

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
# ※ 실제 저장 경로는 get_upload_paths()에서 current_app.root_path 기준으로 계산함
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB
MAX_PHOTOS_PER_USER = 12
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_IMAGE_WIDTH = 1600
MIN_IMAGE_WIDTH = 320

# 실습 모드 스위치 (환경변수로 제어: VULN_LAB=1 이면 ON)
VULN_LAB = os.getenv('VULN_LAB', '0') == '1'
# 필요시 강제 실습 모드
VULN_LAB = True

# 실제 저장 디렉터리/URL 프리픽스 계산(항상 사용)
def get_upload_paths():
    """
    물리 저장 경로: <앱루트>/uploads/car_photos
    브라우저 접근 URL: /uploads/car_photos
    """
    upload_dir = os.path.join(current_app.root_path, 'uploads', 'car_photos')
    upload_url = '/uploads/car_photos'
    os.makedirs(upload_dir, exist_ok=True)
    return upload_dir, upload_url

def resize_image(image_data, max_width=MAX_IMAGE_WIDTH):
    """이미지 리사이징 처리 (안전 모드에서 사용)"""
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
        
        return processed_bytes, image.width, image.height, image.width, image.height
    
    except Exception as e:
        raise ValueError(f'이미지 처리 실패: {str(e)}')

@photo_bp.route('/api/car-photos/upload', methods=['POST'])
@login_required
def upload_car_photos():
    """차량 사진 업로드 (MySQL 저장)"""
    try:
        user_id = session.get('user_id')
        
        # 추가 보안 체크: 사용자 ID가 유효한지 확인
        if not user_id:
            return jsonify({'success': False, 'ok': False, 'error': '인증이 필요합니다.'}), 401

        # 요청 단위 실습 모드: 환경변수 OR 헤더 OR 쿼리
        lab_mode = VULN_LAB or request.headers.get('X-Lab-Mode') == '1' or request.args.get('lab') == '1'
        # 디버깅 로그
        print(f"[UPLOAD] user_id={user_id}, VULN_LAB={VULN_LAB}, lab_mode={lab_mode}, is_json={request.is_json}, file_keys={list(request.files.keys())}")

        # 현재 사진 개수 확인
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 사용자 존재 여부 확인
        cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
        if not cursor.fetchone():
            cursor.close(); conn.close()
            return jsonify({'success': False, 'ok': False, 'error': '유효하지 않은 사용자입니다.'}), 403
            
        cursor.execute("SELECT COUNT(*) as count FROM car_photos WHERE user_id = %s", (user_id,))
        current_count = cursor.fetchone()['count']
        
        if current_count >= MAX_PHOTOS_PER_USER:
            cursor.close(); conn.close()
            return jsonify({'success': False, 'ok': False,
                            'error': f'최대 {MAX_PHOTOS_PER_USER}장까지만 저장할 수 있습니다.'}), 400
        
        uploaded_count = 0

        # ---- Case 1: base64(JSON) 업로드 (안전 모드에서만 허용) ----
        if request.is_json and not lab_mode:
            data = request.get_json(silent=True) or {}
            images = data.get('images', [])
            if not isinstance(images, list):
                images = []

            for img_data in images:
                if current_count + uploaded_count >= MAX_PHOTOS_PER_USER:
                    break
                try:
                    processed_img, width, height, _, _ = resize_image(img_data)
                    photo_id = str(uuid.uuid4())
                    filename = f"{user_id}_{photo_id}.jpg"

                    upload_dir, upload_url = get_upload_paths()
                    filepath = os.path.join(upload_dir, filename)
                    with open(filepath, 'wb') as f:
                        f.write(processed_img)
                    print(f"[SAVE] upload_dir={upload_dir}")
                    print(f"[SAVE] filepath={filepath}")

                    file_url = f'{upload_url}/{filename}'
                    cursor.execute("""
                        INSERT INTO car_photos 
                        (user_id, photo_id, filename, file_path, file_url, file_size, width, height, mime_type)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (user_id, photo_id, filename, filepath, file_url,
                          len(processed_img), width, height, 'image/jpeg'))
                    uploaded_count += 1
                except Exception as e:
                    print(f"[UPLOAD][JSON] Image processing error: {e}")
                    # 안전 모드: 명확하게 실패 반환
                    cursor.close(); conn.close()
                    return jsonify({'success': False, 'ok': False,
                                    'error': '이미지 파일만 업로드할 수 있습니다.'}), 415

        # ---- Case 2: multipart/form-data 업로드 (실습/안전 모드 모두) ----
        else:
            # 필드명 호환: 'files' 우선, 없으면 'photos', 그래도 없으면 전체 values
            files = request.files.getlist('files') or request.files.getlist('photos')
            if not files and request.files:
                # 일부 클라이언트는 단일 파일만 보낼 때 키가 고정이 아닐 수 있음
                files = list(request.files.values())

            if not files:
                cursor.close(); conn.close()
                return jsonify({'success': False, 'ok': False,
                                'error': "업로드 파일 필드는 'files' 또는 'photos'로 보내야 합니다."}), 400

            for file in files:
                if current_count + uploaded_count >= MAX_PHOTOS_PER_USER:
                    break
                if not file or not file.filename:
                    continue

                # 파일 크기 검증 (안전 모드에서만 제한)
                file.seek(0, os.SEEK_END)
                raw_size = file.tell()
                file.seek(0)
                if raw_size > MAX_FILE_SIZE and not lab_mode:
                    print(f"[UPLOAD] Skip large file: {file.filename} ({raw_size} bytes)")
                    cursor.close(); conn.close()
                    return jsonify({'success': False, 'ok': False,
                                    'error': f'파일 크기 제한 {MAX_FILE_SIZE} 바이트를 초과했습니다.'}), 413

                original_filename = file.filename
                photo_id = str(uuid.uuid4())[:4]
                
                if lab_mode:
                    # === 실습 모드: 원본 파일을 가공 없이 그대로 저장 (확장자/내용 유지) ===
                    safe_name = secure_filename(original_filename)  # 경로 탈출 방지
                    filename = f"{user_id}_{photo_id}_{safe_name}"  # 충돌 방지용 접두

                    upload_dir, upload_url = get_upload_paths()
                    filepath = os.path.join(upload_dir, filename)
                    file.save(filepath)
                    print(f"[SAVE] upload_dir={upload_dir}")
                    print(f"[SAVE] filepath={filepath}")

                    file_size = os.path.getsize(filepath)
                    mime_type = file.mimetype or 'application/octet-stream'
                    width, height = 0, 0  # 이미지 아닐 수 있음 → 0 기록

                else:
                    # === 안전 모드: 이미지만 허용 + JPEG 재인코딩 ===
                    # 이미지 MIME이 아니면 즉시 거부 (415)
                    if not (file.mimetype or '').lower().startswith('image/'):
                        cursor.close(); conn.close()
                        return jsonify({'success': False, 'ok': False,
                                        'error': '이미지 파일만 업로드할 수 있습니다.'}), 415
                    try:
                        img_bytes = file.read()
                        img_b64 = base64.b64encode(img_bytes).decode()
                        processed_img, width, height, _, _ = resize_image(img_b64)

                        filename = f"{user_id}_{photo_id}.jpg"
                        upload_dir, upload_url = get_upload_paths()
                        filepath = os.path.join(upload_dir, filename)
                        with open(filepath, 'wb') as f:
                            f.write(processed_img)
                        print(f"[SAVE] upload_dir={upload_dir}")
                        print(f"[SAVE] filepath={filepath}")

                        file_size = len(processed_img)
                        mime_type = 'image/jpeg'
                    except Exception as e:
                        print(f"[UPLOAD][SAFE] File processing error: {e}")
                        cursor.close(); conn.close()
                        return jsonify({'success': False, 'ok': False,
                                        'error': '이미지 처리에 실패했습니다.'}), 415

                file_url = f'{upload_url}/{filename}'
                cursor.execute("""
                    INSERT INTO car_photos 
                    (user_id, photo_id, filename, original_filename, file_path, file_url, file_size, width, height, mime_type)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (user_id, photo_id, filename, original_filename, filepath, file_url,
                      file_size, width, height, mime_type))
                uploaded_count += 1

        # 트랜잭션 커밋
        conn.commit()

        # 업데이트된 사진 목록 조회
        cursor.execute("""
            SELECT photo_id, filename, original_filename, file_url, file_size, width, height, created_at
            FROM car_photos 
            WHERE user_id = %s 
            ORDER BY created_at DESC
        """, (user_id,))
        
        photos = []
        for row in cursor.fetchall():
            photos.append({
                'id': row['photo_id'],
                'filename': row['filename'],
                'original_filename': row.get('original_filename'),
                'url': row['file_url'],
                'file_size': row['file_size'],
                'width': row['width'],
                'height': row['height'],
                'created_at': row['created_at'].isoformat()
            })

        cursor.close(); conn.close()
        return jsonify({
            'success': True, 'ok': True,
            'message': f'{uploaded_count}개의 파일이 업로드되었습니다.',
            'photos': photos,
            'uploaded_count': uploaded_count,
            'uploadedCount': uploaded_count  # 프론트 호환용
        })

    except Exception as e:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()
        return jsonify({'success': False, 'ok': False, 'error': f'업로드 실패: {str(e)}'}), 500

@photo_bp.route('/api/car-photos', methods=['GET'])
@login_required
def get_car_photos():
    """사용자의 차량 사진 목록 조회"""
    try:
        user_id = session.get('user_id')
        
        # 추가 보안 체크: 사용자 ID가 유효한지 확인
        if not user_id:
            return jsonify({'success': False, 'ok': False, 'error': '인증이 필요합니다.'}), 401

        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 사용자 존재 여부 확인
        cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
        if not cursor.fetchone():
            cursor.close(); conn.close()
            return jsonify({'success': False, 'ok': False, 'error': '유효하지 않은 사용자입니다.'}), 403
        cursor.execute("""
            SELECT photo_id, filename, original_filename, file_url, file_size, width, height, is_main, created_at
            FROM car_photos 
            WHERE user_id = %s 
            ORDER BY created_at DESC
        """, (user_id,))
        
        photos = []
        main_photo_id = None
        for row in cursor.fetchall():
            photos.append({
                'id': row['photo_id'],
                'filename': row['filename'],
                'original_filename': row.get('original_filename'),
                'url': row['file_url'],
                'file_size': row['file_size'],
                'width': row['width'],
                'height': row['height'],
                'created_at': row['created_at'].isoformat()
            })
            if row['is_main']:
                main_photo_id = row['photo_id']

        cursor.close(); conn.close()
        return jsonify({
            'success': True, 'ok': True,
            'photos': photos,
            'main_photo_id': main_photo_id,
            'mainPhotoId': main_photo_id,   # 프론트 호환용
            'total_count': len(photos),
            'totalCount': len(photos)       # 프론트 호환용
        })

    except Exception as e:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()
        return jsonify({'success': False, 'ok': False, 'error': f'사진 조회 실패: {str(e)}'}), 500

@photo_bp.route('/api/car-photos/<photo_id>/set-main', methods=['POST'])
@login_required
def set_main_photo(photo_id):
    """메인 사진 설정 (트리거가 자동으로 다른 사진들을 is_main=FALSE로 변경)"""
    try:
        user_id = session.get('user_id')
        
        # 추가 보안 체크: 사용자 ID가 유효한지 확인
        if not user_id:
            return jsonify({'success': False, 'ok': False, 'error': '인증이 필요합니다.'}), 401

        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 사용자 존재 여부 확인
        cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
        if not cursor.fetchone():
            cursor.close(); conn.close()
            return jsonify({'success': False, 'ok': False, 'error': '유효하지 않은 사용자입니다.'}), 403
        cursor.execute("""
            SELECT id FROM car_photos 
            WHERE user_id = %s AND photo_id = %s
        """, (user_id, photo_id))
        if not cursor.fetchone():
            cursor.close(); conn.close()
            return jsonify({'success': False, 'ok': False, 'error': '존재하지 않는 사진이거나 접근 권한이 없습니다.'}), 404

        cursor.execute("""
            UPDATE car_photos 
            SET is_main = TRUE 
            WHERE user_id = %s AND photo_id = %s
        """, (user_id, photo_id))

        conn.commit()
        cursor.close(); conn.close()
        return jsonify({
            'success': True, 'ok': True,
            'message': '메인 사진이 설정되었습니다.',
            'main_photo_id': photo_id,
            'mainPhotoId': photo_id
        })

    except Exception as e:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()
        return jsonify({'success': False, 'ok': False, 'error': f'메인 사진 설정 실패: {str(e)}'}), 500

@photo_bp.route('/api/car-photos/<photo_id>', methods=['DELETE'])
@login_required
def delete_car_photo(photo_id):
    """차량 사진 삭제"""
    try:
        user_id = session.get('user_id')
        
        # 추가 보안 체크: 사용자 ID가 유효한지 확인
        if not user_id:
            return jsonify({'success': False, 'ok': False, 'error': '인증이 필요합니다.'}), 401

        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 사용자 존재 여부 확인
        cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
        if not cursor.fetchone():
            cursor.close(); conn.close()
            return jsonify({'success': False, 'ok': False, 'error': '유효하지 않은 사용자입니다.'}), 403
        cursor.execute("""
            SELECT filename, file_path, is_main 
            FROM car_photos 
            WHERE user_id = %s AND photo_id = %s
        """, (user_id, photo_id))
        photo_info = cursor.fetchone()
        if not photo_info:
            cursor.close(); conn.close()
            return jsonify({'success': False, 'ok': False, 'error': '존재하지 않는 사진이거나 접근 권한이 없습니다.'}), 404

        cursor.execute("""
            DELETE FROM car_photos 
            WHERE user_id = %s AND photo_id = %s
        """, (user_id, photo_id))

        try:
            if os.path.exists(photo_info['file_path']):
                os.remove(photo_info['file_path'])
        except:
            pass  # 파일 삭제 실패해도 DB 삭제는 유지

        if photo_info['is_main']:
            cursor.execute("""
                UPDATE car_photos 
                SET is_main = TRUE 
                WHERE user_id = %s 
                ORDER BY created_at DESC 
                LIMIT 1
            """, (user_id,))

        conn.commit()

        cursor.execute("""
            SELECT photo_id, filename, file_url, file_size, is_main, created_at
            FROM car_photos 
            WHERE user_id = %s 
            ORDER BY created_at DESC
        """, (user_id,))
        photos = []
        main_photo_id = None
        for row in cursor.fetchall():
            photos.append({
                'id': row['photo_id'],
                'filename': row['filename'],
                'url': row['file_url'],
                'file_size': row['file_size'],
                'created_at': row['created_at'].isoformat()
            })
            if row['is_main']:
                main_photo_id = row['photo_id']

        cursor.close(); conn.close()
        return jsonify({
            'success': True, 'ok': True,
            'message': '사진이 삭제되었습니다.',
            'photos': photos,
            'main_photo_id': main_photo_id,
            'mainPhotoId': main_photo_id
        })

    except Exception as e:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()
        return jsonify({'success': False, 'ok': False, 'error': f'사진 삭제 실패: {str(e)}'}), 500

@photo_bp.route('/api/car-photos/clear', methods=['DELETE'])
@login_required
def clear_all_photos():
    """모든 차량 사진 삭제"""
    try:
        user_id = session.get('user_id')
        
        # 추가 보안 체크: 사용자 ID가 유효한지 확인
        if not user_id:
            return jsonify({'success': False, 'ok': False, 'error': '인증이 필요합니다.'}), 401

        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 사용자 존재 여부 확인
        cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
        if not cursor.fetchone():
            cursor.close(); conn.close()
            return jsonify({'success': False, 'ok': False, 'error': '유효하지 않은 사용자입니다.'}), 403
        cursor.execute("SELECT file_path FROM car_photos WHERE user_id = %s", (user_id,))
        file_paths = [row['file_path'] for row in cursor.fetchall()]

        cursor.execute("DELETE FROM car_photos WHERE user_id = %s", (user_id,))
        conn.commit()

        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except:
                pass

        cursor.close(); conn.close()
        return jsonify({
            'success': True, 'ok': True,
            'message': f'{len(file_paths)}개의 사진이 모두 삭제되었습니다.',
            'photos': [],
            'main_photo_id': None,
            'mainPhotoId': None
        })

    except Exception as e:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()
        return jsonify({'success': False, 'ok': False, 'error': f'전체 삭제 실패: {str(e)}'}), 500

# 업로드된 파일을 /uploads/... 로 서빙하는 라우트
@photo_bp.get('/uploads/car_photos/<path:filename>')
def serve_uploaded_photo(filename):
    upload_dir, _ = get_upload_paths()
    return send_from_directory(upload_dir, filename)
