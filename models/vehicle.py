import json
import os
import random
from datetime import datetime

class VehicleModel:
    def __init__(self):
        self.data_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'cars.json')
        self.history_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'car_history.json')
        self.specs_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'vehicle_specs.json')
        self.driving_records_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'driving_records.json')
        self._load_data()
    
    def _load_data(self):
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.cars = data.get('cars', [])
                self.next_id = data.get('next_id', 1)
        except FileNotFoundError:
            self.cars = []
            self.next_id = 1
        
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                self.history = json.load(f)
        except FileNotFoundError:
            self.history = []
        
        try:
            with open(self.specs_file, 'r', encoding='utf-8') as f:
                specs_data = json.load(f)
                self.vehicle_specs = specs_data.get('vehicle_specs', {})
        except FileNotFoundError:
            self.vehicle_specs = {}
        
        try:
            with open(self.driving_records_file, 'r', encoding='utf-8') as f:
                driving_data = json.load(f)
                self.trips = driving_data.get('trips', [])
                self.statistics = driving_data.get('statistics', {})
                self.next_trip_id = driving_data.get('next_trip_id', 1)
        except FileNotFoundError:
            self.trips = []
            self.statistics = {}
            self.next_trip_id = 1
    
    def _save_data(self):
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump({'cars': self.cars, 'next_id': self.next_id}, f, ensure_ascii=False, indent=2)
    
    def _save_history(self):
        os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)
    
    def _save_driving_records(self):
        os.makedirs(os.path.dirname(self.driving_records_file), exist_ok=True)
        with open(self.driving_records_file, 'w', encoding='utf-8') as f:
            json.dump({
                'trips': self.trips,
                'statistics': self.statistics,
                'next_trip_id': self.next_trip_id
            }, f, ensure_ascii=False, indent=2)
    
    def register_car(self, owner_id, model_id, license_plate='', voltage='12V'):
        car = {
            'id': self.next_id,
            'owner_id': owner_id,
            'model_id': model_id,
            'license_plate': license_plate,
            'engine_state': 'off',
            'door_state': 'locked',
            'fuel': 100,
            'battery': 12.6,
            'voltage': voltage,
            'climate': {
                'ac_state': 'off',
                'heater_state': 'off',
                'target_temp': 22,
                'current_temp': 20,
                'fan_speed': 0,
                'auto_mode': False
            },
            'tire_pressure': {
                'front_left': 2.3,
                'front_right': 2.3,
                'rear_left': 2.3,
                'rear_right': 2.3,
                'recommended': 2.3,
                'unit': 'bar',
                'warning_threshold': 1.8,
                'last_checked': datetime.now().isoformat() + 'Z'
            },
            'odometer': {
                'total_km': 0,
                'trip_a_km': 0.0,
                'trip_b_km': 0.0,
                'last_updated': datetime.now().isoformat() + 'Z'
            },
            'location': {
                'lat': 37.5665,
                'lng': 126.9780
            },
            'created_at': datetime.now().isoformat()
        }
        self.cars.append(car)
        self.next_id += 1
        self._save_data()
        
        return car
    
    # 관리자 전용 함수 제거됨 - get_all_cars() 별도 관리자 VM에서 구현 예정
    
    def get_car_by_id(self, car_id):
        for car in self.cars:
            if car['id'] == car_id:
                return car
        return None
    
    def get_cars_by_owner(self, owner_id):
        owned_cars = []
        for car in self.cars:
            if car.get('owner_id') == owner_id:
                model_id = car.get('model_id', 1)
                specs = self.vehicle_specs.get(str(model_id), {})
                car_with_specs = car.copy()
                car_with_specs['brand'] = 'Hyundai'
                car_with_specs['model'] = specs.get('model', 'Unknown')
                car_with_specs['specs'] = specs
                owned_cars.append(car_with_specs)
        return owned_cars
    
    def get_unregistered_cars(self):
        unregistered_cars = []
        for car in self.cars:
            if car.get('owner_id') is None:
                model_id = car.get('model_id', 1)
                specs = self.vehicle_specs.get(str(model_id), {})
                car_with_specs = car.copy()
                car_with_specs['brand'] = 'Hyundai'
                car_with_specs['model'] = specs.get('model', 'Unknown')
                car_with_specs['specs'] = specs
                unregistered_cars.append(car_with_specs)
        return unregistered_cars
    
    def get_car_by_vin(self, vin):
        for car in self.cars:
            if car.get('vin') == vin:
                return car
        return None
    
    def get_car_by_license(self, license_plate):
        for car in self.cars:
            if car.get('license_plate') == license_plate:
                return car
        return None
    
    def get_car_status(self, car_id):
        car = self.get_car_by_id(car_id)
        if car:
            model_id = car.get('model_id', 1)
            specs = self.vehicle_specs.get(str(model_id), {})
            
            return {
                'id': car['id'],
                'owner_id': car.get('owner_id'),
                'brand': 'Hyundai',
                'model': specs.get('model', 'Unknown'),
                'model_id': model_id,
                'license_plate': car.get('license_plate', ''),
                'voltage': car.get('voltage', '12V'),
                'engine': car['engine_state'],
                'door': car['door_state'],
                'fuel': car.get('fuel', 0),
                'battery': car.get('battery', 0),
                'location': car.get('location', {}),
                'climate': car.get('climate', {}),
                'tire_pressure': car.get('tire_pressure', {}),
                'odometer': car.get('odometer', {}),
                'specs': specs
            }
        return None
    
    def is_owner(self, car_id, user_id):
        car = self.get_car_by_id(car_id)
        return car and car.get('owner_id') == user_id
    
    def assign_car_to_user(self, car_id, user_id):
        for car in self.cars:
            if car['id'] == car_id:
                car['owner_id'] = user_id
                self._save_data()
                return car
        return None
    
    # 관리자 전용 함수 제거됨 - assign_car_to_user() 별도 관리자 VM에서 구현 예정
    
    def execute_command(self, car_id, action, user_id=None, value=None):
        car = self.get_car_by_id(car_id)
        if not car:
            return False
        
        # 권한 검증: 소유자만 제어 가능
        if user_id and not self.is_owner(car_id, user_id):
            return False
        
        # 공조기 데이터가 없으면 기본값으로 초기화
        if 'climate' not in car:
            car['climate'] = {
                'ac_state': 'off',
                'heater_state': 'off',
                'target_temp': 22,
                'current_temp': 20,
                'fan_speed': 0,
                'auto_mode': False
            }
        
        if action == 'engine_on':
            car['engine_state'] = 'on'
        elif action == 'engine_off':
            car['engine_state'] = 'off'
        elif action == 'door_lock':
            car['door_state'] = 'locked'
        elif action == 'door_unlock':
            car['door_state'] = 'unlocked'
        elif action == 'door_open':
            car['door_state'] = 'open'
        elif action == 'door_close':
            car['door_state'] = 'closed'
        # 공조기 제어 명령들
        elif action == 'ac_on':
            car['climate']['ac_state'] = 'on'
            car['climate']['heater_state'] = 'off'  # AC 켜면 히터는 끔
        elif action == 'ac_off':
            car['climate']['ac_state'] = 'off'
        elif action == 'heater_on':
            car['climate']['heater_state'] = 'on' 
            car['climate']['ac_state'] = 'off'  # 히터 켜면 AC는 끔
        elif action == 'heater_off':
            car['climate']['heater_state'] = 'off'
        elif action == 'temp_set':
            if value is not None:
                try:
                    temp = int(value)
                    if 16 <= temp <= 30:  # 온도 범위 제한
                        car['climate']['target_temp'] = temp
                    else:
                        return False
                except (ValueError, TypeError):
                    return False
            else:
                return False
        elif action == 'fan_speed':
            if value is not None:
                try:
                    speed = int(value)
                    if 0 <= speed <= 7:  # 팬 속도 0-7 단계
                        car['climate']['fan_speed'] = speed
                    else:
                        return False
                except (ValueError, TypeError):
                    return False
            else:
                return False
        elif action == 'auto_climate_on':
            car['climate']['auto_mode'] = True
        elif action == 'auto_climate_off':
            car['climate']['auto_mode'] = False
        elif action == 'horn':
            # 경적은 단순히 로그만 남기고 실제 차량 상태 변경 없음
            pass
        else:
            return False
        
        self._save_data()
        
        history_entry = {
            'id': len(self.history) + 1,
            'car_id': car_id,
            'action': action,
            'timestamp': datetime.now().isoformat() + 'Z'
        }
        self.history.append(history_entry)
        self._save_history()
        return True
    
    def get_car_history(self, car_id):
        car_exists = any(car['id'] == car_id for car in self.cars)
        if not car_exists:
            return None
        
        return [entry for entry in self.history if entry['car_id'] == car_id]
    
    def get_and_update_location(self, car_id, user_id=None):
        car = self.get_car_by_id(car_id)
        if not car:
            return None
        
        # 권한 검증: 소유자만 위치 조회 가능
        if user_id and not self.is_owner(car_id, user_id):
            return None
        
        # 현재 위치 가져오기
        current_location = car.get('location', {'lat': 37.5665, 'lng': 126.9780})
        
        # 시동이 켜져 있으면 위치 업데이트 (차량이 움직였다고 가정)
        if car.get('engine_state') == 'on':
            # 서울 시내 범위에서 랜덤하게 약간씩 이동 (약 100-500m 범위)
            lat_change = random.uniform(-0.005, 0.005)  # 위도 변화
            lng_change = random.uniform(-0.005, 0.005)  # 경도 변화
            
            new_lat = current_location['lat'] + lat_change
            new_lng = current_location['lng'] + lng_change
            
            # 서울 시내 범위 제한 (대략적 경계)
            new_lat = max(37.4, min(37.7, new_lat))
            new_lng = max(126.8, min(127.2, new_lng))
            
            # 새 위치로 업데이트
            car['location'] = {
                'lat': round(new_lat, 6),
                'lng': round(new_lng, 6)
            }
            self._save_data()
        
        return {
            'car_id': car_id,
            'location': car['location'],
            'engine_state': car['engine_state'],
            'updated_at': datetime.now().isoformat(),
            'moved': car.get('engine_state') == 'on'  # 시동이 켜져 있으면 이동했다고 표시
        }
    
    def horn_and_locate(self, car_id, user_id=None):
        # 경적 울리기 + 위치 조회를 한번에 처리
        car = self.get_car_by_id(car_id)
        if not car:
            return None
        
        # 권한 검증
        if user_id and not self.is_owner(car_id, user_id):
            return None
        
        # 경적 이력 추가
        horn_history = {
            'id': len(self.history) + 1,
            'car_id': car_id,
            'action': 'horn',
            'timestamp': datetime.now().isoformat() + 'Z'
        }
        self.history.append(horn_history)
        self._save_history()
        
        # 위치 정보 조회/업데이트
        location_info = self.get_and_update_location(car_id, user_id)
        
        return {
            'message': f'Horn activated and location updated for car {car_id}',
            'horn_activated': True,
            'location': location_info
        }
    
    def check_tire_pressure(self, car_id, user_id=None):
        car = self.get_car_by_id(car_id)
        if not car:
            return None
        
        # 권한 검증
        if user_id and not self.is_owner(car_id, user_id):
            return None
        
        tire_data = car.get('tire_pressure', {})
        if not tire_data:
            return None
        
        # 실시간 압력 체크 시뮬레이션 (약간의 변동)
        pressures = ['front_left', 'front_right', 'rear_left', 'rear_right']
        current_pressures = {}
        warnings = []
        
        for position in pressures:
            base_pressure = tire_data.get(position, 2.3)
            # 주행 중이면 압력이 약간 변동될 수 있음
            if car.get('engine_state') == 'on':
                variation = random.uniform(-0.1, 0.1)
                current_pressure = round(base_pressure + variation, 1)
            else:
                current_pressure = base_pressure
            
            current_pressures[position] = current_pressure
            
            # 경고 임계값 체크
            if current_pressure < tire_data.get('warning_threshold', 1.8):
                warnings.append({
                    'position': position,
                    'current': current_pressure,
                    'threshold': tire_data.get('warning_threshold', 1.8),
                    'severity': 'critical' if current_pressure < 1.5 else 'warning'
                })
        
        # 체크 시간 업데이트
        tire_data['last_checked'] = datetime.now().isoformat() + 'Z'
        self._save_data()
        
        return {
            'car_id': car_id,
            'tire_pressures': current_pressures,
            'recommended': tire_data.get('recommended', 2.3),
            'unit': tire_data.get('unit', 'bar'),
            'warnings': warnings,
            'last_checked': tire_data['last_checked'],
            'overall_status': 'critical' if any(w['severity'] == 'critical' for w in warnings) else 
                            'warning' if warnings else 'normal'
        }
    
    def simulate_tire_pressure_change(self, car_id, user_id=None):
        # 실제 차량에서는 타이어 압력을 임의로 변경할 수 없지만,
        # 테스트 목적으로 압력 변화를 시뮬레이션하는 함수
        car = self.get_car_by_id(car_id)
        if not car:
            return None
        
        if user_id and not self.is_owner(car_id, user_id):
            return None
        
        tire_data = car.get('tire_pressure', {})
        if not tire_data:
            return None
        
        # 랜덤하게 하나의 타이어 압력을 변경 (시뮬레이션)
        positions = ['front_left', 'front_right', 'rear_left', 'rear_right']
        random_position = random.choice(positions)
        
        # 압력 변화 시뮬레이션 (-0.3 ~ +0.2 bar)
        pressure_change = random.uniform(-0.3, 0.2)
        new_pressure = max(1.0, tire_data[random_position] + pressure_change)
        tire_data[random_position] = round(new_pressure, 1)
        
        # 체크 시간 업데이트
        tire_data['last_checked'] = datetime.now().isoformat() + 'Z'
        self._save_data()
        
        return {
            'message': f'Tire pressure simulation completed for {random_position}',
            'changed_position': random_position,
            'new_pressure': tire_data[random_position],
            'change': round(pressure_change, 1)
        }
    
    def get_driving_statistics(self, car_id, user_id=None):
        # 차량의 주행 통계 조회
        car = self.get_car_by_id(car_id)
        if not car:
            return None
        
        if user_id and not self.is_owner(car_id, user_id):
            return None
        
        car_key = f'car_{car_id}'
        stats = self.statistics.get(car_key, {})
        odometer = car.get('odometer', {})
        
        # 차량의 주행 기록 가져오기
        car_trips = [trip for trip in self.trips if trip['car_id'] == car_id]
        
        return {
            'car_id': car_id,
            'odometer': odometer,
            'statistics': {
                'total_trips': stats.get('total_trips', 0),
                'total_distance_km': stats.get('total_distance_km', 0),
                'total_fuel_consumed': stats.get('total_fuel_consumed', 0),
                'avg_fuel_efficiency': stats.get('avg_fuel_efficiency', 0),
                'total_driving_time_hours': stats.get('total_driving_time_hours', 0),
                'avg_speed_kmh': stats.get('avg_speed_kmh', 0),
                'last_calculated': stats.get('last_calculated', 'N/A')
            },
            'recent_trips_count': len(car_trips)
        }
    
    def get_trip_history(self, car_id, user_id=None, limit=10):
        # 차량의 주행 이력 조회
        car = self.get_car_by_id(car_id)
        if not car:
            return None
        
        if user_id and not self.is_owner(car_id, user_id):
            return None
        
        # 차량의 주행 기록을 최신순으로 정렬하여 반환
        car_trips = [trip for trip in self.trips if trip['car_id'] == car_id]
        car_trips.sort(key=lambda x: x['start_time'], reverse=True)
        
        # 제한된 수만큼 반환
        if limit:
            car_trips = car_trips[:limit]
        
        return {
            'car_id': car_id,
            'trips': car_trips,
            'total_trips': len([trip for trip in self.trips if trip['car_id'] == car_id])
        }
    
    def simulate_new_trip(self, car_id, user_id=None):
        # 새로운 주행 기록을 시뮬레이션하는 함수 (테스트용)
        car = self.get_car_by_id(car_id)
        if not car:
            return None
        
        if user_id and not self.is_owner(car_id, user_id):
            return None
        
        # 현재 위치를 기반으로 새 주행 기록 생성
        current_location = car.get('location', {'lat': 37.5665, 'lng': 126.978})
        
        # 랜덤 목적지 생성 (서울 시내)
        end_lat = current_location['lat'] + random.uniform(-0.05, 0.05)
        end_lng = current_location['lng'] + random.uniform(-0.05, 0.05)
        
        # 랜덤 주행 데이터 생성
        distance = round(random.uniform(2.5, 35.0), 1)
        duration = int(random.uniform(15, 120))  # 15분-2시간
        avg_speed = round(distance / (duration / 60), 1)
        fuel_consumed = round(distance / random.uniform(8, 12), 1)  # 연비 8-12km/L
        
        trip_types = ['commute', 'business', 'personal', 'leisure', 'shopping']
        
        # 새 주행 기록 생성
        new_trip = {
            'id': self.next_trip_id,
            'car_id': car_id,
            'start_time': datetime.now().isoformat() + 'Z',
            'end_time': (datetime.now()).isoformat() + 'Z',
            'start_location': {
                'lat': current_location['lat'],
                'lng': current_location['lng'],
                'address': '서울 시내'
            },
            'end_location': {
                'lat': round(end_lat, 6),
                'lng': round(end_lng, 6), 
                'address': '서울 시내'
            },
            'distance_km': distance,
            'duration_minutes': duration,
            'avg_speed_kmh': avg_speed,
            'max_speed_kmh': min(int(avg_speed * 1.8), 100),
            'fuel_consumed': fuel_consumed,
            'trip_type': random.choice(trip_types)
        }
        
        # 트립 추가
        self.trips.append(new_trip)
        self.next_trip_id += 1
        
        # 차량 위치 업데이트
        car['location'] = {
            'lat': round(end_lat, 6),
            'lng': round(end_lng, 6)
        }
        
        # 오도미터 업데이트
        if 'odometer' not in car:
            car['odometer'] = {
                'total_km': 0,
                'trip_a_km': 0.0,
                'trip_b_km': 0.0,
                'last_updated': datetime.now().isoformat() + 'Z'
            }
        
        car['odometer']['total_km'] += distance
        car['odometer']['trip_a_km'] += distance
        car['odometer']['trip_b_km'] += distance
        car['odometer']['last_updated'] = datetime.now().isoformat() + 'Z'
        
        # 연료 소모 시뮬레이션
        if car.get('fuel', 0) > fuel_consumed:
            car['fuel'] = round(car['fuel'] - fuel_consumed, 1)
        
        # 통계 업데이트
        car_key = f'car_{car_id}'
        if car_key not in self.statistics:
            self.statistics[car_key] = {
                'total_trips': 0,
                'total_distance_km': 0,
                'total_fuel_consumed': 0,
                'avg_fuel_efficiency': 0,
                'total_driving_time_hours': 0,
                'avg_speed_kmh': 0
            }
        
        stats = self.statistics[car_key]
        stats['total_trips'] += 1
        stats['total_distance_km'] += distance
        stats['total_fuel_consumed'] += fuel_consumed
        stats['total_driving_time_hours'] += duration / 60
        stats['avg_fuel_efficiency'] = round(stats['total_distance_km'] / stats['total_fuel_consumed'], 1)
        stats['avg_speed_kmh'] = round(stats['total_distance_km'] / stats['total_driving_time_hours'], 1)
        stats['last_calculated'] = datetime.now().isoformat() + 'Z'
        
        # 데이터 저장
        self._save_data()
        self._save_driving_records()
        
        return {
            'message': 'New trip simulated successfully',
            'trip': new_trip,
            'updated_odometer': car['odometer'],
            'fuel_remaining': car.get('fuel', 0)
        }