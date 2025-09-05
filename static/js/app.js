// app.js
import { Api } from './api.js';
import { State } from './state.js';
import { setActiveTabByHash, updateAuthBadge } from './core/shared.js';
import { attachAuthDelegates } from './core/auth.js';

import { renderMain } from './tabs/main.js';
import { renderMap } from './tabs/map-page.js';
import { renderControl } from './tabs/control.js';
import { renderStore } from './tabs/store.js';
import { renderSettings } from './tabs/settings.js';
const PUBLIC_ROUTES = new Set(['#/main', '#/settings']);

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
    console.log('모든 인증 상태 초기화 완료');
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

    // ⬇ 비로그인 + 보호 라우트면 안내만 렌더하고 종료
    if (!authed && !PUBLIC_ROUTES.has(h)) {
        renderLoginRequired();
        return;
    }

    const fn = routes[location.hash] || renderMain;
    await fn();
}

(async function boot() {
    console.log('앱 시작 - localStorage 확인:', {
        token: localStorage.getItem('cc_token'),
        user: localStorage.getItem('cc_user'),
        user_id: localStorage.getItem('cc_user_id'),
    });

    // 완전 초기화 - 개발/디버깅 시에만 사용
    localStorage.clear(); // 임시로 모든 localStorage 초기화

    // 세션 복원 - 토큰과 사용자 정보가 모두 있고 유효한 경우에만
    const { token, user } = State.get();
    console.log('State에서 가져온 값:', { token: !!token, user: !!user, userHasCar: user?.hasCar });

    if (token && user) {
        try {
            const res = await Api.me(token);
            if (res.ok && res.user) {
                State.setUser(res.user);
                console.log('세션 복원 성공:', res.user);
            } else {
                console.log('API.me 실패 - 상태 초기화');
                clearAllAuthState();
            }
        } catch (e) {
            console.log('API.me 에러 - 상태 초기화', e);
            clearAllAuthState();
        }
    } else {
        console.log('토큰 또는 사용자 정보 없음 - 상태 초기화');
        clearAllAuthState();
    }
    updateAuthBadge();
    attachAuthDelegates();

    if (!location.hash) location.hash = '#/main';
    window.addEventListener('hashchange', navigate);
    await navigate();
})();
