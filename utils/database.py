# MySQL 데이터베이스 설정 및 연결 관리

import pymysql
import json
from typing import Dict, List, Optional, Any
from contextlib import contextmanager

class DatabaseConfig:
    """데이터베이스 설정 클래스"""
    
    # 실제 DB 서버 설정 (주석 처리)
    # HOST = 'your-db-server.com'
    # PORT = 3306
    # DATABASE = 'connected_car_service'
    # USERNAME = 'your-username'
    # PASSWORD = 'your-password'
    
    # 로컬 개발용 설정
    HOST = 'localhost'
    PORT = 3306
    DATABASE = 'connected_car_service'
    USERNAME = 'root'
    PASSWORD = 'ensiz225712'  # 일반적인 비밀번호 시도
    
    CHARSET = 'utf8mb4'
    AUTOCOMMIT = True

class DatabaseConnection:
    """데이터베이스 연결 관리 클래스"""
    
    @staticmethod
    @contextmanager
    def get_connection():
        """데이터베이스 연결 컨텍스트 매니저"""
        connection = None
        try:
            connection = pymysql.connect(
                host=DatabaseConfig.HOST,
                port=DatabaseConfig.PORT,
                user=DatabaseConfig.USERNAME,
                password=DatabaseConfig.PASSWORD,
                database=DatabaseConfig.DATABASE,
                charset=DatabaseConfig.CHARSET,
                autocommit=DatabaseConfig.AUTOCOMMIT,
                cursorclass=pymysql.cursors.DictCursor  # 딕셔너리 형태로 결과 반환
            )
            yield connection
        except Exception as e:
            if connection:
                connection.rollback()
            raise e
        finally:
            if connection:
                connection.close()

class DatabaseHelper:
    """데이터베이스 헬퍼 함수들"""
    
    @staticmethod
    def execute_query(query: str, params: tuple = None) -> List[Dict]:
        """SELECT 쿼리 실행"""
        with DatabaseConnection.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()
    
    @staticmethod
    def execute_insert(query: str, params: tuple = None) -> int:
        """INSERT 쿼리 실행 후 마지막 삽입 ID 반환"""
        with DatabaseConnection.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.lastrowid
    
    @staticmethod
    def execute_update(query: str, params: tuple = None) -> int:
        """UPDATE/DELETE 쿼리 실행 후 영향받은 행 수 반환"""
        with DatabaseConnection.get_connection() as conn:
            with conn.cursor() as cursor:
                return cursor.execute(query, params)
    
    @staticmethod
    def execute_batch(query: str, params_list: List[tuple]) -> int:
        """배치 INSERT/UPDATE 실행"""
        with DatabaseConnection.get_connection() as conn:
            with conn.cursor() as cursor:
                return cursor.executemany(query, params_list)

# 사용자 관련 데이터베이스 함수들
class UserDatabase:
    """사용자 데이터베이스 작업"""
    
    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[Dict]:
        """사용자 ID로 사용자 정보 조회"""
        query = "SELECT * FROM users WHERE id = %s"
        result = DatabaseHelper.execute_query(query, (user_id,))
        return result[0] if result else None
    
    @staticmethod
    def get_user_by_username(username: str) -> Optional[Dict]:
        """사용자명으로 사용자 정보 조회"""
        query = "SELECT * FROM users WHERE username = %s"
        result = DatabaseHelper.execute_query(query, (username,))
        return result[0] if result else None
    
    @staticmethod
    def create_user(username: str, password: str, email: str, name: str, phone: str = None) -> int:
        """새 사용자 생성"""
        query = """
        INSERT INTO users (username, password, email, name, phone) 
        VALUES (%s, %s, %s, %s, %s)
        """
        return DatabaseHelper.execute_insert(query, (username, password, email, name, phone))
    
    @staticmethod
    def get_user_cards(user_id: int) -> List[Dict]:
        """사용자의 등록된 카드 목록 조회"""
        query = "SELECT * FROM registered_cards WHERE user_id = %s ORDER BY is_default DESC, created_at"
        return DatabaseHelper.execute_query(query, (user_id,))

