# VehicleSpec 모델 - 차량 스펙 정보 관리

from typing import Dict, List, Optional, Any
from .base import DatabaseHelper

class VehicleSpec:
    """차량 스펙 모델 클래스"""
    
    @staticmethod
    def get_all() -> List[Dict]:
        """모든 차량 스펙 조회"""
        query = """
        SELECT * FROM vehicle_specs 
        ORDER BY category, model
        """
        return DatabaseHelper.execute_query(query)
    
    @staticmethod
    def get_by_id(spec_id: int) -> Optional[Dict]:
        """ID로 차량 스펙 조회"""
        query = "SELECT * FROM vehicle_specs WHERE id = %s"
        result = DatabaseHelper.execute_query(query, (spec_id,))
        return result[0] if result else None
    
    @staticmethod
    def get_by_model_id(model_id: int) -> Optional[Dict]:
        """model_id로 차량 스펙 조회 (FK 관계 활용)"""
        query = "SELECT * FROM vehicle_specs WHERE id = %s"
        result = DatabaseHelper.execute_query(query, (model_id,))
        return result[0] if result else None
    
    @staticmethod
    def get_by_model(model: str) -> Optional[Dict]:
        """모델명으로 차량 스펙 조회"""
        query = "SELECT * FROM vehicle_specs WHERE model = %s"
        result = DatabaseHelper.execute_query(query, (model,))
        return result[0] if result else None
    
    @staticmethod
    def get_by_category(category: str) -> List[Dict]:
        """카테고리별 차량 스펙 조회"""
        query = """
        SELECT * FROM vehicle_specs 
        WHERE category = %s 
        ORDER BY model
        """
        return DatabaseHelper.execute_query(query, (category,))
    
    @staticmethod
    def get_electric_vehicles() -> List[Dict]:
        """전기차 스펙 조회"""
        query = """
        SELECT * FROM vehicle_specs 
        WHERE engine_type = 'Electric' 
        ORDER BY model
        """
        return DatabaseHelper.execute_query(query)
    
    @staticmethod
    def get_by_voltage_system(voltage_system: str) -> List[Dict]:
        """전압 시스템별 차량 스펙 조회"""
        query = """
        SELECT * FROM vehicle_specs 
        WHERE voltage_system LIKE %s 
        ORDER BY category, model
        """
        return DatabaseHelper.execute_query(query, (f'%{voltage_system}%',))
    
    @staticmethod
    def search(keyword: str) -> List[Dict]:
        """키워드로 차량 스펙 검색"""
        query = """
        SELECT * FROM vehicle_specs 
        WHERE model LIKE %s OR category LIKE %s OR engine_type LIKE %s
        ORDER BY model
        """
        search_term = f'%{keyword}%'
        return DatabaseHelper.execute_query(query, (search_term, search_term, search_term))
    
    @staticmethod
    def get_stats() -> Dict:
        """차량 스펙 통계 조회"""
        queries = {
            'total_models': "SELECT COUNT(*) as count FROM vehicle_specs",
            'by_category': """
                SELECT category, COUNT(*) as count 
                FROM vehicle_specs 
                GROUP BY category 
                ORDER BY count DESC
            """,
            'by_engine_type': """
                SELECT engine_type, COUNT(*) as count 
                FROM vehicle_specs 
                GROUP BY engine_type 
                ORDER BY count DESC
            """,
            'voltage_distribution': """
                SELECT voltage_system, COUNT(*) as count 
                FROM vehicle_specs 
                GROUP BY voltage_system 
                ORDER BY count DESC
            """
        }
        
        stats = {}
        
        # 전체 모델 수
        total_result = DatabaseHelper.execute_query(queries['total_models'])
        stats['total_models'] = total_result[0]['count'] if total_result else 0
        
        # 카테고리별 분포
        category_results = DatabaseHelper.execute_query(queries['by_category'])
        stats['by_category'] = {r['category']: r['count'] for r in category_results}
        
        # 엔진 타입별 분포
        engine_results = DatabaseHelper.execute_query(queries['by_engine_type'])
        stats['by_engine_type'] = {r['engine_type']: r['count'] for r in engine_results}
        
        # 전압 시스템별 분포
        voltage_results = DatabaseHelper.execute_query(queries['voltage_distribution'])
        stats['voltage_distribution'] = {r['voltage_system']: r['count'] for r in voltage_results}
        
        return stats