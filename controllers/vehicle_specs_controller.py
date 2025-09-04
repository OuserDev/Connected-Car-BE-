# 차량 스펙 관리 API 컨트롤러
from flask import Blueprint, jsonify, request
from models.vehicle_spec import VehicleSpec
from utils.auth import login_required

vehicle_specs_bp = Blueprint('vehicle_specs', __name__)

# 모든 차량 스펙 조회 API
@vehicle_specs_bp.route('/api/specs', methods=['GET'])
@login_required
def get_all_specs():
    """모든 차량 스펙 정보 조회"""
    try:
        specs = VehicleSpec.get_all()
        
        return jsonify({
            'success': True,
            'data': specs
        })
        
    except Exception as e:
        return jsonify({'error': f'차량 스펙 조회 실패: {str(e)}'}), 500

# 특정 모델의 차량 스펙 조회 API
@vehicle_specs_bp.route('/api/specs/<int:model_id>', methods=['GET'])
@login_required
def get_specs_by_model(model_id):
    """특정 모델 ID의 차량 스펙 정보 조회"""
    try:
        spec = VehicleSpec.get_by_model_id(model_id)
        
        if not spec:
            return jsonify({'error': '해당 모델의 스펙 정보를 찾을 수 없습니다'}), 404
        
        return jsonify({
            'success': True,
            'data': spec
        })
        
    except Exception as e:
        return jsonify({'error': f'차량 스펙 조회 실패: {str(e)}'}), 500

# 차량 스펙 등록 API
@vehicle_specs_bp.route('/api/specs', methods=['POST'])
@login_required
def create_spec():
    """새 차량 스펙 등록"""
    try:
        data = request.get_json()
        
        # 필수 필드 검증
        required_fields = ['model_id', 'model_name', 'manufacturer', 'year']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field}는 필수 입력 항목입니다'}), 400
        
        # 차량 스펙 등록
        spec_id = VehicleSpec.create(data)
        
        if not spec_id:
            return jsonify({'error': '차량 스펙 등록 실패'}), 500
        
        return jsonify({
            'success': True,
            'message': '차량 스펙이 성공적으로 등록되었습니다',
            'spec_id': spec_id
        })
        
    except Exception as e:
        return jsonify({'error': f'차량 스펙 등록 실패: {str(e)}'}), 500

# 차량 스펙 업데이트 API
@vehicle_specs_bp.route('/api/specs/<int:model_id>', methods=['PUT'])
@login_required
def update_spec(model_id):
    """차량 스펙 정보 업데이트"""
    try:
        data = request.get_json()
        
        # 기존 스펙 존재 확인
        existing_spec = VehicleSpec.get_by_model_id(model_id)
        if not existing_spec:
            return jsonify({'error': '해당 모델의 스펙 정보를 찾을 수 없습니다'}), 404
        
        # 차량 스펙 업데이트
        success = VehicleSpec.update(model_id, data)
        
        if not success:
            return jsonify({'error': '차량 스펙 업데이트 실패'}), 500
        
        return jsonify({
            'success': True,
            'message': '차량 스펙이 성공적으로 업데이트되었습니다'
        })
        
    except Exception as e:
        return jsonify({'error': f'차량 스펙 업데이트 실패: {str(e)}'}), 500

# 차량 스펙 삭제 API
@vehicle_specs_bp.route('/api/specs/<int:model_id>', methods=['DELETE'])
@login_required
def delete_spec(model_id):
    """차량 스펙 삭제"""
    try:
        # 기존 스펙 존재 확인
        existing_spec = VehicleSpec.get_by_model_id(model_id)
        if not existing_spec:
            return jsonify({'error': '해당 모델의 스펙 정보를 찾을 수 없습니다'}), 404
        
        # 차량 스펙 삭제
        success = VehicleSpec.delete(model_id)
        
        if not success:
            return jsonify({'error': '차량 스펙 삭제 실패'}), 500
        
        return jsonify({
            'success': True,
            'message': '차량 스펙이 성공적으로 삭제되었습니다'
        })
        
    except Exception as e:
        return jsonify({'error': f'차량 스펙 삭제 실패: {str(e)}'}), 500
