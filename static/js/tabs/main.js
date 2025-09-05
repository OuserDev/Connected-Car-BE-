// tabs/main.js
import { Api } from '../api.js';
import { State } from '../state.js';
import { UI } from '../ui/components.js';
import { getRoot, waitForNaver } from '../core/shared.js';
import { mount as mountMap, addVehicleMarker, moveToLocation } from '../ui/map.js';

// 중복 렌더링 방지
let _isRendering = false;

export async function renderMain() {
    if (_isRendering) {
        console.log('⚠️ renderMain already in progress, skipping...');
        return;
    }
    _isRendering = true;
    const root = getRoot();
    // 완전히 초기화 - 모든 자식 요소 제거
    while (root.firstChild) {
        root.removeChild(root.firstChild);
    }

    // 먼저 인증 상태 확인
    const { user, token } = State.get();
    console.log('👤 Main.js - User State:', { token: !!token, user: !!user, userHasCar: user?.hasCar });

    // 로그인되어 있고 차량이 있는 경우에만 API 호출
    if (user && token && user.hasCar) {
        const [{ ok: okP, items = [] } = {}, vehicleResponse = {}] = await Promise.all([Api.recommendedPlaces(), Api.vehicleStatus()]);

        // 디버깅용 로그
        console.log('🚗 Main.js - Vehicle Response:', vehicleResponse);
        console.log('🚗 Vehicle Status:', vehicleResponse.status);
        console.log('🚗 Car Info:', vehicleResponse.carInfo);

        renderAuthenticatedUser(root, user, vehicleResponse, okP, items);
    } else {
        // 로그인하지 않았거나 차량이 없으면 로그인 유도 화면만 표시
        console.log('🚫 로그인하지 않았거나 차량 정보 없음 - 로그인 유도 화면 표시');
        renderUnauthenticatedUser(root);
    }

    // 렌더링 완료
    _isRendering = false;
}

function renderAuthenticatedUser(root, user, vehicleResponse, okP, items) {
    // 사용자 상태에 따른 UI 분기
    if (vehicleResponse.noCars) {
        // 로그인했지만 차량이 없는 경우
        root.appendChild(UI.noCarCallout());
    } else if (vehicleResponse.ok && vehicleResponse.allCars && vehicleResponse.allCars.length > 1) {
        // 여러 차량을 소유한 경우 - 히어로 먼저, 차량 선택기는 아래에
        const selectedCarId = State.selectedCarId || vehicleResponse.carInfo?.id;
        const selectedCar = vehicleResponse.allCars.find((car) => car.id === selectedCarId) || vehicleResponse.carInfo;
        root.appendChild(UI.carHero(user, vehicleResponse.status, selectedCar));
        root.appendChild(UI.carSelector(vehicleResponse.allCars, selectedCarId));
    } else if (vehicleResponse.ok && vehicleResponse.status) {
        // 정상적으로 차량 1대를 소유한 경우
        root.appendChild(UI.carHero(user, vehicleResponse.status, vehicleResponse.carInfo));
    } else {
        // 기타 오류 상황 (MockAPI 폴백 등)
        root.appendChild(UI.carHero(user, null));
    }

    // 지도 렌더링 먼저 (차량 위치 포함)
    let currentCarInfo = null;
    if (vehicleResponse.ok && vehicleResponse.allCars && vehicleResponse.allCars.length > 1) {
        const selectedCarId = State.selectedCarId || vehicleResponse.carInfo?.id;
        currentCarInfo = vehicleResponse.allCars.find((car) => car.id === selectedCarId) || vehicleResponse.carInfo;
    } else if (vehicleResponse.carInfo) {
        currentCarInfo = vehicleResponse.carInfo;
    }

    renderMapSection(root, items, vehicleResponse.status, currentCarInfo);

    // 추천 리스트는 지도 아래에 렌더링
    renderRecommendedPlaces(root, okP, items);
}

function renderUnauthenticatedUser(root) {
    // 로그인 유도 화면 표시
    root.appendChild(UI.loginCallout());

    // 로그인하지 않은 경우 추천 장소 섹션을 표시하지 않음
    // renderRecommendedPlaces(root, false, []);
}

