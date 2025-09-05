// api.js - API facade (now using real BE for auth and vehicle control)
import { MockApi } from './mockApi.js';

const BASE_URL = '';

// Action message helper function (from MockAPI)
function getActionMessage(property, value) {
    switch (property) {
        case 'door_state':
            return value === 'locked' ? '🔒 문을 잠갔습니다.' : '🔓 문을 열었습니다.';
        case 'engine_state':
            return value === 'on' ? '▶️ 시동을 켰습니다.' : '⏹️ 시동을 껐습니다.';
        case 'ac_state':
            return value === 'on' ? '❄️ 에어컨을 켰습니다.' : '🛑 에어컨을 껐습니다.';
        case 'target_temp':
            return `🌡️ 목표온도 ${value}℃`;
        case 'horn':
            return '📣 경적을 울렸습니다.';
        case 'hazard_lights':
            return '💡 비상등 점멸.';
        default:
            return '제어가 완료되었습니다.';
    }
}

// Convert new API format to MockAPI action names
function convertToMockApiAction(property, value, originalAction) {
    switch (property) {
        case 'door_state':
            return value === 'locked' ? 'lock' : 'unlock';
        case 'engine_state':
            return value === 'on' ? 'engineOn' : 'engineOff';
        case 'ac_state':
            return value === 'on' ? 'acOn' : 'acOff';
        case 'target_temp':
            return 'setTemp';
        case 'horn':
            return 'horn';
        case 'hazard_lights':
            return 'flash';
        default:
            return originalAction || 'unknown';
    }
}