# 차량 관련 데이터베이스 함수들
class CarDatabase:
    """차량 데이터베이스 작업"""
    
    @staticmethod
    def get_cars_by_owner(owner_id: int) -> List[Dict]:
        """소유자 ID로 차량 목록 조회"""
        query = """
        SELECT c.*, vs.model, vs.category, vs.voltage 
        FROM cars c 
        LEFT JOIN vehicle_specs vs ON c.model_id = vs.id 
        WHERE c.owner_id = %s
        ORDER BY c.created_at DESC
        """
        return DatabaseHelper.execute_query(query, (owner_id,))
    
    @staticmethod
    def get_car_by_id(car_id: int) -> Optional[Dict]:
        """차량 ID로 차량 정보 조회"""
        query = """
        SELECT c.*, vs.model, vs.category, vs.voltage 
        FROM cars c 
        LEFT JOIN vehicle_specs vs ON c.model_id = vs.id 
        WHERE c.id = %s
        """
        result = DatabaseHelper.execute_query(query, (car_id,))
        return result[0] if result else None
    
    @staticmethod
    def register_car(owner_id: int, model_id: int, license_plate: str, vin: str) -> int:
        """새 차량 등록"""
        query = """
        INSERT INTO cars (owner_id, model_id, license_plate, vin, created_at) 
        VALUES (%s, %s, %s, %s, CURDATE())
        """
        return DatabaseHelper.execute_insert(query, (owner_id, model_id, license_plate, vin))
    
    @staticmethod
    def verify_car_ownership(user_id: int, car_id: int) -> bool:
        """차량 소유권 확인"""
        query = "SELECT 1 FROM cars WHERE id = %s AND owner_id = %s"
        result = DatabaseHelper.execute_query(query, (car_id, user_id))
        return len(result) > 0

# 차량 이력 관련 데이터베이스 함수들
class CarHistoryDatabase:
    """차량 이력 데이터베이스 작업"""
    
    @staticmethod
    def add_history(car_id: int, action: str, user_id: int = None, parameters: Dict = None) -> int:
        """차량 제어 이력 추가"""
        query = """
        INSERT INTO car_history (car_id, action, user_id, parameters) 
        VALUES (%s, %s, %s, %s)
        """
        params_json = json.dumps(parameters) if parameters else None
        return DatabaseHelper.execute_insert(query, (car_id, action, user_id, params_json))
    
    @staticmethod
    def get_car_history(car_id: int, limit: int = 50) -> List[Dict]:
        """차량 제어 이력 조회"""
        query = """
        SELECT ch.*, u.username 
        FROM car_history ch 
        LEFT JOIN users u ON ch.user_id = u.id 
        WHERE ch.car_id = %s 
        ORDER BY ch.timestamp DESC 
        LIMIT %s
        """
        return DatabaseHelper.execute_query(query, (car_id, limit))

# 차량 스펙 관련 데이터베이스 함수들
class VehicleSpecDatabase:
    """차량 스펙 데이터베이스 작업"""
    
    @staticmethod
    def get_all_specs() -> List[Dict]:
        """모든 차량 스펙 조회"""
        query = "SELECT * FROM vehicle_specs ORDER BY category, model"
        return DatabaseHelper.execute_query(query)
    
    @staticmethod
    def get_spec_by_id(spec_id: int) -> Optional[Dict]:
        """스펙 ID로 차량 스펙 조회"""
        query = "SELECT * FROM vehicle_specs WHERE id = %s"
        result = DatabaseHelper.execute_query(query, (spec_id,))
        return result[0] if result else None
    
    @staticmethod
    def get_specs_by_category(category: str) -> List[Dict]:
        """카테고리별 차량 스펙 조회"""
        query = "SELECT * FROM vehicle_specs WHERE category = %s ORDER BY model"
        return DatabaseHelper.execute_query(query, (category,))

# 데이터베이스 테스트 함수
def test_database_connection():
    """데이터베이스 연결 테스트"""
    try:
        with DatabaseConnection.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1 as test")
                result = cursor.fetchone()
                print(f"✅ 데이터베이스 연결 성공: {result}")
                return True
    except Exception as e:
        print(f"❌ 데이터베이스 연결 실패: {str(e)}")
        return False

if __name__ == "__main__":
    # 데이터베이스 연결 테스트
    test_database_connection()
