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

# 차량 등록 API (MySQL 기반) - 기존 방식
@vehicle_bp.route('/api/cars/register-old', methods=['POST'])
@login_required
def register_car_old():
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
        
        # 디버깅: 전체 차량 수와 미등록 차량 수도 함께 반환
        all_cars_query = "SELECT COUNT(*) as total FROM cars"
        unowned_cars_query = "SELECT COUNT(*) as unowned FROM cars WHERE owner_id IS NULL"
        user_cars_query = "SELECT COUNT(*) as user_cars FROM cars WHERE owner_id = %s"
        specific_cars_query = "SELECT id, owner_id, license_plate FROM cars WHERE owner_id = %s LIMIT 3"
        
        total_cars = DatabaseHelper.execute_query(all_cars_query)[0]['total']
        unowned_cars = DatabaseHelper.execute_query(unowned_cars_query)[0]['unowned']
        user_car_count = DatabaseHelper.execute_query(user_cars_query, (user_id,))[0]['user_cars']
        specific_cars = DatabaseHelper.execute_query(specific_cars_query, (user_id,))
        
        return jsonify({
            'success': True,
            'data': cars,
            'count': len(cars),
            'debug': {
                'user_id': user_id,
                'total_cars_in_db': total_cars,
                'unowned_cars': unowned_cars,
                'user_car_count_from_db': user_car_count,
                'specific_user_cars': specific_cars,
                'cars_from_model': len(cars) if cars else 0
            }
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

# 차량 기본 정보 조회 API (스펙 제외)
@vehicle_bp.route('/api/car/<int:car_id>/info', methods=['GET'])
@login_required
def get_car_info(car_id):
    """차량 기본 정보 조회 (등록 정보만, 스펙 제외)"""
    try:
        user_id = session.get('user_id')
        
        # 소유권 확인
        if not Car.verify_ownership(user_id, car_id):
            return jsonify({'error': '해당 차량에 대한 권한이 없습니다'}), 403
        
        # 차량 정보 조회
        car = Car.get_by_id(car_id)
        if not car:
            return jsonify({'error': '차량을 찾을 수 없습니다'}), 404
        
        # 기본 등록 정보만 반환 (실제 테이블 구조에 맞게)
        basic_info = {
            'id': car.get('id'),
            'license_plate': car.get('license_plate'),
            'vin': car.get('vin'),
            'model_id': car.get('model_id'),
            'model_name': car.get('model_name'),
            'category': car.get('category'),
            'created_at': car.get('created_at').isoformat() if car.get('created_at') else None
        }
        
        return jsonify({
            'success': True,
            'data': basic_info
        })
        
    except Exception as e:
        return jsonify({'error': f'차량 정보 조회 실패: {str(e)}'}), 500

# 차량 스펙 정보 조회 API
@vehicle_bp.route('/api/car/<int:car_id>/specs', methods=['GET'])
@login_required
def get_car_specs(car_id):
    """차량의 스펙 정보 조회"""
    try:
        user_id = session.get('user_id')
        
        # 소유권 확인
        if not Car.verify_ownership(user_id, car_id):
            return jsonify({'error': '해당 차량에 대한 권한이 없습니다'}), 403
        
        # 차량 정보 조회 (스펙 포함)
        car = Car.get_by_id(car_id)
        if not car:
            return jsonify({'error': '차량을 찾을 수 없습니다'}), 404
        
        # 실제 테이블 구조에 맞는 스펙 정보만 추출
        specs_info = {
            'model_id': car.get('model_id'),
            'model_name': car.get('model_name'),
            'category': car.get('category'),
            'segment': car.get('segment'),
            'engine_type': car.get('engine_type'),
            'displacement': car.get('displacement'),
            'power': car.get('max_power'),  # power as max_power
            'torque': car.get('max_torque'),  # torque as max_torque
            'fuel_efficiency': car.get('fuel_efficiency'),
            'transmission': car.get('transmission'),
            'drive_type': car.get('drivetrain'),  # drive_type as drivetrain
            'voltage': car.get('voltage'),
            'fuel_capacity': car.get('fuel_capacity'),
            # 차량 크기 정보
            'length': car.get('length'),
            'width': car.get('width'),
            'height': car.get('height'),
            'wheelbase': car.get('wheelbase'),
            'weight': car.get('curb_weight'),  # weight as curb_weight
            # 성능 정보
            'max_speed': car.get('max_speed'),
            'acceleration': car.get('acceleration')
        }
        
        return jsonify({
            'success': True,
            'data': specs_info
        })
        
    except Exception as e:
        return jsonify({'error': f'차량 스펙 조회 실패: {str(e)}'}), 500

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

# 내 차량들의 제어 이력 전체 조회 API (사용자별)
@vehicle_bp.route('/api/my/history', methods=['GET'])
@login_required
def get_my_history():
    """현재 로그인한 사용자의 모든 차량 제어 이력 조회"""
    try:
        user_id = session.get('user_id')
        
        # 이력 조회 (최근 100개)
        limit = request.args.get('limit', 100, type=int)
        history = CarHistory.get_by_user(user_id, limit)
        
        return jsonify({
            'success': True,
            'data': history,
            'count': len(history),
            'user_id': user_id
        })
        
    except Exception as e:
        return jsonify({'error': f'내 이력 조회 실패: {str(e)}'}), 500

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
        recent_history = CarHistory.get_by_car(car_id, 10)
        
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

# 테스트용: 미등록 차량을 현재 사용자에게 할당
@vehicle_bp.route('/api/cars/assign-test-vehicle', methods=['POST'])
@login_required
def assign_test_vehicle():
    """테스트용: 첫 번째 미등록 차량을 현재 사용자에게 할당"""
    try:
        user_id = session.get('user_id')
        
        # 미등록 차량 중 첫 번째 조회
        unowned_query = "SELECT id FROM cars WHERE owner_id IS NULL LIMIT 1"
        unowned_cars = DatabaseHelper.execute_query(unowned_query)
        
        if not unowned_cars:
            return jsonify({'error': '할당 가능한 미등록 차량이 없습니다'}), 404
        
        car_id = unowned_cars[0]['id']
        
        # 차량을 현재 사용자에게 할당
        assign_query = "UPDATE cars SET owner_id = %s WHERE id = %s"
        DatabaseHelper.execute_update(assign_query, (user_id, car_id))
        
        # 할당된 차량 정보 조회
        assigned_car = Car.get_by_id(car_id)
        
        return jsonify({
            'success': True,
            'message': f'차량 ID {car_id}가 사용자 ID {user_id}에게 할당되었습니다',
            'data': assigned_car
        })
        
    except Exception as e:
        return jsonify({'error': f'테스트 차량 할당 실패: {str(e)}'}), 500


# 차량 정보 검증 API (라이선스 플레이트 + VIN 코드로 조회)
@vehicle_bp.route('/api/cars/verify', methods=['POST'])
@login_required
def verify_car_info():
    """라이선스 플레이트와 VIN 코드로 차량 정보 확인"""
    print("🚗 [DEBUG] /api/cars/verify 엔드포인트 호출됨")
    try:
        data = request.get_json()
        print(f"🚗 [DEBUG] 받은 데이터: {data}")
        
        if not data:
            return jsonify({'error': 'JSON 데이터가 필요합니다'}), 400
        
        license_plate = data.get('licensePlate', '').strip()
        vin_code = data.get('vinCode', '').strip()
        
        if not license_plate or not vin_code:
            return jsonify({'error': '라이선스 플레이트와 VIN 코드를 모두 입력해주세요'}), 400
        
        # 차량 조회 (owner_id가 NULL인 차량만)
        query = """
        SELECT c.*, vs.model, vs.category, vs.engine_type, vs.segment, vs.fuel_capacity
        FROM cars c
        LEFT JOIN vehicle_specs vs ON c.model_id = vs.id
        WHERE c.license_plate = %s AND c.vin = %s AND c.owner_id IS NULL
        """
        
        result = DatabaseHelper.execute_query(query, (license_plate, vin_code))
        
        if not result:
            return jsonify({
                'success': False,
                'error': '입력한 정보와 일치하는 차량을 찾을 수 없거나 이미 등록된 차량입니다'
            }), 404
        
        car_info = result[0]
        
        return jsonify({
            'success': True,
            'car': {
                'id': car_info['id'],
                'license_plate': car_info['license_plate'],
                'vin': car_info['vin'],
                'model_name': car_info['model'],  # vehicle_specs.model
                'manufacturer': 'Hyundai',  # 하드코딩 (테이블에 없음)
                'year': '2024',  # 하드코딩 (테이블에 없음) 
                'fuel_type': car_info['engine_type']  # vehicle_specs.engine_type
            },
            'message': '차량 정보를 찾았습니다'
        })
        
    except Exception as e:
        return jsonify({'error': f'차량 정보 확인 실패: {str(e)}'}), 500


# 차량 등록 완료 API (owner_id 업데이트)
@vehicle_bp.route('/api/cars/register', methods=['POST'])
@login_required
def complete_car_registration():
    """검증된 차량을 현재 사용자에게 등록"""
    print("🚗 [DEBUG] /api/cars/register 엔드포인트 호출됨")
    try:
        user_id = session.get('user_id')
        data = request.get_json()
        print(f"🚗 [DEBUG] 받은 데이터: {data}")
        print(f"🚗 [DEBUG] 사용자 ID: {user_id}")
        
        if not data:
            return jsonify({'error': 'JSON 데이터가 필요합니다'}), 400
        
        car_id = data.get('carId')
        license_plate = data.get('licensePlate', '').strip()
        vin_code = data.get('vinCode', '').strip()
        
        print(f"🚗 [DEBUG] car_id: {car_id}, license_plate: {license_plate}, vin_code: {vin_code}")
        
        if not all([car_id, license_plate, vin_code]):
            return jsonify({'error': '차량 ID, 라이선스 플레이트, VIN 코드가 모두 필요합니다'}), 400
        
        # 차량 존재 및 소유권 확인
        verify_query = """
        SELECT id FROM cars 
        WHERE id = %s AND license_plate = %s AND vin = %s AND owner_id IS NULL
        """
        
        result = DatabaseHelper.execute_query(verify_query, (car_id, license_plate, vin_code))
        
        if not result:
            return jsonify({
                'success': False,
                'error': '차량을 찾을 수 없거나 이미 등록된 차량입니다'
            }), 404
        
        # 사용자가 이미 같은 차량을 소유하고 있는지 확인 (중복 등록 방지)
        duplicate_car_query = "SELECT id FROM cars WHERE owner_id = %s AND id = %s"
        duplicate_car = DatabaseHelper.execute_query(duplicate_car_query, (user_id, car_id))
        
        if duplicate_car:
            return jsonify({
                'success': False,
                'error': '이미 등록된 차량입니다'
            }), 409
        
        # 차량 소유권 업데이트
        update_query = "UPDATE cars SET owner_id = %s WHERE id = %s"
        DatabaseHelper.execute_update(update_query, (user_id, car_id))
        
        # 차량 등록 이력 추가
        CarHistory.add(
            car_id=car_id,
            action='register',
            user_id=user_id,
            parameters={'license_plate': license_plate, 'vin_code': vin_code},
            result='success'
        )
        
        # 등록된 차량 정보 조회
        car_info_query = """
        SELECT c.*, vs.model, vs.category, vs.engine_type, vs.segment 
        FROM cars c
        LEFT JOIN vehicle_specs vs ON c.model_id = vs.id
        WHERE c.id = %s
        """
        
        car_info = DatabaseHelper.execute_query(car_info_query, (car_id,))
        
        if car_info:
            car_data = car_info[0]
            return jsonify({
                'success': True,
                'car': {
                    'id': car_data['id'],
                    'license_plate': car_data['license_plate'],
                    'vin': car_data['vin'],
                    'model_name': car_data['model'],  # vehicle_specs.model
                    'manufacturer': 'Hyundai',  # 하드코딩
                    'year': '2024',  # 하드코딩
                    'fuel_type': car_data['engine_type']  # vehicle_specs.engine_type
                },
                'message': '차량이 성공적으로 등록되었습니다'
            })
        else:
            return jsonify({
                'success': True,
                'message': '차량이 등록되었지만 정보 조회에 실패했습니다'
            })
        
    except Exception as e:
        print(f"🚗 [ERROR] 차량 등록 실패: {str(e)}")
        import traceback
        print(f"🚗 [ERROR] 스택 트레이스: {traceback.format_exc()}")
        return jsonify({'error': f'차량 등록 실패: {str(e)}'}), 500
