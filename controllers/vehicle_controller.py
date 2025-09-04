# MySQL 기반 차량 컨트롤러 (로컬 데이터 관리)

from flask import Blueprint, jsonify, request, session
from models.car import Car
from models.car_history import CarHistory
from models.vehicle_spec import VehicleSpec
from models.base import DatabaseHelper
from utils.auth import login_required
import json
import os
from datetime import datetime

vehicle_bp = Blueprint('vehicle', __name__)

# 차량 등록 API (MySQL 기반)
@vehicle_bp.route('/api/cars/register', methods=['POST'])
@login_required
def register_car():
    """새 차량 등록 (MySQL 기반)"""
    try:
        user_id = session.get('user_id')
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'JSON 데이터가 필요합니다'}), 400
        
        # 필수 필드 검증
        required_fields = ['model_id', 'license_plate', 'vin']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field}는 필수 입력 항목입니다'}), 400
        
        # 중복 검사 (VIN, 번호판)
        existing_car_query = "SELECT id FROM cars WHERE vin = %s OR license_plate = %s"
        existing = DatabaseHelper.execute_query(existing_car_query, (data['vin'], data['license_plate']))
        
        if existing:
            return jsonify({'error': '이미 등록된 차량입니다 (VIN 또는 번호판 중복)'}), 409
        
        # 차량 등록
        car_id = Car.register(
            owner_id=user_id,
            model_id=data['model_id'],
            license_plate=data['license_plate'],
            vin=data['vin']
        )
        
        # 등록 이력 추가
        CarHistory.add(
            car_id=car_id,
            action='car_registered',
            user_id=user_id
        )
        
        # 등록된 차량 정보 조회
        registered_car = Car.get_by_id(car_id)
        
        return jsonify({
            'success': True,
            'message': '차량이 성공적으로 등록되었습니다',
            'data': registered_car
        })
        
    except Exception as e:
        return jsonify({'error': f'차량 등록 실패: {str(e)}'}), 500

# 내 차량 목록 조회 API (MySQL 기반)
@vehicle_bp.route('/api/cars', methods=['GET'])
@login_required
def get_my_cars():
    """로그인한 사용자의 차량 목록 조회 (MySQL 기반)"""
    try:
        user_id = session.get('user_id')
        
        # 사용자 소유 차량 목록 조회
        cars = Car.get_by_owner(user_id)
        
        return jsonify({
            'success': True,
            'data': cars,
            'count': len(cars)
        })
        
    except Exception as e:
        return jsonify({'error': f'차량 목록 조회 실패: {str(e)}'}), 500

# 차량 상세 정보 조회 API (MySQL 기반)
@vehicle_bp.route('/api/car/<int:car_id>', methods=['GET'])
@login_required
def get_car_details(car_id):
    """차량 상세 정보 조회 (MySQL 기반)"""
    try:
        user_id = session.get('user_id')
        
        # 소유권 확인
        if not Car.verify_ownership(user_id, car_id):
            return jsonify({'error': '해당 차량에 대한 권한이 없습니다'}), 403
        
        # 차량 정보 조회
        car = Car.get_by_id(car_id)
        if not car:
            return jsonify({'error': '차량을 찾을 수 없습니다'}), 404
        
        return jsonify({
            'success': True,
            'data': car
        })
        
    except Exception as e:
        return jsonify({'error': f'차량 정보 조회 실패: {str(e)}'}), 500

# 차량 제어 이력 조회 API (MySQL 기반)
@vehicle_bp.route('/api/car/<int:car_id>/history', methods=['GET'])
@login_required
def get_car_history(car_id):
    """차량 제어 이력 조회 (MySQL 기반)"""
    try:
        user_id = session.get('user_id')
        
        # 소유권 확인
        if not Car.verify_ownership(user_id, car_id):
            return jsonify({'error': '해당 차량에 대한 권한이 없습니다'}), 403
        
        # 이력 조회 (최근 50개)
        limit = request.args.get('limit', 50, type=int)
        history = CarHistory.get_by_car(car_id, limit)
        
        return jsonify({
            'success': True,
            'data': history,
            'count': len(history)
        })
        
    except Exception as e:
        return jsonify({'error': f'차량 이력 조회 실패: {str(e)}'}), 500

# 차량 위치 정보 관리 API (MySQL 기반)
@vehicle_bp.route('/api/car/<int:car_id>/location', methods=['GET', 'POST'])
@login_required
def manage_car_location(car_id):
    """차량 위치 정보 조회/업데이트 (MySQL 기반)"""
    try:
        user_id = session.get('user_id')
        
        # 소유권 확인
        if not Car.verify_ownership(user_id, car_id):
            return jsonify({'error': '해당 차량에 대한 권한이 없습니다'}), 403
        
        if request.method == 'GET':
            # 위치 정보 조회 - car-api에서 실시간 위치 가져와야 함
            # 현재는 기본 위치 반환
            return jsonify({
                'success': True,
                'data': {
                    'car_id': car_id,
                    'location': {
                        'lat': 37.5665,
                        'lng': 126.978,
                        'address': '서울특별시 중구 명동'
                    },
                    'last_updated': datetime.now().isoformat()
                }
            })
        
        elif request.method == 'POST':
            # 위치 업데이트 명령 (실제로는 car-api로 전달)
            data = request.get_json()
            
            # 이력 추가
            CarHistory.add(
                car_id=car_id,
                action='location_update_requested',
                user_id=user_id,
                parameters=data
            )
            
            return jsonify({
                'success': True,
                'message': '위치 업데이트 요청이 전송되었습니다'
            })
            
    except Exception as e:
        return jsonify({'error': f'위치 정보 처리 실패: {str(e)}'}), 500

