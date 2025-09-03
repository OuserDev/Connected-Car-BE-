from flask import Blueprint, jsonify, request, session
from models.vehicle import VehicleModel
from models.user import UserModel
import json
import os

vehicle_bp = Blueprint('vehicle', __name__)
vehicle_model = VehicleModel()
user_model = UserModel()

@vehicle_bp.route('/api/cars/register', methods=['POST'])
def register_car():
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'JSON data required'}), 400
    
    # 차량 ID 또는 VIN으로 기존 차량 매칭
    car_id = data.get('car_id')
    vin = data.get('vin')
    license_plate = data.get('license_plate', '')
    
    if not car_id and not vin and not license_plate:
        return jsonify({'error': 'Car ID, VIN, or license plate is required'}), 400
    
    user_id = session['user_id']
    
    # 차량 찾기
    car = None
    if car_id:
        car = vehicle_model.get_car_by_id(car_id)
    elif vin:
        car = vehicle_model.get_car_by_vin(vin)
    elif license_plate:
        car = vehicle_model.get_car_by_license(license_plate)
    
    if not car:
        return jsonify({'error': 'Car not found'}), 404
    
    # 이미 등록된 차량인지 확인
    if car.get('owner_id') is not None:
        return jsonify({'error': 'Car is already registered to another user'}), 409
    
    # 차량을 사용자에게 할당
    updated_car = vehicle_model.assign_car_to_user(car['id'], user_id)
    if not updated_car:
        return jsonify({'error': 'Failed to register car'}), 500
    
    # 사용자 정보에도 차량 추가
    user_model.add_car_to_user(user_id, car['id'])
    
    return jsonify({
        'message': 'Car registered successfully',
        'car': updated_car
    })

@vehicle_bp.route('/api/cars', methods=['GET'])
def get_my_cars():
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    user_id = session['user_id']
    cars = vehicle_model.get_cars_by_owner(user_id)
    return jsonify({'cars': cars})

@vehicle_bp.route('/api/cars/available', methods=['GET'])
def get_available_cars():
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    cars = vehicle_model.get_unregistered_cars()
    return jsonify({'cars': cars})


@vehicle_bp.route('/api/car/<int:car_id>/status')
def get_car_status(car_id):
    """
    차량 상태 조회 - 등록 정보 + 실시간 상태 조합
    car_id: 차량 ID
    반환값: 차량 등록 정보와 실시간 상태를 결합한 데이터
    """
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401

    user_id = session['user_id']
    
    # 사용자는 본인 소유 차량만 조회 가능
    if not vehicle_model.is_owner(car_id, user_id):
        return jsonify({'error': 'Access denied - not your car'}), 403

    # 차량 등록 정보 조회
    car_info = vehicle_model.get_car_by_id(car_id)
    if not car_info:
        return jsonify({'error': 'Car not found'}), 404
    
    # 실시간 차량 상태 조회
    vehicle_status = get_vehicle_real_time_status(car_id)
    
    # 등록 정보와 상태 정보 결합
    combined_data = {**car_info, **vehicle_status}
    
    return jsonify(combined_data)

