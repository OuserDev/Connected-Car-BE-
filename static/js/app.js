// app.js
import { Api } from "./api.js";
import { State } from "./state.js";
import { setActiveTabByHash, updateAuthBadge } from "./core/shared.js";
import { attachAuthDelegates } from "./core/auth.js";

import { renderMain } from "./tabs/main.js";
import { renderMap } from "./tabs/map-page.js";
import { renderControl } from "./tabs/control.js";
import { renderStore } from "./tabs/store.js";
import { renderSettings } from "./tabs/settings.js";
const PUBLIC_ROUTES = new Set(["#/main", "#/settings"]);

function renderLoginRequired(){
  const root = document.getElementById("view");
  root.innerHTML = `
    <div class="card"><div class="body">
      <div class="kicker">접근 제한</div>
      <div class="cta">
        <div>이 기능은 로그인 후 이용할 수 있습니다.</div>
        <div class="row" style="margin-top:10px">
          <button class="btn brand" id="btnOpenLogin2">로그인</button>
          <button class="btn ghost" type="button" onclick="location.hash='#/main'">메인으로</button>
        </div>
      </div>
    </div></div>`;
}

const routes = {
  "#/main": renderMain,
  "#/map": renderMap,
  "#/control": renderControl,
  "#/store": renderStore,
  "#/settings": renderSettings,
};

async function navigate(){
  setActiveTabByHash();

  const h = location.hash || "#/main";
  const authed = !!State.get().token;

  // ⬇ 비로그인 + 보호 라우트면 안내만 렌더하고 종료
  if (!authed && !PUBLIC_ROUTES.has(h)) {
    renderLoginRequired();
    return;
  }

  const fn = routes[location.hash] || renderMain;
  await fn();
}

(async function boot(){
  // 세션 복원
  const { token } = State.get();
  if(token){
    const res = await Api.me(token);
    if(res.ok) State.setUser(res.user); else State.setToken(null);
  }
  updateAuthBadge();
  attachAuthDelegates();

  if(!location.hash) location.hash = "#/main";
  window.addEventListener("hashchange", navigate);
  await navigate();
})();
