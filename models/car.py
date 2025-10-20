# Car 모델 - 차량 데이터 관리

from typing import Dict, List, Optional, Any
from .base import DatabaseHelper
from datetime import datetime
import random
import string

class Car:
    """차량 모델 클래스"""
    
    @staticmethod
    def register(owner_id: int, model_id: int, license_plate: str, vin: str) -> Optional[int]:
        """차량 등록"""
        try:
            query = """
            INSERT INTO cars (owner_id, model_id, license_plate, vin, created_at) 
            VALUES (%s, %s, %s, %s, %s)
            """
            car_id = DatabaseHelper.execute_insert(query, (
                owner_id, model_id, license_plate, vin, datetime.now()
            ))
            return car_id
        except Exception as e:
            print(f"Car registration error: {e}")
            return None
    
    @staticmethod
    def get_by_id(car_id: int) -> Optional[Dict]:
        """ID로 차량 조회 (vehicle_specs와 FK 조인)"""
        query = """
        SELECT c.id, c.owner_id, c.model_id, c.license_plate, c.vin, c.created_at,
               vs.model as model_name,
               vs.category,
               vs.segment,
               vs.engine_type,
               vs.displacement,
               vs.power as max_power,
               vs.torque as max_torque,
               vs.fuel_efficiency,
               vs.transmission,
               vs.drive_type as drivetrain,
               vs.voltage,
               vs.fuel_capacity,
               vs.length,
               vs.width,
               vs.height,
               vs.wheelbase,
               vs.weight as curb_weight,
               vs.max_speed,
               vs.acceleration
        FROM cars c
        LEFT JOIN vehicle_specs vs ON c.model_id = vs.id
        WHERE c.id = %s
        """
        result = DatabaseHelper.execute_query(query, (car_id,))
        return result[0] if result else None
    
    @staticmethod
    def get_by_owner(owner_id: int) -> List[Dict]:
        """소유자별 차량 목록 조회 (vehicle_specs와 FK 조인)"""
        try:
            # 실제 테이블 구조에 맞는 쿼리
            query = """
            SELECT c.id, c.owner_id, c.model_id, c.license_plate, c.vin, c.created_at,
                   vs.model as model_name,
                   vs.category,
                   vs.engine_type,
                   vs.voltage
            FROM cars c
            LEFT JOIN vehicle_specs vs ON c.model_id = vs.id
            WHERE c.owner_id = %s
            ORDER BY c.created_at DESC
            """
            result = DatabaseHelper.execute_query(query, (owner_id,))
            print(f"DEBUG: Query result for owner_id {owner_id}: {result}")
            return result
        except Exception as e:
            print(f"ERROR in get_by_owner: {e}")
            return []
    
    @staticmethod
    def get_by_owner(owner_id: int) -> List[Dict]:
        """소유자별 차량 목록 조회 (FK 관계 활용)"""
        query = """
        SELECT c.id, c.owner_id, c.model_id, c.license_plate, c.vin, c.created_at,
               vs.model as model_name,
               vs.category,
               vs.engine_type,
               vs.voltage,
               vs.displacement,
               vs.power as max_power,
               vs.torque as max_torque,
               vs.fuel_efficiency,
               vs.transmission,
               vs.drive_type as drivetrain
        FROM cars c
        LEFT JOIN vehicle_specs vs ON c.model_id = vs.id
        WHERE c.owner_id = %s
        ORDER BY c.created_at DESC
        """
        return DatabaseHelper.execute_query(query, (owner_id,))
    
    @staticmethod
    def get_unregistered() -> List[Dict]:
        """미등록 차량 목록 조회 (관리자용, FK 관계 활용)"""
        query = """
        SELECT c.id, c.owner_id, c.model_id, c.license_plate, c.vin, c.created_at,
               vs.model as model_name,
               vs.category,
               vs.engine_type,
               vs.voltage
        FROM cars c
        LEFT JOIN vehicle_specs vs ON c.model_id = vs.id
        WHERE c.owner_id IS NULL
        ORDER BY c.created_at DESC
        """
        return DatabaseHelper.execute_query(query)
    
    @staticmethod
    def verify_ownership(user_id: int, car_id: int) -> bool:
        """차량 소유권 확인"""
        query = "SELECT id FROM cars WHERE id = %s AND owner_id = %s"
        result = DatabaseHelper.execute_query(query, (car_id, user_id))
        return len(result) > 0
    
    @staticmethod
    def assign_to_user(car_id: int, user_id: int) -> bool:
        """차량을 사용자에게 할당"""
        query = "UPDATE cars SET owner_id = %s WHERE id = %s"
        return DatabaseHelper.execute_update(query, (user_id, car_id)) > 0
    
    @staticmethod
    def unregister(car_id: int) -> bool:
        """차량 등록 해제 (소유권 해제)"""
        query = "UPDATE cars SET owner_id = NULL WHERE id = %s"
        return DatabaseHelper.execute_update(query, (car_id,)) > 0
    
    @staticmethod
    def get_by_vin(vin: str) -> Optional[Dict]:
        """VIN으로 차량 조회"""
        query = "SELECT * FROM cars WHERE vin = %s"
        result = DatabaseHelper.execute_query(query, (vin,))
        return result[0] if result else None
    
    @staticmethod
    def get_by_license_plate(license_plate: str) -> Optional[Dict]:
        """번호판으로 차량 조회"""
        query = "SELECT * FROM cars WHERE license_plate = %s"
        result = DatabaseHelper.execute_query(query, (license_plate,))
        return result[0] if result else None

    @staticmethod
    def generate_random_vin() -> str:
        """랜덤 VIN(차대번호) 생성 - 17자리 영숫자"""
        # VIN은 일반적으로 17자리 영숫자로 구성 (I, O, Q 제외)
        # 실제 VIN 형식을 간소화한 버전
        allowed_chars = string.ascii_uppercase.replace('I', '').replace('O', '').replace('Q', '') + string.digits

        # WMI (World Manufacturer Identifier) - 3자리
        wmi = ''.join(random.choices(allowed_chars, k=3))

        # VDS (Vehicle Descriptor Section) - 6자리
        vds = ''.join(random.choices(allowed_chars, k=6))

        # VIS (Vehicle Identifier Section) - 8자리
        vis = ''.join(random.choices(allowed_chars, k=8))

        vin = wmi + vds + vis
        return vin

    @staticmethod
    def generate_random_license_plate() -> str:
        """랜덤 차량 번호판 생성 - 한국 형식 (예: 12가3456)"""
        # 지역번호 (2자리)
        region_num = random.randint(10, 99)

        # 용도 문자 (가, 나, 다, 라, 마, 거, 너, 더, 러, 머, 버, 서, 어, 저, 고, 노, 도, 로, 모, 보, 소, 오, 조, 구, 누, 두, 루, 무, 부, 수, 우, 주, 하, 허, 호)
        usage_chars = ['가', '나', '다', '라', '마', '거', '너', '더', '러', '머', '버', '서', '어', '저',
                       '고', '노', '도', '로', '모', '보', '소', '오', '조', '구', '누', '두', '루', '무',
                       '부', '수', '우', '주', '하', '허', '호']
        usage_char = random.choice(usage_chars)

        # 일련번호 (4자리)
        serial_num = random.randint(1000, 9999)

        license_plate = f"{region_num}{usage_char}{serial_num}"
        return license_plate