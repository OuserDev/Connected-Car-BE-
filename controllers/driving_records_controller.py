# 주행 기록 관리 API 컨트롤러
from flask import Blueprint, jsonify, request, session, send_from_directory, abort
from models.car import Car
from utils.auth import login_required
import json
import os
from datetime import datetime

driving_records_bp = Blueprint('driving_records', __name__)

# 주행 기록 데이터 파일 경로
DRIVING_RECORDS_FILE = 'data/driving_records.json'

def load_driving_records():
    """주행 기록 데이터 로드"""
    try:
        print(f"🔍 Debug: 파일 경로 확인: {DRIVING_RECORDS_FILE}")
        print(f"🔍 Debug: 파일 존재 여부: {os.path.exists(DRIVING_RECORDS_FILE)}")
        
        if os.path.exists(DRIVING_RECORDS_FILE):
            with open(DRIVING_RECORDS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"🔍 Debug: 로드된 데이터 구조: {type(data)}")
                print(f"🔍 Debug: 데이터 키들: {data.keys() if isinstance(data, dict) else 'Not dict'}")
                if isinstance(data, dict) and 'trips' in data:
                    print(f"🔍 Debug: trips 개수: {len(data['trips'])}")
                return data
    except Exception as e:
        print(f"❌ Debug: 파일 로드 오류: {e}")
    return {}

def save_driving_records(records):
    """주행 기록 데이터 저장"""
    with open(DRIVING_RECORDS_FILE, 'w', encoding='utf-8') as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

# 사용자의 주행 기록 조회 API
@driving_records_bp.route('/api/driving/records', methods=['GET'])
@login_required
def get_driving_records():
    """로그인한 사용자의 주행 기록 조회"""
    try:
        user_id = session.get('user_id')
        print(f"🔍 Debug: user_id from session: {user_id}")
        print(f"🔍 Debug: full session: {dict(session)}")
        
        # 사용자 소유 차량 목록 조회
        user_cars = Car.get_by_owner(user_id)
        user_car_ids = [car['id'] for car in user_cars]
        print(f"🔍 Debug: user_cars: {user_cars}")
        print(f"🔍 Debug: user_car_ids: {user_car_ids}")
        
        # 주행 기록 로드
        all_data = load_driving_records()
        all_trips = all_data.get('trips', []) if all_data else []
        
        # 사용자 차량의 주행 기록만 필터링
        user_records = [
            record for record in all_trips 
            if record.get('car_id') in user_car_ids
        ]
        
        print(f"🔍 Debug: user_id={user_id}, user_car_ids={user_car_ids}")
        print(f"🔍 Debug: total_trips={len(all_trips)}, user_records={len(user_records)}")
        print(f"🔍 Debug: user_records={user_records[:2]}")  # 처음 2개만 출력
        
        return jsonify({
            'success': True,
            'data': user_records
        })
        
    except Exception as e:
        return jsonify({'error': f'주행 기록 조회 실패: {str(e)}'}), 500

# 특정 차량의 주행 기록 조회 API
@driving_records_bp.route('/api/driving/records/<int:car_id>', methods=['GET'])
@login_required
def get_car_driving_records(car_id):
    """특정 차량의 주행 기록 조회"""
    try:
        user_id = session.get('user_id')
        
        # 차량 소유권 확인
        car = Car.get_by_id(car_id)
        if not car or car.get('owner_id') != user_id:
            return jsonify({'error': '해당 차량에 대한 권한이 없습니다'}), 403
        
        # 주행 기록 로드
        all_records = load_driving_records()
        
        # 해당 차량의 주행 기록만 필터링
        car_records = [
            record for record in all_records 
            if record.get('car_id') == car_id
        ]
        
        return jsonify({
            'success': True,
            'data': car_records
        })
        
    except Exception as e:
        return jsonify({'error': f'주행 기록 조회 실패: {str(e)}'}), 500

