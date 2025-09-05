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
CAR_API_BASE_URL = os.getenv('CAR_API_BASE_URL', 'http://localhost:8000')  # 로컬 환경으로 수정
CAR_API_TIMEOUT = int(os.getenv('CAR_API_TIMEOUT', '10'))

# 디버그: 환경변수 확인
print(f"[DEBUG] CAR_API_BASE_URL: {CAR_API_BASE_URL}")
print(f"[DEBUG] CAR_API_TIMEOUT: {CAR_API_TIMEOUT}")

# car-api 서버 통신 헬퍼 함수
def call_car_api(endpoint, method='GET', data=None, timeout=CAR_API_TIMEOUT):
    """car-api 서버 HTTP 통신 헬퍼"""
    try:
        url = f'{CAR_API_BASE_URL}{endpoint}'
        print(f"[DEBUG] car-api 요청: {method} {url}")  # 디버그 로그
        
        if method == 'GET':
            response = requests.get(url, timeout=timeout)
        elif method == 'POST':
            response = requests.post(url, json=data, timeout=timeout)
        elif method == 'PUT':
            response = requests.put(url, json=data, timeout=timeout)
        else:
            raise ValueError(f'지원하지 않는 HTTP 메서드: {method}')
        
        print(f"[DEBUG] car-api 응답: {response.status_code}")  # 디버그 로그
        response.raise_for_status()
        result = response.json()
        print(f"[DEBUG] car-api 데이터: {result}")  # 디버그 로그
        return result
        
    except requests.ConnectionError as e:
        error_msg = f'car-api 서버에 연결할 수 없습니다: {str(e)}'
        print(f"[ERROR] {error_msg}")
        return {'success': False, 'error': error_msg}
    except requests.Timeout as e:
        error_msg = f'car-api 서버 응답 시간 초과: {str(e)}'
        print(f"[ERROR] {error_msg}")
        return {'success': False, 'error': error_msg}
    except requests.HTTPError as e:
        error_msg = f'car-api 서버 HTTP 오류: {e.response.status_code}'
        print(f"[ERROR] {error_msg}")
        return {'success': False, 'error': error_msg}
    except Exception as e:
        error_msg = f'통신 오류: {str(e)}'
        print(f"[ERROR] {error_msg}")
        return {'success': False, 'error': error_msg}

# 실시간 차량 상태 조회 API
@vehicle_api_bp.route('/api/vehicle/<int:vehicle_id>/status', methods=['GET'])
@login_required
def get_vehicle_status(vehicle_id):
    """car-api 서버에서 실시간 차량 상태 조회"""
    try:
        user_id = session.get('user_id')
        
        # 차량 소유권 확인
        if not Car.verify_ownership(user_id, vehicle_id):
            return jsonify({'error': '해당 차량에 대한 권한이 없습니다'}), 403
        
        # car-api 서버에서 상태 조회 (새로운 명세에 맞게)
        api_response = call_car_api(f'/api/vehicle/status?id={vehicle_id}')
        
        # car-api 서버 오류 처리
        if api_response.get('error'):
            return jsonify({
                'success': False,
                'error': f'car-api 서버 오류: {api_response["error"]}',
                'details': {
                    'car_api_url': CAR_API_BASE_URL,
                    'endpoint': f'/api/vehicle/status?id={vehicle_id}',
                    'vehicle_id': vehicle_id
                }
            }), 503
        
        return jsonify({
            'success': True,
            'data': api_response
        })
        
    except Exception as e:
        return jsonify({'error': f'차량 상태 조회 실패: {str(e)}'}), 500

