# CarHistory 모델 - 차량 제어 이력 관리

from typing import Dict, List, Optional, Any
from .base import DatabaseHelper
import json
from datetime import datetime

class CarHistory:
    """차량 이력 모델 클래스"""
    
    @staticmethod
    def add(car_id: int, action: str, user_id: int, parameters: Dict = None, result: str = 'success') -> Optional[int]:
        """차량 제어 이력 추가"""
        try:
            params_json = json.dumps(parameters) if parameters else None
            
            query = """
            INSERT INTO car_history (car_id, action, user_id, parameters, result, timestamp) 
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            history_id = DatabaseHelper.execute_insert(query, (
                car_id, action, user_id, params_json, result, datetime.now()
            ))
            return history_id
        except Exception as e:
            print(f"History addition error: {e}")
            return None
    
    @staticmethod
    def get_by_car(car_id: int, limit: int = 50) -> List[Dict]:
        """차량별 이력 조회"""
        query = """
        SELECT ch.*, u.username 
        FROM car_history ch
        LEFT JOIN users u ON ch.user_id = u.id
        WHERE ch.car_id = %s
        ORDER BY ch.timestamp DESC
        LIMIT %s
        """
        results = DatabaseHelper.execute_query(query, (car_id, limit))
        
        # parameters JSON 파싱
        for result in results:
            if result.get('parameters'):
                try:
                    result['parameters'] = json.loads(result['parameters'])
                except:
                    result['parameters'] = {}
            else:
                result['parameters'] = {}
        
        return results
    
    @staticmethod
    def get_by_user(user_id: int, limit: int = 50) -> List[Dict]:
        """사용자별 이력 조회"""
        query = """
        SELECT ch.*, c.license_plate, vs.model
        FROM car_history ch
        LEFT JOIN cars c ON ch.car_id = c.id
        LEFT JOIN vehicle_specs vs ON c.model_id = vs.id
        WHERE ch.user_id = %s
        ORDER BY ch.timestamp DESC
        LIMIT %s
        """
        results = DatabaseHelper.execute_query(query, (user_id, limit))
        
        # parameters JSON 파싱
        for result in results:
            if result.get('parameters'):
                try:
                    result['parameters'] = json.loads(result['parameters'])
                except:
                    result['parameters'] = {}
            else:
                result['parameters'] = {}
        
        return results
    
    @staticmethod
    def get_recent(limit: int = 100) -> List[Dict]:
        """최근 이력 조회 (관리자용)"""
        query = """
        SELECT ch.*, u.username, c.license_plate, vs.model
        FROM car_history ch
        LEFT JOIN users u ON ch.user_id = u.id
        LEFT JOIN cars c ON ch.car_id = c.id
        LEFT JOIN vehicle_specs vs ON c.model_id = vs.id
        ORDER BY ch.timestamp DESC
        LIMIT %s
        """
        results = DatabaseHelper.execute_query(query, (limit,))
        
        # parameters JSON 파싱
        for result in results:
            if result.get('parameters'):
                try:
                    result['parameters'] = json.loads(result['parameters'])
                except:
                    result['parameters'] = {}
            else:
                result['parameters'] = {}
        
        return results
    
    @staticmethod
    def get_statistics(car_id: int = None, days: int = 30) -> Dict:
        """차량 제어 통계 조회"""
        if car_id:
            query = """
            SELECT action, COUNT(*) as count
            FROM car_history
            WHERE car_id = %s AND timestamp >= DATE_SUB(NOW(), INTERVAL %s DAY)
            GROUP BY action
            ORDER BY count DESC
            """
            params = (car_id, days)
        else:
            query = """
            SELECT action, COUNT(*) as count
            FROM car_history
            WHERE timestamp >= DATE_SUB(NOW(), INTERVAL %s DAY)
            GROUP BY action
            ORDER BY count DESC
            """
            params = (days,)
        
        results = DatabaseHelper.execute_query(query, params)
        
        # 통계 데이터 구성
        statistics = {
            'total_actions': sum(r['count'] for r in results),
            'actions_by_type': {r['action']: r['count'] for r in results},
            'period_days': days
        }
        
        if car_id:
            statistics['car_id'] = car_id
        
        return statistics
    
    @staticmethod
    def get_by_car_id(car_id: int, limit: int = 50, offset: int = 0) -> List[Dict]:
        """차량별 제어 기록 조회 (페이징 지원)"""
        query = """
        SELECT ch.*, u.username 
        FROM car_history ch
        LEFT JOIN users u ON ch.user_id = u.id
        WHERE ch.car_id = %s
        ORDER BY ch.timestamp DESC
        LIMIT %s OFFSET %s
        """
        results = DatabaseHelper.execute_query(query, (car_id, limit, offset))
        
        # parameters JSON 파싱
        for result in results:
            if result.get('parameters'):
                try:
                    result['parameters'] = json.loads(result['parameters'])
                except:
                    result['parameters'] = {}
            else:
                result['parameters'] = {}
        
        return results
    
    @staticmethod
    def get_count_by_car_id(car_id: int) -> int:
        """차량별 제어 기록 총 개수 조회"""
        query = "SELECT COUNT(*) as count FROM car_history WHERE car_id = %s"
        result = DatabaseHelper.execute_query(query, (car_id,))
        return result[0]['count'] if result else 0