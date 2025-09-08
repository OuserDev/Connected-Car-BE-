// app.js
import { Api } from './api.js';
import { State } from './state.js';
import { setActiveTabByHash, updateAuthBadge, updateHeaderVehicleInfo, updateTabsDisabledState } from './core/shared.js';
import { attachAuthDelegates } from './core/auth.js';
import { UI } from './ui/components.js';

import { renderMain } from './tabs/main.js';
import { renderMap } from './tabs/map-page.js';
import { renderControl } from './tabs/control.js';
import { renderStore } from './tabs/store.js';
import { renderSettings } from './tabs/settings.js';
const PUBLIC_ROUTES = new Set(['#/main', '#/settings']);
const VEHICLE_REQUIRED_ROUTES = new Set(['#/map', '#/control', '#/store']);

function clearAllAuthState() {
    State.setToken(null);
    State.setUser(null);
    localStorage.removeItem('cc_token');
    localStorage.removeItem('cc_user');
    localStorage.removeItem('cc_user_id');
    // 모든 사용자별 데이터도 제거
    Object.keys(localStorage).forEach((key) => {
        if (key.startsWith('cc_user_')) {
            localStorage.removeItem(key);
        }
    });
}

function renderLoginRequired() {
    const root = document.getElementById('view');
    root.innerHTML = `
    <div class="card"><div class="body">
      <div class="kicker">접근 제한</div>
      <div class="cta" style="text-align: center; padding: 24px 16px;">
        <div style="margin-bottom: 20px;">이 기능은 로그인 후 이용할 수 있습니다.</div>
        <div class="row" style="justify-content: center; gap: 12px;">
          <button class="btn brand" id="btnOpenLogin2">로그인</button>
          <button class="btn ghost" type="button" onclick="location.hash='#/main'">메인으로</button>
        </div>
      </div>
    </div></div>`;
}

function renderVehicleRequired() {
    const root = document.getElementById('view');
    root.innerHTML = `
    <div class="card"><div class="body">
      <div class="kicker">차량 등록 필요</div>
      <div class="cta" style="text-align: center; padding: 24px 16px;">
        <div style="margin-bottom: 20px;">이 기능을 이용하려면 차량을 먼저 등록해야 합니다.</div>
        <div class="row" style="justify-content: center; gap: 12px;">
          <button class="btn brand" type="button" onclick="location.hash='#/settings'">차량 등록하기</button>
          <button class="btn ghost" type="button" onclick="location.hash='#/main'">메인으로</button>
        </div>
      </div>
    </div></div>`;
}

const routes = {
    '#/main': renderMain,
    '#/map': renderMap,
    '#/control': renderControl,
    '#/store': renderStore,
    '#/settings': renderSettings,
};

export async function navigate() {
    setActiveTabByHash();

    const h = location.hash || '#/main';
    const authed = !!State.get().token;
    const user = State.get().user;

    // 제어 페이지를 벗어날 때 폴링 정리
    if (h !== '#/control' && window.cleanupControlPolling) {
        window.cleanupControlPolling();
    }

    // ⬇ 비로그인 + 보호 라우트면 안내만 렌더하고 종료
    if (!authed && !PUBLIC_ROUTES.has(h)) {
        renderLoginRequired();
        return;
    }

    // ⬇ 로그인 상태이지만 차량 등록이 필요한 라우트인 경우
    if (authed && VEHICLE_REQUIRED_ROUTES.has(h)) {
        // 실시간으로 차량 등록 상태 체크
        try {
            const response = await fetch('/api/cars', { credentials: 'include' });
            let hasActualCars = false;
            if (response.ok) {
                const data = await response.json();
                hasActualCars = data.success && data.data && data.data.length > 0;
            }

            // 실제 차량이 등록되지 않았으면 차단
            if (!hasActualCars) {
                // 토스트 메시지 표시하고 메인으로 리다이렉트
                UI.toast('차량을 먼저 등록해야 합니다');
                location.hash = '#/main';
                return;
            }
        } catch (error) {
            // 오류 발생 시에도 토스트 메시지 표시하고 메인으로 리다이렉트
            UI.toast('차량을 먼저 등록해야 합니다');
            location.hash = '#/main';
            return;
        }
    }

    const fn = routes[location.hash] || renderMain;
    await fn();
}

(async function boot() {
    // localStorage 상태 확인 (디버깅용)

    // 완전 초기화 - 개발/디버깅 시에만 사용 (현재 비활성화)
    // localStorage.clear(); // 임시로 모든 localStorage 초기화

    // 세션 복원 - 토큰과 사용자 정보가 모두 있고 유효한 경우에만
    const { token, user } = State.get();

    if (token && user) {
        try {
            const res = await Api.me(token);
            if (res.ok && res.user) {
                State.setUser(res.user);
            } else {
                clearAllAuthState();
            }
        } catch (e) {
            clearAllAuthState();
        }
    } else {
        clearAllAuthState();
    }
    await updateAuthBadge();
    attachAuthDelegates();

    // 전역 차량 선택 이벤트 리스너
    window.addEventListener('carSelected', async (event) => {
        const selectedCar = event.detail;
        State.setSelectedCarId(selectedCar.id);
        UI.toast(`${selectedCar.model_name} 차량이 선택되었습니다`);
        // 헤더 차량 정보 업데이트
        await updateHeaderVehicleInfo();
        // 탭 상태 업데이트
        await updateTabsDisabledState();
        // 현재 페이지가 메인이면 다시 렌더링
        if (location.hash === '#/main') {
            renderMain();
        }
    });

    if (!location.hash) location.hash = '#/main';
    window.addEventListener('hashchange', navigate);
    await navigate();
})();
