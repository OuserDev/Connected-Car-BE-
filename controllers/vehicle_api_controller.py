# 차량 상태 API 컨트롤러
# 실시간 차량 상태 정보를 제공하는 API 엔드포인트
import json
import os
import random
from datetime import datetime
from flask import Blueprint, jsonify, request

vehicle_api_bp = Blueprint('vehicle_api', __name__)

# 차량 상태 데이터 파일 경로
VEHICLE_STATUS_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'vehicle_status.json')

# 차량 상태 데이터 로드
def load_vehicle_status():
    try:
        with open(VEHICLE_STATUS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"차량 상태 데이터 로드 실패: {e}")
        return {"vehicle_status": {}}

# 차량 상태 데이터 저장
def save_vehicle_status(data):
    try:
        with open(VEHICLE_STATUS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"차량 상태 데이터 저장 실패: {e}")
        return False

# 실시간 차량 상태 조회 API
# GET /api/vehicle/{vehicle_id}/status
@vehicle_api_bp.route('/api/vehicle/<int:vehicle_id>/status', methods=['GET'])
def get_vehicle_status(vehicle_id):
    """
    특정 차량의 실시간 상태 정보를 반환
    vehicle_id: 차량 ID
    반환값: 차량의 현재 상태 (엔진, 도어, 연료, 배터리, 에어컨, 타이어압력, 주행거리, 위치)
    """
    try:
        data = load_vehicle_status()
        vehicle_status = data.get('vehicle_status', {})
        
        # 해당 차량 ID의 상태 정보 조회
        status = vehicle_status.get(str(vehicle_id))
        
        if not status:
            return jsonify({
                'success': False,
                'message': '차량 상태 정보를 찾을 수 없습니다.'
            }), 404
        
        # 실시간 데이터 시뮬레이션 (일부 값들을 약간 변경)
        simulated_status = simulate_real_time_data(status.copy())
        
        return jsonify({
            'success': True,
            'data': simulated_status
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'차량 상태 조회 중 오류 발생: {str(e)}'
        }), 500

# 차량 원격 제어 API
# POST /api/vehicle/{vehicle_id}/control
@vehicle_api_bp.route('/api/vehicle/<int:vehicle_id>/control', methods=['POST'])
def control_vehicle(vehicle_id):
    """
    차량 원격 제어 (시동, 도어, 에어컨 등)
    vehicle_id: 차량 ID
    요청 데이터: {"action": "start_engine|stop_engine|lock_door|unlock_door|start_ac|stop_ac", "params": {...}}
    반환값: 제어 결과 및 변경된 상태
    """
    try:
        request_data = request.get_json()
        action = request_data.get('action')
        params = request_data.get('params', {})
        
        data = load_vehicle_status()
        vehicle_status = data.get('vehicle_status', {})
        
        # 해당 차량 ID의 상태 정보 조회
        status = vehicle_status.get(str(vehicle_id))
        
        if not status:
            return jsonify({
                'success': False,
                'message': '차량을 찾을 수 없습니다.'
            }), 404
        
        # 제어 명령 처리
        updated_status = process_vehicle_control(status.copy(), action, params)
        
        if updated_status is None:
            return jsonify({
                'success': False,
                'message': '잘못된 제어 명령입니다.'
            }), 400
        
        # 변경된 상태 저장
        vehicle_status[str(vehicle_id)] = updated_status
        data['vehicle_status'] = vehicle_status
        
        if save_vehicle_status(data):
            return jsonify({
                'success': True,
                'message': '차량 제어가 완료되었습니다.',
                'data': updated_status
            })
        else:
            return jsonify({
                'success': False,
                'message': '차량 상태 저장에 실패했습니다.'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'차량 제어 중 오류 발생: {str(e)}'
        }), 500

# 실시간 데이터 시뮬레이션 함수
def simulate_real_time_data(status):
    """
    실제 차량처럼 일부 데이터를 실시간으로 변화시킴
    배터리 전압, 현재 온도, GPS 위치 등을 약간씩 변경
    """
    # 배터리 전압 ±0.1V 변화
    if 'battery' in status:
        current_battery = status['battery']
        status['battery'] = round(current_battery + random.uniform(-0.1, 0.1), 1)
    
    # 실내 온도 ±1도 변화
    if 'climate' in status and 'current_temp' in status['climate']:
        current_temp = status['climate']['current_temp']
        status['climate']['current_temp'] = current_temp + random.randint(-1, 1)
    
    # GPS 위치 약간 변화 (±0.001도)
    if 'location' in status:
        status['location']['lat'] += random.uniform(-0.001, 0.001)
        status['location']['lng'] += random.uniform(-0.001, 0.001)
        status['location']['lat'] = round(status['location']['lat'], 6)
        status['location']['lng'] = round(status['location']['lng'], 6)
    
    return status

# 차량 제어 명령 처리 함수
def process_vehicle_control(status, action, params):
    """
    차량 제어 명령을 처리하여 상태를 업데이트
    action: 제어 명령
    params: 제어 매개변수
    반환값: 업데이트된 상태 또는 None (잘못된 명령)
    """
    current_time = datetime.now().isoformat() + "Z"
    
    if action == "start_engine":
        status['engine_state'] = "on"
        
    elif action == "stop_engine":
        status['engine_state'] = "off"
        
    elif action == "lock_door":
        status['door_state'] = "locked"
        
    elif action == "unlock_door":
        status['door_state'] = "unlocked"
        
    elif action == "start_ac":
        status['climate']['ac_state'] = "on"
        target_temp = params.get('target_temp', 22)
        status['climate']['target_temp'] = target_temp
        status['climate']['fan_speed'] = params.get('fan_speed', 3)
        
    elif action == "stop_ac":
        status['climate']['ac_state'] = "off"
        status['climate']['fan_speed'] = 0
        
    elif action == "start_heater":
        status['climate']['heater_state'] = "on"
        target_temp = params.get('target_temp', 24)
        status['climate']['target_temp'] = target_temp
        status['climate']['fan_speed'] = params.get('fan_speed', 2)
        
    elif action == "stop_heater":
        status['climate']['heater_state'] = "off"
        status['climate']['fan_speed'] = 0
        
    else:
        # 잘못된 명령
        return None
    
    return status

# 모든 차량 상태 조회 (관제용)
# GET /api/vehicles/status
@vehicle_api_bp.route('/api/vehicles/status', methods=['GET'])
def get_all_vehicles_status():
    """
    모든 차량의 실시간 상태 정보를 반환 (관제 시스템용)
    반환값: 모든 차량의 현재 상태 목록
    """
    try:
        data = load_vehicle_status()
        vehicle_status = data.get('vehicle_status', {})
        
        # 모든 차량에 실시간 데이터 시뮬레이션 적용
        simulated_status = {}
        for vehicle_id, status in vehicle_status.items():
            simulated_status[vehicle_id] = simulate_real_time_data(status.copy())
        
        return jsonify({
            'success': True,
            'data': simulated_status
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'전체 차량 상태 조회 중 오류 발생: {str(e)}'
        }), 500