// Real BE API calls
const RealApi = {
    async login(username, password) {
        try {
            const response = await fetch(`${BASE_URL}/api/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ username, password }),
            });

            const data = await response.json();
            if (data.status === 'success') {
                return {
                    ok: true,
                    token: 'session-based',
                    user: {
                        id: data.user.username,
                        name: data.user.name,
                        hasCar: true,
                        car: { model: 'GRANDEUR', plate: '12가 3456', color: '#79d1ff', imageUrl: '/static/assets/cars/USER1_GRANDEUR.jpg' },
                    },
                };
            } else {
                return { ok: false, message: data.error || '로그인 실패' };
            }
        } catch (error) {
            return { ok: false, message: '서버 연결 실패' };
        }
    },

    async register(username, password, name, email, phone) {
        try {
            const response = await fetch(`${BASE_URL}/api/auth/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ username, password, name, email, phone }),
            });

            const data = await response.json();
            if (data.status === 'success') {
                return { ok: true, user_id: data.user_id };
            } else {
                return { ok: false, message: data.error || '회원가입 실패' };
            }
        } catch (error) {
            return { ok: false, message: '서버 연결 실패' };
        }
    },

    async me() {
        try {
            const response = await fetch(`${BASE_URL}/api/auth/me`, {
                credentials: 'include',
            });

            const data = await response.json();
            if (data.status === 'success') {
                return {
                    ok: true,
                    user: {
                        id: data.user.username,
                        name: data.user.name,
                        hasCar: true,
                        car: { model: 'GRANDEUR', plate: '12가 3456', color: '#79d1ff', imageUrl: '/static/assets/cars/USER1_GRANDEUR.jpg' },
                    },
                };
            } else {
                return { ok: false };
            }
        } catch (error) {
            return { ok: false };
        }
    },

    async vehicleStatus() {
        try {
            console.log('🔍 API.vehicleStatus - Starting...');

            // 1. BE 앱에서 차량 등록 정보 조회 (정적 데이터)
            const carsResponse = await fetch(`${BASE_URL}/api/cars`, {
                credentials: 'include',
            });

            console.log('📋 Cars Response Status:', carsResponse.status);

            if (!carsResponse.ok) {
                throw new Error('차량 목록 조회 실패');
            }

            const carsData = await carsResponse.json();
            console.log('📋 Cars Data:', carsData);

            if (!carsData.success || !carsData.data || carsData.data.length === 0) {
                // 차량이 없는 경우 에러가 아닌 특별한 응답 반환
                console.log('❌ No cars found');
                return {
                    ok: true,
                    noCars: true,
                    message: '등록된 차량이 없습니다',
                    status: null,
                };
            }

            console.log(`🚗 Found ${carsData.data.length} cars`);
            const carInfo = carsData.data[0]; // 첫 번째 차량의 등록 정보
            const vehicleId = carInfo.id;

            // 2. car-api 서버에서 실시간 상태 조회 (동적 데이터)
            // 이 부분은 BE의 vehicle_api_controller를 통해 car-api 서버와 통신
            const statusResponse = await fetch(`${BASE_URL}/api/vehicle/${vehicleId}/status`, {
                credentials: 'include',
            });

            console.log('🔍 Status Response Status:', statusResponse.status);
            const statusData = await statusResponse.json();
            console.log('🔍 Status Data:', statusData);

            if (statusData.success) {
                // 3. 정적 데이터(차량 등록 정보) + 동적 데이터(실시간 상태) 조합
                return {
                    ok: true,
                    status: statusData.data, // car-api에서 온 실시간 상태 (data 필드 사용)
                    carInfo: {
                        // BE에서 온 차량 등록 정보
                        id: carInfo.id,
                        model: carInfo.model_name,
                        licensePlate: carInfo.license_plate,
                        ownerName: carInfo.owner_name,
                        imageUrl: `/static/assets/cars/main_car_images/${carInfo.model_id}.jpg`,
                        controlImageUrl: `/static/assets/cars/control_car_images/${carInfo.model_id}.png`,
                    },
                    allCars: carsData.data.map((car) => ({
                        ...car,
                        imageUrl: `/static/assets/cars/main_car_images/${car.model_id}.jpg`,
                        controlImageUrl: `/static/assets/cars/control_car_images/${car.model_id}.png`,
                    })), // 모든 차량 목록 (여러 차량 대응)
                };
            } else {
                throw new Error(statusData.error || '차량 상태 조회 실패');
            }
        } catch (error) {
            console.error('❌ Vehicle status error:', error);
            console.log('🔄 Falling back to MockAPI...');
            // MockAPI로 폴백
            return MockApi.vehicleStatus();
        }
    },

    // 내 차량 목록 조회 (차량 선택용)
    async myCars() {
        try {
            const response = await fetch(`${BASE_URL}/api/cars`, {
                credentials: 'include',
            });

            if (!response.ok) {
                throw new Error('차량 목록 조회 실패');
            }

            const data = await response.json();
            return {
                ok: data.success,
                cars: data.cars || [],
                message: data.success ? null : data.error,
            };
        } catch (error) {
            return { ok: false, cars: [], message: '서버 연결 실패' };
        }
    },

    async vehicleControl(vehicleId = null, action, data = {}) {
        try {
            // vehicleId가 없으면 첫 번째 차량 사용 (기존 동작 유지)
            let targetVehicleId = vehicleId;

            if (!targetVehicleId) {
                // 1. BE 앱에서 차량 등록 정보 조회 (소유권 및 vehicle_id 확인)
                const carsResponse = await fetch(`${BASE_URL}/api/cars`, {
                    credentials: 'include',
                });

                if (!carsResponse.ok) {
                    throw new Error('차량 목록 조회 실패');
                }

                const carsData = await carsResponse.json();
                if (!carsData.success || !carsData.cars || carsData.cars.length === 0) {
                    throw new Error('등록된 차량이 없습니다');
                }

                targetVehicleId = carsData.cars[0].id;
            }

            // 2. 액션을 car-api 서버 형식으로 변환
            let property, value;

            // 새로운 형식 (property와 value를 직접 전달)
            if (data.value !== undefined) {
                property = action;
                value = data.value;
            } else {
                // 기존 액션 형식 변환
                switch (action) {
                    case 'lock':
                        property = 'door_state';
                        value = 'locked';
                        break;
                    case 'unlock':
                        property = 'door_state';
                        value = 'unlocked';
                        break;
                    case 'engineOn':
                        property = 'engine_state';
                        value = 'on';
                        break;
                    case 'engineOff':
                        property = 'engine_state';
                        value = 'off';
                        break;
                    case 'acOn':
                        property = 'ac_state';
                        value = 'on';
                        break;
                    case 'acOff':
                        property = 'ac_state';
                        value = 'off';
                        break;
                    case 'setTemp':
                        property = 'target_temp';
                        value = data.target || data.value || 22;
                        break;
                    case 'horn':
                        property = 'horn';
                        value = true;
                        break;
                    case 'flash':
                        property = 'hazard_lights';
                        value = true;
                        break;
                    default:
                        throw new Error(`지원하지 않는 액션: ${action}`);
                }
            }

            // 3. BE의 vehicle_api_controller를 통해 car-api 서버로 제어 요청
            // BE가 중간에서 소유권 검증 + car-api 서버와 통신 + 이력 저장
            const controlResponse = await fetch(`${BASE_URL}/api/vehicle/${targetVehicleId}/control`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ property, value }),
            });

            if (!controlResponse.ok) {
                if (controlResponse.status === 503) {
                    throw new Error('car-api 서버에 연결할 수 없습니다');
                } else if (controlResponse.status === 422) {
                    throw new Error('잘못된 제어 요청입니다');
                } else {
                    throw new Error(`서버 오류 (${controlResponse.status})`);
                }
            }

            const controlData = await controlResponse.json();
            if (controlData.success) {
                const actionMessage = getActionMessage(property, value);
                return {
                    ok: true,
                    message: controlData.message || actionMessage,
                    status: controlData.data || controlData.status, // data 필드 우선 사용
                };
            } else {
                throw new Error(controlData.error || '차량 제어 실패');
            }
        } catch (error) {
            console.error('Vehicle control error:', error);

            // 구체적인 오류 메시지와 함께 MockAPI로 폴백
            const fallbackMessage = error.message.includes('서버') || error.message.includes('연결') ? '서버 연결 실패 - 시뮬레이션 모드로 동작합니다' : '제어 실패 - 시뮬레이션 모드로 동작합니다';

            console.log('Falling back to MockAPI:', fallbackMessage);

            // MockAPI는 기존 action명을 사용하므로 변환 필요
            const mockAction = convertToMockApiAction(property, value, action);
            const result = await MockApi.vehicleControl(mockAction, data);
            return { ...result, message: result.message || fallbackMessage };
        }
    },

    // 🖼️ 차량 사진 업로드 API
    async uploadCarPhotos(imageDataArray) {
        try {
            const response = await fetch(`${BASE_URL}/api/car-photos/upload`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ images: imageDataArray }),
            });

            const data = await response.json();
            if (data.success) {
                return {
                    ok: true,
                    message: data.message,
                    photos: data.photos,
                    uploadedCount: data.uploaded_count,
                };
            } else {
                return { ok: false, message: data.error || '업로드 실패' };
            }
        } catch (error) {
            console.error('Photo upload error:', error);
            return { ok: false, message: '서버 연결 실패' };
        }
    },

    async getCarPhotos() {
        try {
            const response = await fetch(`${BASE_URL}/api/car-photos`, {
                credentials: 'include',
            });

            const data = await response.json();
            if (data.success) {
                return {
                    ok: true,
                    photos: data.photos,
                    mainPhotoId: data.main_photo_id,
                    totalCount: data.total_count,
                };
            } else {
                return { ok: false, message: data.error || '사진 조회 실패' };
            }
        } catch (error) {
            console.error('Photo fetch error:', error);
            return { ok: false, message: '서버 연결 실패' };
        }
    },

    async setMainCarPhoto(photoId) {
        try {
            const response = await fetch(`${BASE_URL}/api/car-photos/${photoId}/set-main`, {
                method: 'POST',
                credentials: 'include',
            });

            const data = await response.json();
            if (data.success) {
                return {
                    ok: true,
                    message: data.message,
                    mainPhotoId: data.main_photo_id,
                };
            } else {
                return { ok: false, message: data.error || '메인 사진 설정 실패' };
            }
        } catch (error) {
            console.error('Set main photo error:', error);
            return { ok: false, message: '서버 연결 실패' };
        }
    },

    async deleteCarPhoto(photoId) {
        try {
            const response = await fetch(`${BASE_URL}/api/car-photos/${photoId}`, {
                method: 'DELETE',
                credentials: 'include',
            });

            const data = await response.json();
            if (data.success) {
                return {
                    ok: true,
                    message: data.message,
                    photos: data.photos,
                    mainPhotoId: data.main_photo_id,
                };
            } else {
                return { ok: false, message: data.error || '사진 삭제 실패' };
            }
        } catch (error) {
            console.error('Delete photo error:', error);
            return { ok: false, message: '서버 연결 실패' };
        }
    },

    async clearAllCarPhotos() {
        try {
            const response = await fetch(`${BASE_URL}/api/car-photos/clear`, {
                method: 'DELETE',
                credentials: 'include',
            });

            const data = await response.json();
            if (data.success) {
                return {
                    ok: true,
                    message: data.message,
                };
            } else {
                return { ok: false, message: data.error || '전체 삭제 실패' };
            }
        } catch (error) {
            console.error('Clear all photos error:', error);
            return { ok: false, message: '서버 연결 실패' };
        }
    },
};