# 주행 기록 등록 API
@driving_records_bp.route('/api/driving/records', methods=['POST'])
@login_required
def create_driving_record():
    """새 주행 기록 등록"""
    try:
        user_id = session.get('user_id')
        data = request.get_json()
        
        # 필수 필드 검증
        required_fields = ['car_id', 'start_time', 'end_time', 'distance', 'start_location', 'end_location']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field}는 필수 입력 항목입니다'}), 400
        
        car_id = data['car_id']
        
        # 차량 소유권 확인
        car = Car.get_by_id(car_id)
        if not car or car.get('owner_id') != user_id:
            return jsonify({'error': '해당 차량에 대한 권한이 없습니다'}), 403
        
        # 주행 기록 로드
        records = load_driving_records()
        
        # 새 기록 ID 생성
        new_id = max([record.get('id', 0) for record in records], default=0) + 1
        
        # 새 주행 기록 생성
        new_record = {
            'id': new_id,
            'car_id': car_id,
            'start_time': data['start_time'],
            'end_time': data['end_time'],
            'distance': data['distance'],
            'start_location': data['start_location'],
            'end_location': data['end_location'],
            'avg_speed': data.get('avg_speed'),
            'max_speed': data.get('max_speed'),
            'fuel_consumption': data.get('fuel_consumption'),
            'created_at': datetime.now().isoformat()
        }
        
        records.append(new_record)
        save_driving_records(records)
        
        return jsonify({
            'success': True,
            'message': '주행 기록이 성공적으로 등록되었습니다',
            'record_id': new_id
        })
        
    except Exception as e:
        return jsonify({'error': f'주행 기록 등록 실패: {str(e)}'}), 500

# 주행 기록 삭제 API
@driving_records_bp.route('/api/driving/records/<int:record_id>', methods=['DELETE'])
@login_required
def delete_driving_record(record_id):
    """주행 기록 삭제"""
    try:
        user_id = session.get('user_id')
        
        # 주행 기록 로드
        records = load_driving_records()
        
        # 해당 기록 찾기
        record_to_delete = None
        for record in records:
            if record.get('id') == record_id:
                # 차량 소유권 확인
                car = Car.get_by_id(record.get('car_id'))
                if car and car.get('owner_id') == user_id:
                    record_to_delete = record
                    break
        
        if not record_to_delete:
            return jsonify({'error': '삭제할 주행 기록을 찾을 수 없거나 권한이 없습니다'}), 404
        
        # 기록 삭제
        records.remove(record_to_delete)
        save_driving_records(records)
        
        return jsonify({
            'success': True,
            'message': '주행 기록이 성공적으로 삭제되었습니다'
        })
        
    except Exception as e:
        return jsonify({'error': f'주행 기록 삭제 실패: {str(e)}'}), 500

# 주행 영상 다운로드 API
@driving_records_bp.route('/api/driving/records/<int:record_id>/video', methods=['GET'])
@login_required
def download_driving_video(record_id):
    """주행 영상 파일 다운로드"""
    try:

        
        user_id = session.get('user_id')
        
        # 사용자 소유 차량 목록 조회
        user_cars = Car.get_by_owner(user_id)
        user_car_ids = [car['id'] for car in user_cars]
        
        # 주행 기록 로드
        all_records = load_driving_records()
        trips = all_records.get('trips', [])
        
        # 해당 주행 기록 찾기
        record = None
        for trip in trips:
            if trip.get('id') == record_id:
                record = trip
                break
        
        if not record:
            return jsonify({'error': '주행 기록을 찾을 수 없습니다'}), 404
            
        # 소유권 확인
        if record.get('car_id') not in user_car_ids:
            return jsonify({'error': '해당 주행 기록에 접근할 권한이 없습니다'}), 403
            
        # 영상 파일 확인
        video_file = record.get('video_file')
        if not video_file:
            return jsonify({'error': '해당 기록에 영상 파일이 없습니다'}), 404
            
        # 파일 경로 확인
        video_path = os.path.join('static/assets/videos', video_file)
        if not os.path.exists(video_path):
            return jsonify({'error': '영상 파일을 찾을 수 없습니다'}), 404
            
        # 파일 다운로드 제공
        return send_from_directory(
            directory='static/assets/videos',
            path=video_file,
            as_attachment=True,
            download_name=f'주행기록_{record_id}_{video_file}'
        )
        
    except Exception as e:
        return jsonify({'error': f'영상 다운로드 실패: {str(e)}'}), 500
