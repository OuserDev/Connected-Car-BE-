# MySQL 기반 외부 API 통신 컨트롤러 (car-api 서버 연동)

from flask import Blueprint, jsonify, request, session
from models.car import Car
from models.car_history import CarHistory
from utils.auth import login_required
import requests
import json
import os
from datetime import datetime
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

vehicle_api_bp = Blueprint('vehicle_api', __name__)

# car-api 서버 설정 (환경변수 사용)
CAR_API_BASE_URL = os.getenv('CAR_API_BASE_URL', 'http://localhost:9000')
CAR_API_TIMEOUT = int(os.getenv('CAR_API_TIMEOUT', '10'))

# car-api 서버 통신 헬퍼 함수
def call_car_api(endpoint, method='GET', data=None, timeout=CAR_API_TIMEOUT):
    """car-api 서버 HTTP 통신 헬퍼"""
    try:
        url = f'{CAR_API_BASE_URL}{endpoint}'
        
        if method == 'GET':
            response = requests.get(url, timeout=timeout)
        elif method == 'POST':
            response = requests.post(url, json=data, timeout=timeout)
        elif method == 'PUT':
            response = requests.put(url, json=data, timeout=timeout)
        else:
            raise ValueError(f'지원하지 않는 HTTP 메서드: {method}')
        
        response.raise_for_status()
        return response.json()
        
    except requests.ConnectionError:
        return {'success': False, 'error': 'car-api 서버에 연결할 수 없습니다'}
    except requests.Timeout:
        return {'success': False, 'error': 'car-api 서버 응답 시간 초과'}
    except requests.HTTPError as e:
        return {'success': False, 'error': f'car-api 서버 오류: {e.response.status_code}'}
    except Exception as e:
        return {'success': False, 'error': f'통신 오류: {str(e)}'}

# 실시간 차량 상태 조회 API
@vehicle_api_bp.route('/api/vehicle/<int:vehicle_id>/status', methods=['GET'])
@login_required
def get_vehicle_status(vehicle_id):
    """car-api에서 실시간 차량 상태 조회"""
    try:
        user_id = session.get('user_id')
        
        # 소유권 확인 (BE 데이터베이스에서)
        if not Car.verify_ownership(user_id, vehicle_id):
            return jsonify({'error': '해당 차량에 대한 권한이 없습니다'}), 403
        
        # car-api에서 실시간 상태 조회
        api_response = call_car_api(f'/api/vehicle/{vehicle_id}/status')
        
        if not api_response.get('success', True):
            return jsonify({
                'success': False,
                'error': api_response.get('error', 'car-api 통신 실패'),
                'fallback_data': {
                    'message': 'car-api 서버가 응답하지 않습니다. 기본값을 표시합니다.',
                    'vehicle_id': vehicle_id,
                    'status': 'unknown'
                }
            }), 503
        
        # BE 데이터베이스에서 차량 기본 정보 조회
        car_info = Car.get_by_id(vehicle_id)
        
        # 실시간 상태와 기본 정보 결합
        combined_data = {
            'vehicle_id': vehicle_id,
            'license_plate': car_info['license_plate'] if car_info else 'Unknown',
            'model': car_info.get('model', 'Unknown'),
            'real_time_status': api_response.get('data', {}),
            'last_updated': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'data': combined_data
        })
        
    except Exception as e:
        return jsonify({'error': f'차량 상태 조회 실패: {str(e)}'}), 500

# 차량 원격 제어 API
@vehicle_api_bp.route('/api/vehicle/<int:vehicle_id>/control', methods=['POST'])
@login_required
def control_vehicle(vehicle_id):
    """car-api로 차량 원격 제어 명령 전송"""
    try:
        user_id = session.get('user_id')
        data = request.get_json()
        
        if not data or not data.get('command'):
            return jsonify({'error': '제어 명령이 필요합니다'}), 400
        
        # 소유권 확인 (BE 데이터베이스에서)
        if not Car.verify_ownership(user_id, vehicle_id):
            return jsonify({'error': '해당 차량에 대한 권한이 없습니다'}), 403
        
        command = data.get('command')
        parameters = data.get('parameters', {})
        
        # 지원되는 명령어 검증
        supported_commands = [
            'engine_start', 'engine_stop',
            'door_lock', 'door_unlock',
            'climate_on', 'climate_off',
            'set_temperature', 'set_fan_speed',
            'toggle_auto_mode', 'reset_trip_meter',
            'update_location'
        ]
        
        if command not in supported_commands:
            return jsonify({'error': f'지원하지 않는 명령어입니다: {command}'}), 400
        
        # car-api로 제어 명령 전송
        control_data = {
            'command': command,
            'parameters': parameters
        }
        
        api_response = call_car_api(
            f'/api/vehicle/{vehicle_id}/control',
            method='POST',
            data=control_data
        )
        
        # BE 데이터베이스에 제어 이력 추가
        CarHistory.add(
            car_id=vehicle_id,
            action=command,
            user_id=user_id,
            parameters=parameters
        )
        
        if not api_response.get('success', True):
            # car-api 통신 실패 시에도 이력은 남기되 실패로 표시
            return jsonify({
                'success': False,
                'error': api_response.get('error', 'car-api 제어 실패'),
                'message': '명령이 기록되었지만 차량에 전달되지 않았을 수 있습니다'
            }), 503
        
        return jsonify({
            'success': True,
            'message': f'차량 제어 명령({command})이 성공적으로 실행되었습니다',
            'data': api_response.get('data', {}),
            'executed_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        # 오류 발생 시에도 이력에 실패 기록
        try:
            CarHistory.add(
                car_id=vehicle_id,
                action=f"failed_{data.get('command', 'unknown')}",
                user_id=user_id,
                parameters={'error': str(e)}
            )
        except:
            pass  # 이력 기록 실패는 무시
        
        return jsonify({'error': f'차량 제어 실패: {str(e)}'}), 500

# car-api 서버 상태 확인 API
@vehicle_api_bp.route('/api/car-api/health', methods=['GET'])
@login_required
def check_car_api_health():
    """car-api 서버 상태 확인"""
    try:
        # car-api 서버 헬스체크
        api_response = call_car_api('/', timeout=5)
        
        if api_response.get('success', True):
            return jsonify({
                'success': True,
                'message': 'car-api 서버가 정상 작동 중입니다',
                'car_api_status': 'healthy',
                'response_data': api_response
            })
        else:
            return jsonify({
                'success': False,
                'message': 'car-api 서버가 응답하지 않습니다',
                'car_api_status': 'unhealthy',
                'error': api_response.get('error')
            }), 503
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'car-api 서버 상태 확인 실패',
            'car_api_status': 'unknown',
            'error': str(e)
        }), 500