function renderRecommendedPlaces(root, okP, items) {
    // 추천 리스트
    const listCard = UI.el('div', 'card');
    const listBody = UI.el('div', 'body');
    listBody.innerHTML = `<div class="kicker">가볼만한 곳</div>`;
    const list = UI.el('div', 'list');
    listBody.appendChild(list);
    if (!okP || !items.length) {
        const empty = UI.el('div', 'muted', '추천 데이터를 불러오는 중이거나 항목이 없습니다.');
        empty.style.padding = '6px 2px';
        list.appendChild(empty);
    } else {
        items.forEach((p, index) => {
            const row = UI.el('div', 'place');
            row.innerHTML = `
        <div class="pin">📍</div>
        <div style="flex:1">
          <div class="title">${p.name}</div>
          <div class="meta">${p.tag} · ${p.dist}</div>
        </div>
        <button class="btn ghost place-detail-btn" data-index="${index}">자세히</button>`;
            list.appendChild(row);
        });

        // "자세히" 버튼 이벤트 리스너 추가
        list.addEventListener('click', (e) => {
            if (e.target.classList.contains('place-detail-btn')) {
                const index = parseInt(e.target.getAttribute('data-index'));
                const place = items[index];
                if (place && typeof place.lat === 'number' && typeof place.lng === 'number') {
                    console.log('🗺️ Moving to place:', place.name, place.lat, place.lng);
                    moveToLocation(place.lat, place.lng, place.name);

                    // 지도로 스크롤 (지도가 위쪽에 있으므로 상단으로 스크롤)
                    setTimeout(() => {
                        const mapElement = document.querySelector('.map');
                        if (mapElement) {
                            mapElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
                        }
                    }, 100);
                }
            }
        });
    }
    listCard.appendChild(listBody);
    root.appendChild(listCard);
}

function renderMapSection(root, items, vehicleStatus = null, carInfo = null) {
    // 지도 (제목 없이)
    const mapCard = UI.el('div', 'card');
    const mapBody = UI.el('div', 'body');
    mapBody.innerHTML = `<div class="map"><div id="map-main"></div></div>`;
    mapCard.appendChild(mapBody);
    root.appendChild(mapCard);

    // 비동기 지도 초기화
    setTimeout(async () => {
        try {
            await waitForNaver();
            mountMap('#map-main', { places: items });

            // 차량 위치 정보가 있으면 차량 마커 추가
            console.log('🗺️ Checking vehicle location:', { vehicleStatus, carInfo });
            if (vehicleStatus?.location && carInfo) {
                const { lat, lng } = vehicleStatus.location;
                console.log('🗺️ Adding vehicle marker:', { lat, lng, carInfo });

                addVehicleMarker(lat, lng, {
                    model: carInfo.model_name || carInfo.model,
                    plate: carInfo.license_plate || carInfo.licensePlate,
                });
            } else {
                console.log('❌ No vehicle location data:', {
                    hasLocation: !!vehicleStatus?.location,
                    hasCarInfo: !!carInfo,
                    vehicleStatus,
                    carInfo,
                });
            }
        } catch (e) {
            const m = document.getElementById('map-main');
            if (m) m.innerHTML = `<div style="padding:14px" class="muted">지도를 초기화하지 못했습니다.<br>${String(e.message || e)}</div>`;
        }
    }, 100);

    // 이벤트 리스너 추가
    setupMainEventListeners();
}

function setupMainEventListeners() {
    // 차량 등록 버튼
    const btnRegisterCar = document.getElementById('btnRegisterCar');
    const dlgCarRegister = document.getElementById('dlgCarRegister');
    const dlgCarConfirm = document.getElementById('dlgCarConfirm');
    const carRegisterForm = document.getElementById('carRegisterForm');
    
    if (btnRegisterCar && dlgCarRegister) {
        btnRegisterCar.addEventListener('click', () => {
            dlgCarRegister.showModal();
        });
    }

    // 차량 등록 모달 닫기
    const btnCloseCarRegister = document.getElementById('btnCloseCarRegister');
    const btnCancelCarRegister = document.getElementById('btnCancelCarRegister');
    
    if (btnCloseCarRegister) {
        btnCloseCarRegister.addEventListener('click', () => {
            dlgCarRegister.close();
        });
    }
    
    if (btnCancelCarRegister) {
        btnCancelCarRegister.addEventListener('click', () => {
            dlgCarRegister.close();
        });
    }

    // 차량 등록 폼 제출
    if (carRegisterForm) {
        carRegisterForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const licensePlate = document.getElementById('licensePlate').value.trim();
            const vinCode = document.getElementById('vinCode').value.trim();
            
            if (!licensePlate || !vinCode) {
                UI.toast('라이선스 플레이트와 VIN 코드를 모두 입력해주세요');
                return;
            }

            try {
                const btnSubmit = document.getElementById('btnSubmitCarRegister');
                btnSubmit.disabled = true;
                btnSubmit.textContent = '확인 중...';
                
                // 차량 정보 확인 API 호출
                const response = await Api.verifyCarInfo({ licensePlate, vinCode });
                
                if (response.ok && response.car) {
                    // 차량 정보가 일치하면 확인 모달 표시
                    showCarConfirmModal(response.car, licensePlate, vinCode);
                    dlgCarRegister.close();
                } else {
                    UI.toast(response.message || '입력한 차량 정보와 일치하는 차량을 찾을 수 없습니다');
                }
            } catch (error) {
                console.error('Car verification error:', error);
                UI.toast('서버 연결 실패');
            } finally {
                const btnSubmit = document.getElementById('btnSubmitCarRegister');
                if (btnSubmit) {
                    btnSubmit.disabled = false;
                    btnSubmit.textContent = '확인';
                }
            }
        });
    }

    // 차량 확인 모달 관련 이벤트
    const btnCloseCarConfirm = document.getElementById('btnCloseCarConfirm');
    const btnCancelCarConfirm = document.getElementById('btnCancelCarConfirm');
    
    if (btnCloseCarConfirm) {
        btnCloseCarConfirm.addEventListener('click', () => {
            dlgCarConfirm.close();
        });
    }
    
    if (btnCancelCarConfirm) {
        btnCancelCarConfirm.addEventListener('click', () => {
            dlgCarConfirm.close();
        });
    }
}

