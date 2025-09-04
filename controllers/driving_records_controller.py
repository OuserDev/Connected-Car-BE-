# 주행 기록 관리 API 컨트롤러
from flask import Blueprint, jsonify, request, session
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
        if os.path.exists(DRIVING_RECORDS_FILE):
            with open(DRIVING_RECORDS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return []

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
        
        # 사용자 소유 차량 목록 조회
        user_cars = Car.get_by_owner(user_id)
        user_car_ids = [car['id'] for car in user_cars]
        
        # 주행 기록 로드
        all_records = load_driving_records()
        
        # 사용자 차량의 주행 기록만 필터링
        user_records = [
            record for record in all_records 
            if record.get('car_id') in user_car_ids
        ]
        
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