def get_vehicle_real_time_status(vehicle_id):
    """
    차량의 실시간 상태 정보를 vehicle_status.json에서 조회
    vehicle_id: 차량 ID
    반환값: 실시간 차량 상태 딕셔너리
    """
    try:
        # vehicle_status.json 파일 경로
        status_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'vehicle_status.json')
        
        with open(status_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        vehicle_status = data.get('vehicle_status', {})
        status = vehicle_status.get(str(vehicle_id), {})
        
        # 기본 상태값 설정 (데이터가 없는 경우)
        if not status:
            status = {
                "engine_state": "off",
                "door_state": "locked", 
                "fuel": 0,
                "battery": 12.0,
                "voltage": "12V",
                "climate": {
                    "ac_state": "off",
                    "heater_state": "off",
                    "target_temp": 22,
                    "current_temp": 20,
                    "fan_speed": 0,
                    "auto_mode": False
                },
                "tire_pressure": {
                    "front_left": 2.3,
                    "front_right": 2.3,
                    "rear_left": 2.3,
                    "rear_right": 2.3,
                    "recommended": 2.3,
                    "unit": "bar",
                    "warning_threshold": 1.8,
                    "last_checked": "2024-01-01T00:00:00Z"
                },
                "odometer": {
                    "total_km": 0,
                    "trip_a_km": 0,
                    "trip_b_km": 0,
                    "last_updated": "2024-01-01T00:00:00Z"
                },
                "location": {
                    "lat": 37.5665,
                    "lng": 126.9780
                }
            }
        
        return status
        
    except Exception as e:
        print(f"차량 상태 조회 중 오류: {e}")
        # 오류 발생 시 기본값 반환
        return {
            "engine_state": "off",
            "door_state": "locked",
            "fuel": 0,
            "battery": 12.0,
            "voltage": "12V"
        }

@vehicle_bp.route('/api/car/<int:car_id>/command', methods=['POST'])
def execute_command(car_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    action = request.args.get('action')
    value = request.args.get('value')  # 온도, 팬속도 등의 값
    
    if not action:
        return jsonify({'error': 'Action parameter is required'}), 400
    
    user_id = session['user_id']
    
    # 소유권 검증 포함하여 명령 실행
    result = vehicle_model.execute_command(car_id, action, user_id, value)
    if result:
        response = {
            'message': f'{action} executed on car {car_id}',
            'car_id': car_id,
            'action': action,
            'status': 'success'
        }
        if value is not None:
            response['value'] = value
        return jsonify(response)
    
    # 차량이 존재하지 않거나 권한이 없는 경우
    car = vehicle_model.get_car_by_id(car_id)
    if not car:
        return jsonify({'error': 'Car not found'}), 404
    else:
        return jsonify({'error': 'Access denied - not your car'}), 403

@vehicle_bp.route('/api/car/<int:car_id>/history')
def get_car_history(car_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    user_id = session['user_id']
    
    # 사용자는 본인 소유 차량의 이력만 조회 가능
    if not vehicle_model.is_owner(car_id, user_id):
        return jsonify({'error': 'Access denied - not your car'}), 403
    
    history = vehicle_model.get_car_history(car_id)
    if history is not None:
        return jsonify(history)
    return jsonify({'error': 'Car not found'}), 404

@vehicle_bp.route('/api/car/<int:car_id>/location')
def get_car_location(car_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    user_id = session['user_id']
    
    # 사용자는 본인 소유 차량의 위치만 조회 가능
    if not vehicle_model.is_owner(car_id, user_id):
        return jsonify({'error': 'Access denied - not your car'}), 403
    
    location_info = vehicle_model.get_and_update_location(car_id, user_id)
    if location_info:
        return jsonify(location_info)
    return jsonify({'error': 'Car not found'}), 404

@vehicle_bp.route('/api/car/<int:car_id>/horn', methods=['POST'])
def horn_and_locate(car_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    user_id = session['user_id']
    
    # 사용자는 본인 소유 차량만 제어 가능
    if not vehicle_model.is_owner(car_id, user_id):
        return jsonify({'error': 'Access denied - not your car'}), 403
    
    result = vehicle_model.horn_and_locate(car_id, user_id)
    if result:
        return jsonify(result)
    return jsonify({'error': 'Car not found'}), 404

@vehicle_bp.route('/api/car/<int:car_id>/tire-pressure')
def check_tire_pressure(car_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    user_id = session['user_id']
    
    # 사용자는 본인 소유 차량의 타이어 압력만 조회 가능
    if not vehicle_model.is_owner(car_id, user_id):
        return jsonify({'error': 'Access denied - not your car'}), 403
    
    pressure_info = vehicle_model.check_tire_pressure(car_id, user_id)
    if pressure_info:
        return jsonify(pressure_info)
    return jsonify({'error': 'Car not found or no tire pressure data'}), 404

@vehicle_bp.route('/api/car/<int:car_id>/tire-pressure/simulate', methods=['POST'])
def simulate_tire_pressure(car_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    user_id = session['user_id']
    
    # 사용자는 본인 소유 차량만 시뮬레이션 가능
    if not vehicle_model.is_owner(car_id, user_id):
        return jsonify({'error': 'Access denied - not your car'}), 403
    
    result = vehicle_model.simulate_tire_pressure_change(car_id, user_id)
    if result:
        return jsonify(result)
    return jsonify({'error': 'Car not found or no tire pressure data'}), 404

@vehicle_bp.route('/api/car/<int:car_id>/driving-statistics')
def get_driving_statistics(car_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    user_id = session['user_id']
    
    # 사용자는 본인 소유 차량의 주행 통계만 조회 가능
    if not vehicle_model.is_owner(car_id, user_id):
        return jsonify({'error': 'Access denied - not your car'}), 403
    
    stats = vehicle_model.get_driving_statistics(car_id, user_id)
    if stats:
        return jsonify(stats)
    return jsonify({'error': 'Car not found'}), 404

@vehicle_bp.route('/api/car/<int:car_id>/trip-history')
def get_trip_history(car_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    user_id = session['user_id']
    limit = request.args.get('limit', 10, type=int)
    
    # 사용자는 본인 소유 차량의 주행 이력만 조회 가능
    if not vehicle_model.is_owner(car_id, user_id):
        return jsonify({'error': 'Access denied - not your car'}), 403
    
    trips = vehicle_model.get_trip_history(car_id, user_id, limit)
    if trips:
        return jsonify(trips)
    return jsonify({'error': 'Car not found'}), 404

@vehicle_bp.route('/api/car/<int:car_id>/simulate-trip', methods=['POST'])
def simulate_trip(car_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    user_id = session['user_id']
    
    # 사용자는 본인 소유 차량만 시뮬레이션 가능
    if not vehicle_model.is_owner(car_id, user_id):
        return jsonify({'error': 'Access denied - not your car'}), 403
    
    result = vehicle_model.simulate_new_trip(car_id, user_id)
    if result:
        return jsonify(result)
    return jsonify({'error': 'Car not found'}), 404

# 관리자 전용 차량 할당 기능 제거됨 - 별도 관리자 VM에서 구현 예정