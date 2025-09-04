# MySQL 데이터베이스 기본 설정 및 연결 관리

import pymysql
import json
import os
from typing import Dict, List, Optional, Any
from contextlib import contextmanager
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

class DatabaseConfig:
    """데이터베이스 설정 클래스"""
    
    # 환경변수에서 설정값 로드 (기본값 제공)
    HOST = os.getenv('DB_HOST', 'localhost')
    PORT = int(os.getenv('DB_PORT', '3306'))
    DATABASE = os.getenv('DB_NAME', 'connected_car_service')
    USERNAME = os.getenv('DB_USER', 'root')
    PASSWORD = os.getenv('DB_PASSWORD', 'student')
    
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
    """데이터베이스 헬퍼 클래스 - 공통 쿼리 실행"""
    
    @staticmethod
    def execute_query(query: str, params: tuple = None) -> List[Dict]:
        """SELECT 쿼리 실행"""
        try:
            with DatabaseConnection.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params or ())
                    return cursor.fetchall()
        except Exception as e:
            print(f"Query execution error: {e}")
            return []
    
    @staticmethod
    def execute_insert(query: str, params: tuple = None) -> int:
        """INSERT 쿼리 실행 후 생성된 ID 반환"""
        try:
            with DatabaseConnection.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params or ())
                    return cursor.lastrowid
        except Exception as e:
            print(f"Insert execution error: {e}")
            return 0
    
    @staticmethod
    def execute_update(query: str, params: tuple = None) -> int:
        """UPDATE/DELETE 쿼리 실행 후 영향받은 행 수 반환"""
        try:
            with DatabaseConnection.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params or ())
                    return cursor.rowcount
        except Exception as e:
            print(f"Update execution error: {e}")
            return 0

def test_database_connection():
    """데이터베이스 연결 테스트"""
    try:
        with DatabaseConnection.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1 as test")
                result = cursor.fetchone()
                return result and result['test'] == 1
    except Exception as e:
        print(f"Database connection test failed: {e}")
        return False