export const Api = {
    // Use real BE for authentication and vehicle control
    login: RealApi.login,
    register: RealApi.register,
    me: RealApi.me,
    vehicleStatus: RealApi.vehicleStatus,
    vehicleControl: RealApi.vehicleControl,
    myCars: RealApi.myCars,

    // 🖼️ Car photos - Real BE API
    uploadCarPhotos: RealApi.uploadCarPhotos,
    getCarPhotos: RealApi.getCarPhotos,
    setMainCarPhoto: RealApi.setMainCarPhoto,
    deleteCarPhoto: RealApi.deleteCarPhoto,
    clearAllCarPhotos: RealApi.clearAllCarPhotos,

    // Keep mock for other features for now
    setHasCar: MockApi.setHasCar,
    recommendedPlaces: MockApi.recommendedPlaces,
    controlLogs: MockApi.controlLogs, // 제어 로그 조회
    controlLogsClear: MockApi.controlLogsClear, // 제어 로그 초기화
    storeNew: MockApi.storeNew,
    storeUsedList: MockApi.storeUsedList,
    storeUsedCreate: MockApi.storeUsedCreate,
    cardsList: MockApi.cardsList,
    cardSelect: MockApi.cardSelect,
    cardsAddTest: MockApi.cardsAddTest,
    purchase: MockApi.purchase,
};