# 차량 진단 정보 API (MySQL 기반)
@vehicle_bp.route('/api/car/<int:car_id>/diagnostics', methods=['GET'])
@login_required
def get_car_diagnostics(car_id):
    """차량 진단 정보 조회 (MySQL 기반)"""
    try:
        user_id = session.get('user_id')
        
        # 소유권 확인
        if not Car.verify_ownership(user_id, car_id):
            return jsonify({'error': '해당 차량에 대한 권한이 없습니다'}), 403
        
        # 차량 기본 정보 조회
        car = Car.get_by_id(car_id)
        if not car:
            return jsonify({'error': '차량을 찾을 수 없습니다'}), 404
        
        # 최근 제어 이력 조회 (진단용)
        recent_history = CarHistoryDatabase.get_car_history(car_id, 10)
        
        # 진단 정보 구성
        diagnostics = {
            'car_id': car_id,
            'license_plate': car['license_plate'],
            'model': car.get('model', 'Unknown'),
            'voltage': car.get('voltage', '12V'),
            'last_activity': recent_history[0]['timestamp'].isoformat() if recent_history else None,
            'total_commands': len(recent_history),
            'recent_commands': [
                {
                    'action': h['action'],
                    'timestamp': h['timestamp'].isoformat(),
                    'result': h.get('result', 'success')
                } for h in recent_history[:5]
            ]
        }
        
        return jsonify({
            'success': True,
            'data': diagnostics
        })
        
    except Exception as e:
        return jsonify({'error': f'진단 정보 조회 실패: {str(e)}'}), 500

# 차량 스펙 정보 조회 API (MySQL 기반)
@vehicle_bp.route('/api/vehicle-specs', methods=['GET'])
@login_required
def get_vehicle_specs():
    """모든 차량 스펙 정보 조회 (MySQL 기반)"""
    try:
        # 카테고리 필터
        category = request.args.get('category')
        
        if category:
            specs = VehicleSpec.get_by_category(category)
        else:
            specs = VehicleSpec.get_all()
        
        return jsonify({
            'success': True,
            'data': specs,
            'count': len(specs)
        })
        
    except Exception as e:
        return jsonify({'error': f'차량 스펙 조회 실패: {str(e)}'}), 500

# 특정 차량 스펙 조회 API (MySQL 기반)
@vehicle_bp.route('/api/vehicle-specs/<int:spec_id>', methods=['GET'])
@login_required
def get_vehicle_spec_by_id(spec_id):
    """특정 차량 스펙 정보 조회 (MySQL 기반)"""
    try:
        spec = VehicleSpec.get_by_id(spec_id)
        
        if not spec:
            return jsonify({'error': '차량 스펙을 찾을 수 없습니다'}), 404
        
        return jsonify({
            'success': True,
            'data': spec
        })
        
    except Exception as e:
        return jsonify({'error': f'차량 스펙 조회 실패: {str(e)}'}), 500

# 미등록 차량 목록 조회 API (관리자용 - 주석 처리)
# @vehicle_bp.route('/api/cars/unregistered', methods=['GET'])
# @login_required
# def get_unregistered_cars():
#     """미등록 차량 목록 조회 (관리자 전용)"""
#     # 관리자 기능은 별도 관리자 VM에서 구현
#     pass

# 차량 소유권 이전 API (관리자용 - 주석 처리)
# @vehicle_bp.route('/api/car/<int:car_id>/transfer', methods=['POST'])
# @login_required
# def transfer_car_ownership(car_id):
#     """차량 소유권 이전 (관리자 전용)"""
#     # 관리자 기능은 별도 관리자 VM에서 구현
#     pass

# 차량 삭제 API (MySQL 기반)
@vehicle_bp.route('/api/car/<int:car_id>', methods=['DELETE'])
@login_required
def delete_car(car_id):
    """차량 등록 해제 (MySQL 기반)"""
    try:
        user_id = session.get('user_id')
        
        # 소유권 확인
        if not Car.verify_ownership(user_id, car_id):
            return jsonify({'error': '해당 차량에 대한 권한이 없습니다'}), 403
        
        # 차량 정보 조회
        car = Car.get_by_id(car_id)
        if not car:
            return jsonify({'error': '차량을 찾을 수 없습니다'}), 404
        
        # 소유권 해제 (owner_id를 NULL로 설정)
        query = "UPDATE cars SET owner_id = NULL WHERE id = %s"
        DatabaseHelper.execute_update(query, (car_id,))
        
        # 해제 이력 추가
        CarHistory.add(
            car_id=car_id,
            action='car_unregistered',
            user_id=user_id
        )
        
        return jsonify({
            'success': True,
            'message': '차량 등록이 해제되었습니다'
        })
        
    except Exception as e:
        return jsonify({'error': f'차량 등록 해제 실패: {str(e)}'}), 500