# 차량 원격 제어 API
@vehicle_api_bp.route('/api/vehicle/<int:vehicle_id>/control', methods=['POST'])
@login_required
def control_vehicle(vehicle_id):
    """car-api로 차량 원격 제어 명령 전송 (새 명세에 맞게)"""
    try:
        user_id = session.get('user_id')
        data = request.get_json()
        
        print(f"[DEBUG] Control Vehicle - user_id: {user_id}, vehicle_id: {vehicle_id}")
        print(f"[DEBUG] Session data: {dict(session)}")
        print(f"[DEBUG] Request data: {data}")
        
        # 필수 필드 검증
        if not data or not data.get('property') or 'value' not in data:
            return jsonify({'error': 'property와 value가 필요합니다'}), 400
        
        # 소유권 확인
        ownership_check = Car.verify_ownership(user_id, vehicle_id)
        print(f"[DEBUG] Ownership check result: {ownership_check}")
        
        if not ownership_check:
            return jsonify({'error': '해당 차량에 대한 권한이 없습니다'}), 403
        
        # horn, flash, hazard_lights는 이력만 남기고 car-api에 전송하지 않음 (Car-API 미지원)
        if data['property'] in ['horn', 'flash', 'hazard_lights']:
            # 제어 이력 저장 (BE 데이터베이스에만)
            CarHistory.add(
                car_id=vehicle_id,
                action=f"{data['property']}_activated",
                user_id=user_id,
                parameters={
                    'property': data['property'],
                    'value': data['value'],
                    'note': 'Temporary action - logged only'
                },
                success=True
            )
            
            # 성공 응답 반환 (상태는 변경하지 않음)
            return jsonify({
                'success': True,
                'message': f"{data['property']} 명령이 실행되었습니다",
                'data': None  # 상태 변경 없음
            }), 200
        
        # 일반 제어 명령은 car-api로 전송
        control_data = {
            'id': vehicle_id,
            'property': data['property'],
            'value': data['value']
        }
        
        # car-api로 제어 명령 전송
        api_response = call_car_api('/api/vehicle/control', 'POST', control_data)
        
        if api_response.get('error'):
            return jsonify({
                'success': False,
                'error': api_response['error']
            }), 503
        
        # 제어 이력 저장 (BE 데이터베이스에)
        CarHistory.add(
            car_id=vehicle_id,
            action=f"{data['property']}_{data['value']}",
            user_id=user_id,
            parameters={
                'property': data['property'],
                'value': data['value'],
                'car_api_response': api_response
            },
            result='success'
        )
        
        return jsonify({
            'success': True,
            'message': api_response.get('message', '차량 제어가 완료되었습니다'),
            'vehicle_id': vehicle_id,
            'property': data['property'],
            'value': data['value']
        })
        
    except Exception as e:
        # 실패 이력도 저장
        try:
            CarHistory.create(
                vehicle_id=vehicle_id,
                user_id=session.get('user_id'),
                command=data.get('property', 'unknown'),
                value=str(data.get('value', 'unknown')),
                status='error',
                result=str(e)
            )
        except:
            pass
        
        return jsonify({'error': f'차량 제어 실패: {str(e)}'}), 500
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
        # car-api 서버 헬스체크 (README에 따르면 /health 엔드포인트)
        api_response = call_car_api('/health', timeout=5)
        
        if api_response.get('error'):
            return jsonify({
                'success': False,
                'message': 'car-api 서버가 응답하지 않습니다',
                'car_api_status': 'unhealthy',
                'car_api_url': CAR_API_BASE_URL,
                'error': api_response.get('error')
            }), 503
        else:
            return jsonify({
                'success': True,
                'message': 'car-api 서버가 정상 작동 중입니다',
                'car_api_status': 'healthy',
                'car_api_url': CAR_API_BASE_URL,
                'response_data': api_response
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'car-api 서버 상태 확인 실패',
            'car_api_status': 'error',
            'error': str(e)
        }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'car-api 서버 상태 확인 실패',
            'car_api_status': 'unknown',
            'error': str(e)
        }), 500

# 차량 제어 기록 조회 API
@vehicle_api_bp.route('/api/vehicle/<int:vehicle_id>/history', methods=['GET'])
@login_required
def get_vehicle_control_history(vehicle_id):
    """차량 제어 기록 조회 (car_history 테이블에서)"""
    try:
        user_id = session.get('user_id')
        
        # 차량 소유권 확인
        if not Car.verify_ownership(user_id, vehicle_id):
            return jsonify({'error': '해당 차량에 대한 권한이 없습니다'}), 403
        
        # URL 파라미터 처리
        limit = request.args.get('limit', 50, type=int)  # 기본 50개
        page = request.args.get('page', 1, type=int)     # 기본 1페이지
        
        # 제한값 검증
        if limit > 200:
            limit = 200  # 최대 200개
        if page < 1:
            page = 1
            
        offset = (page - 1) * limit
        
        # car_history에서 해당 차량의 제어 기록 조회
        history_records = CarHistory.get_by_car_id(
            car_id=vehicle_id, 
            limit=limit, 
            offset=offset
        )
        
        # 전체 기록 수 조회 (페이징 정보용)
        total_records = CarHistory.get_count_by_car_id(vehicle_id)
        
        # 응답 데이터 구성
        records = []
        for record in history_records:
            records.append({
                'id': record.get('id'),
                'action': record.get('action'),
                'timestamp': record.get('timestamp').isoformat() if record.get('timestamp') else None,
                'parameters': record.get('parameters', {}),
                'result': record.get('result', 'success'),
                'user_id': record.get('user_id')
            })
        
        return jsonify({
            'success': True,
            'data': {
                'vehicle_id': vehicle_id,
                'records': records,
                'pagination': {
                    'total_records': total_records,
                    'page': page,
                    'limit': limit,
                    'total_pages': (total_records + limit - 1) // limit,
                    'has_next': (page * limit) < total_records,
                    'has_prev': page > 1
                }
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'제어 기록 조회 실패: {str(e)}'}), 500
