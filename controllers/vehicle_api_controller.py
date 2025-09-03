# 차량 상태 API 컨트롤러
# car-api 서버에서 실시간 차량 상태를 가져오는 API 엔드포인트
import json
import os
import random
import requests
from datetime import datetime
from flask import Blueprint, jsonify, request

vehicle_api_bp = Blueprint('vehicle_api', __name__)

# car-api 서버 설정
CAR_API_BASE_URL = "http://127.0.0.1:9000"

# car-api 서버에서 차량 상태 가져오기
def get_vehicle_status_from_api(vehicle_id):
    """car-api 서버에서 실시간 차량 상태 조회"""
    try:
        response = requests.get(f"{CAR_API_BASE_URL}/api/vehicle/{vehicle_id}/status")
        if response.status_code == 200:
            return response.json()
        else:
            print(f"car-api 서버 응답 오류: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"car-api 서버 연결 실패: {e}")
        return None

# car-api 서버로 차량 제어 명령 전송
def send_vehicle_control(vehicle_id, action):
    """car-api 서버로 차량 제어 명령 전송"""
    try:
        response = requests.post(f"{CAR_API_BASE_URL}/api/vehicle/{vehicle_id}/control", 
                               params={"action": action})
        if response.status_code == 200:
            return response.json()
        else:
            print(f"car-api 서버 제어 명령 오류: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"car-api 서버 연결 실패: {e}")
        return None

def convert_action_to_api_format(action):
    """BE 액션을 car-api 형식으로 변환"""
    action_map = {
        'start_engine': 'engine_on',
        'stop_engine': 'engine_off',
        'lock_door': 'door_lock',
        'unlock_door': 'door_unlock',
        'start_ac': 'ac_on',
        'stop_ac': 'ac_off',
        'start_heater': 'heater_on',
        'stop_heater': 'heater_off'
    }
    return action_map.get(action)

# GET /api/vehicle/{vehicle_id}/status
@vehicle_api_bp.route('/api/vehicle/<int:vehicle_id>/status', methods=['GET'])
def get_vehicle_status(vehicle_id):
    """
    특정 차량의 실시간 상태 정보를 car-api 서버에서 조회
    vehicle_id: 차량 ID
    반환값: 차량의 현재 상태 (엔진, 도어, 연료, 배터리, 에어컨, 타이어압력, 주행거리, 위치)
    """
    try:
        # car-api 서버에서 실시간 상태 조회
        status = get_vehicle_status_from_api(vehicle_id)
        
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
@vehicle_api_bp.route('/api/vehicle/<int:vehicle_id>/control', methods=['POST'])
def control_vehicle(vehicle_id):
    """
    차량 원격 제어 (시동, 도어, 에어컨 등) - car-api 서버로 명령 전송
    vehicle_id: 차량 ID
    요청 데이터: {"action": "start_engine|stop_engine|lock_door|unlock_door|start_ac|stop_ac", "params": {...}}
    반환값: 제어 결과 및 변경된 상태
    """
    try:
        request_data = request.get_json()
        action = request_data.get('action')
        params = request_data.get('params', {})
        
        # action을 car-api가 이해하는 형식으로 변환
        api_action = convert_action_to_api_format(action)
        
        if not api_action:
            return jsonify({
                'success': False,
                'message': '잘못된 제어 명령입니다.'
            }), 400
        
        # car-api 서버로 제어 명령 전송
        result = send_vehicle_control(vehicle_id, api_action)
        
        if not result:
            return jsonify({
                'success': False,
                'message': '차량 제어 명령 전송에 실패했습니다.'
            }), 500
        
        return jsonify({
            'success': True,
            'message': '차량 제어가 완료되었습니다.',
            'data': result.get('data', {})
        })
            
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
    
    # 타임스탬프 업데이트
    current_time = datetime.now().isoformat()
    if 'tire_pressure' in status:
        status['tire_pressure']['last_checked'] = current_time
    if 'odometer' in status:
        status['odometer']['last_updated'] = current_time
    
    return status

# 차량 히스토리 조회 API  
@vehicle_api_bp.route('/api/vehicle/<int:vehicle_id>/history', methods=['GET'])
def get_vehicle_history(vehicle_id):
    """
    특정 차량의 제어 이력 조회 - BE 데이터베이스에서 조회
    vehicle_id: 차량 ID
    반환값: 차량 제어 이력 목록
    """
    try:
        from ..models.vehicle import VehicleModel
        vehicle_model = VehicleModel()
        
        history = vehicle_model.get_car_history(vehicle_id)
        if history is None:
            return jsonify({
                'success': False,
                'message': '차량을 찾을 수 없습니다.'
            }), 404
            
        return jsonify({
            'success': True,
            'data': history
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'차량 이력 조회 중 오류 발생: {str(e)}'
        }), 500
