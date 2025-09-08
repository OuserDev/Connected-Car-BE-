// core/shared.js
import { State } from '../state.js';

export function getRoot() {
    return document.getElementById('view');
}
export function getScrim() {
    return document.getElementById('dlgScrim');
}

/* NAVER Maps 로드 대기 */
export function waitForNaver(maxMs = 4000) {
    return new Promise((resolve, reject) => {
        const t0 = Date.now();
        (function loop() {
            if (window.naver && naver.maps) return resolve();
            if (Date.now() - t0 > maxMs) return reject(new Error('NAVER Maps 로드를 확인하지 못했습니다.'));
            requestAnimationFrame(loop);
        })();
    });
}

/* 하단 탭 활성화 표시 */
export function setActiveTabByHash() {
    const map = { '#/main': '0', '#/map': '1', '#/control': '2', '#/store': '3', '#/settings': '4' };
    const idx = map[location.hash] ?? '0';
    document.querySelectorAll('.tab').forEach((t) => {
        const active = t.dataset.index === idx;
        t.dataset.active = active ? 'true' : 'false';
        t.setAttribute('aria-selected', active ? 'true' : 'false');
    });
}

/* 실제 차량 등록 상태 체크 */
async function checkActualCarRegistration() {
    try {
        const response = await fetch('/api/cars', { credentials: 'include' });
        if (response.ok) {
            const data = await response.json();
            return data.success && data.data && data.data.length > 0;
        }
        return false;
    } catch (error) {
        return false;
    }
}

/* 차량 등록 상태에 따른 탭 비활성화 표시 */
export async function updateTabsDisabledState() {
    const { token, user } = State.get();
    const vehicleRequiredTabs = ['#/map', '#/control', '#/store'];

    // 로그인 상태일 때만 실시간 차량 상태 체크
    let hasActualCars = false;
    if (token) {
        hasActualCars = await checkActualCarRegistration();
    }

    document.querySelectorAll('.tab').forEach((tab) => {
        const href = tab.getAttribute('href');

        // 차량 등록이 필요한 탭인지 확인
        if (vehicleRequiredTabs.includes(href)) {
            // 로그인하지 않았거나 실제 차량이 없으면 비활성화 스타일 적용
            if (!token || !hasActualCars) {
                tab.style.opacity = '0.5';
                tab.style.pointerEvents = 'none'; // 아예 클릭 불가능하게
                tab.setAttribute('data-disabled', 'true');
                tab.style.cursor = 'not-allowed'; // 커서를 금지 표시로
                tab.title = '차량을 먼저 등록해야 합니다'; // 툴팁 추가
            } else {
                tab.style.opacity = '1';
                tab.style.pointerEvents = 'auto';
                tab.setAttribute('data-disabled', 'false');
                tab.style.cursor = 'pointer'; // 정상 커서
                tab.title = ''; // 툴팁 제거
            }
        } else {
            // 차량이 필요하지 않은 탭은 항상 활성화
            tab.style.opacity = '1';
            tab.style.pointerEvents = 'auto';
            tab.setAttribute('data-disabled', 'false');
        }
    });
}

/* 헤더 배지 갱신 */
export async function updateAuthBadge() {
    const { token, user } = State.get();
    const badge = document.getElementById('badgeAuth');
    const logoutBtn = document.getElementById('btnLogout');

    if (badge) {
        if (token) {
            badge.textContent = `환영합니다. ${user?.name || '사용자'}님`;
            badge.title = '클릭하여 프로필 수정';
            logoutBtn.style.display = 'block';
        } else {
            badge.textContent = '로그인';
            badge.title = '클릭하여 로그인';
            logoutBtn.style.display = 'none';
        }
    }

    // 헤더 차량 정보도 함께 업데이트
    await updateHeaderVehicleInfo();

    // 탭 비활성화 상태도 함께 업데이트
    await updateTabsDisabledState();
}

/* 헤더 중앙 차량 정보 업데이트 */
export async function updateHeaderVehicleInfo() {
    const { token, selectedCarId } = State.get();
    const headerVehicleInfo = document.getElementById('headerVehicleInfo');
    const headerVehicleModel = document.getElementById('headerVehicleModel');
    const headerVehiclePlate = document.getElementById('headerVehiclePlate');

    if (!headerVehicleInfo || !headerVehicleModel || !headerVehiclePlate) return;

    if (!token) {
        // 로그인하지 않은 경우 차량 정보 숨기기
        headerVehicleInfo.style.display = 'none';
        return;
    }

    // selectedCarId가 없어도 차량이 있으면 자동 선택하므로 조건 제거

    try {
        // 사용자의 차량 목록 가져오기
        const response = await fetch('/api/cars', { credentials: 'include' });
        if (response.ok) {
            const data = await response.json();
            if (data.success && data.data && data.data.length > 0) {
                let selectedCar = null;

                // 선택된 차량이 있으면 해당 차량 찾기
                if (selectedCarId) {
                    selectedCar = data.data.find((car) => car.id === selectedCarId);
                }

                // 선택된 차량이 없으면 첫 번째 차량을 자동 선택
                if (!selectedCar) {
                    selectedCar = data.data[0];
                    // 자동 선택된 차량을 State에도 저장
                    State.setSelectedCarId(selectedCar.id);
                }

                // 차량 정보 표시
                if (selectedCar) {
                    headerVehicleModel.textContent = selectedCar.model_name || selectedCar.model || '차량';
                    headerVehiclePlate.textContent = selectedCar.license_plate || selectedCar.licensePlate || '번호판 미등록';
                    headerVehicleInfo.style.display = 'block';
                } else {
                    headerVehicleInfo.style.display = 'none';
                }
            } else {
                headerVehicleInfo.style.display = 'none';
            }
        } else {
            headerVehicleInfo.style.display = 'none';
        }
    } catch (error) {
        headerVehicleInfo.style.display = 'none';
    }
}

/* 사용자 상태 주기적 확인 */
let statusCheckInterval = null;

export function startUserStatusCheck() {
    // 기존 인터벌 정리
    if (statusCheckInterval) {
        clearInterval(statusCheckInterval);
    }
    
    // 5분마다 사용자 상태 확인
    statusCheckInterval = setInterval(async () => {
        const { token } = State.get();
        if (!token) return; // 로그인되지 않은 상태면 확인 안함
        
        try {
            const response = await fetch('/api/auth/me', { credentials: 'include' });
            if (response.status === 403) {
                // 계정 정지됨 - 강제 로그아웃
                const data = await response.json();
                stopUserStatusCheck(); // 상태 확인 정지
                State.clearAll();
                await updateAuthBadge();
                
                // 로그인 페이지로 이동하고 경고 메시지 표시
                location.hash = '#/main';
                setTimeout(() => {
                    alert('⚠️ ' + (data.error || '계정이 정지되었습니다. 관리자에게 문의하세요.'));
                }, 100);
                
                // 인터벌 정지
                clearInterval(statusCheckInterval);
                statusCheckInterval = null;
            }
        } catch (error) {
            // 네트워크 오류는 무시
        }
    }, 5 * 60 * 1000); // 5분
}

export function stopUserStatusCheck() {
    if (statusCheckInterval) {
        clearInterval(statusCheckInterval);
        statusCheckInterval = null;
    }
}
