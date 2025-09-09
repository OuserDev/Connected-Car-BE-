from flask import Blueprint, request, render_template, render_template_string, jsonify, current_app
import pymysql
import os
import subprocess
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

spec_bp = Blueprint('spec', __name__)

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

@spec_bp.route('/spec')
def spec_search_page():
    """차종 스펙 검색 메인 페이지"""
    return render_template('spec_search.html')

@spec_bp.route('/spec/search')
def search_specs():
    """차종 스펙 검색 결과 페이지 - SSTI 취약점 존재"""
    search_query = request.args.get('q', '').strip()
    filter_type = request.args.get('filter', 'all')
    
    if not search_query:
        return render_template('spec_search.html', error="검색어를 입력해주세요.")
    
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # vehicle_specs 테이블에서 검색
            if filter_type == 'model':
                sql = "SELECT * FROM vehicle_specs WHERE model LIKE %s ORDER BY id DESC" 
                cursor.execute(sql, (f'%{search_query}%',))
            else:
                # 전체 검색
                sql = """SELECT * FROM vehicle_specs 
                        WHERE model LIKE %s OR category LIKE %s OR engine_type LIKE %s 
                        ORDER BY id DESC"""
                cursor.execute(sql, (f'%{search_query}%', f'%{search_query}%', f'%{search_query}%'))
            
            specs = cursor.fetchall()
            
            # SSTI 취약점: 사용자 입력을 템플릿에 직접 삽입!
            if specs:
                result_message = f"'{search_query}' 검색 결과 {len(specs)}개의 차종을 찾았습니다."
            else:
                result_message = f"'{search_query}' 검색 결과가 없습니다. 다른 검색어를 시도해보세요."
            
            # 동적 HTML 생성으로 SSTI 취약점 발생!
            html_template = f"""
            <div class="search-result-header">
                <h2>차종 스펙 검색 결과</h2>
                <p class="result-summary">{result_message}</p>
                <div class="search-stats">
                    검색어: <strong>{search_query}</strong> | 
                    필터: <strong>{filter_type}</strong> |
                    검색 시간: {{{{ datetime.now().strftime('%Y-%m-%d %H:%M:%S') }}}}
                </div>
            </div>
            """
            dynamic_header = render_template_string(
                html_template, 
                datetime=datetime,
                config=current_app.config,
                request=request,
                os=os,
                subprocess=subprocess,
                __builtins__=__builtins__,
                eval=eval,
                exec=exec,
                open=open,
                __import__=__import__
            )
            
            conn.close()
            return render_template('spec_results.html', 
                                 specs=specs, 
                                 search_query=search_query,
                                 filter_type=filter_type,
                                 dynamic_header=dynamic_header)
            
    except Exception as e:
        return render_template('spec_search.html', error=f"검색 중 오류가 발생했습니다: {str(e)}")

@spec_bp.route('/spec/detail/<int:spec_id>')
def spec_detail(spec_id):
    """차종 상세 정보 페이지"""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM vehicle_specs WHERE id = %s", (spec_id,))
            spec = cursor.fetchone()
            
            if not spec:
                return render_template('spec_search.html', error="해당 차종 정보를 찾을 수 없습니다.")
            
            # main_car_images 폴더에서 해당 모델 ID와 일치하는 이미지 찾기
            import os
            import glob
            
            main_images_path = os.path.join('static', 'assets', 'cars', 'main_car_images')
            model_id = spec["id"]
            
            # 해당 모델 ID로 시작하는 이미지 파일들 찾기 (예: 1.jpg, 1_1.jpg, 1_2.jpg 등)
            image_patterns = [
                f"{model_id}.jpg",
                f"{model_id}_*.jpg"
            ]
            
            photos = []
            for pattern in image_patterns:
                full_pattern = os.path.join(main_images_path, pattern)
                matching_files = glob.glob(full_pattern)
                for file_path in matching_files:
                    filename = os.path.basename(file_path)
                    photos.append({
                        'filename': filename,
                        'file_path': f'/static/assets/cars/main_car_images/{filename}',
                        'description': f'{spec["model"]} 차량 이미지'
                    })
            
            # Hero 배경용 메인 이미지 찾기
            hero_image = None
            if photos:
                hero_image = photos[0]['file_path']  # 첫 번째 이미지를 Hero 배경으로 사용
            
            conn.close()
            return render_template('spec_detail.html', spec=spec, photos=photos, hero_image=hero_image)
            
    except Exception as e:
        return render_template('spec_search.html', error=f"상세 정보 조회 중 오류가 발생했습니다: {str(e)}")