// 차량 확인 모달 표시 함수
function showCarConfirmModal(carInfo, licensePlate, vinCode) {
    const dlgCarConfirm = document.getElementById('dlgCarConfirm');
    const carConfirmContent = document.getElementById('carConfirmContent');
    
    if (!dlgCarConfirm || !carConfirmContent) return;
    
    // 차량 정보 표시
    carConfirmContent.innerHTML = `
        <div style="text-align: center; margin-bottom: 20px;">
            <div style="font-size: 48px; margin-bottom: 12px;">🚗</div>
            <h3 style="margin-bottom: 8px;">${carInfo.model_name || '알 수 없음'}</h3>
            <p style="color: #6b7280; margin-bottom: 16px;">이 차량이 맞습니까?</p>
        </div>
        <div class="form-row">
            <label>차량 모델</label>
            <div style="padding: 8px; background: #f3f4f6; border-radius: 4px;">${carInfo.model_name || '알 수 없음'}</div>
        </div>
        <div class="form-row">
            <label>제조사</label>
            <div style="padding: 8px; background: #f3f4f6; border-radius: 4px;">${carInfo.manufacturer || '알 수 없음'}</div>
        </div>
        <div class="form-row">
            <label>연식</label>
            <div style="padding: 8px; background: #f3f4f6; border-radius: 4px;">${carInfo.year || '알 수 없음'}</div>
        </div>
        <div class="form-row">
            <label>연료 타입</label>
            <div style="padding: 8px; background: #f3f4f6; border-radius: 4px;">${carInfo.fuel_type || '알 수 없음'}</div>
        </div>
    `;
    
    // 확인 버튼에 이벤트 리스너 추가
    const btnConfirmCarRegister = document.getElementById('btnConfirmCarRegister');
    if (btnConfirmCarRegister) {
        // 기존 이벤트 리스너 제거
        const newBtn = btnConfirmCarRegister.cloneNode(true);
        btnConfirmCarRegister.parentNode.replaceChild(newBtn, btnConfirmCarRegister);
        
        // 새 이벤트 리스너 추가
        newBtn.addEventListener('click', async () => {
            await registerCar(carInfo.id, licensePlate, vinCode);
        });
    }
    
    dlgCarConfirm.showModal();
}

// 최종 차량 등록 함수
async function registerCar(carId, licensePlate, vinCode) {
    try {
        const btnConfirm = document.getElementById('btnConfirmCarRegister');
        if (btnConfirm) {
            btnConfirm.disabled = true;
            btnConfirm.textContent = '등록 중...';
        }
        
        const response = await Api.registerCar({ carId, licensePlate, vinCode });
        
        if (response.ok) {
            UI.toast('차량이 성공적으로 등록되었습니다!');
            document.getElementById('dlgCarConfirm').close();
            
            // 사용자 상태 업데이트
            const { user } = State.get();
            if (user) {
                user.hasCar = true;
                State.setUser(user);
            }
            
            // 메인 화면 다시 렌더링
            setTimeout(() => renderMain(), 1000);
        } else {
            UI.toast(response.message || '차량 등록에 실패했습니다');
        }
    } catch (error) {
        console.error('Car registration error:', error);
        UI.toast('서버 연결 실패');
    } finally {
        const btnConfirm = document.getElementById('btnConfirmCarRegister');
        if (btnConfirm) {
            btnConfirm.disabled = false;
            btnConfirm.textContent = '네, 맞습니다';
        }
    }

    // 차량 선택 이벤트
    window.addEventListener('carSelected', (event) => {
        const selectedCar = event.detail;
        UI.toast(`${selectedCar.model_name} 차량이 선택되었습니다`);
        // 실제로는 선택된 차량으로 상태 업데이트
        State.selectedCarId = selectedCar.id;
        renderMain(); // 다시 렌더링
    });
}
