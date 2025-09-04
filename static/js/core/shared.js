// core/shared.js
import { State } from "../state.js";

export function getRoot(){
  return document.getElementById("view");
}
export function getScrim(){
  return document.getElementById("dlgScrim");
}

/* NAVER Maps 로드 대기 */
export function waitForNaver(maxMs = 4000){
  return new Promise((resolve, reject)=>{
    const t0 = Date.now();
    (function loop(){
      if (window.naver && naver.maps) return resolve();
      if (Date.now() - t0 > maxMs) return reject(new Error("NAVER Maps 로드를 확인하지 못했습니다."));
      requestAnimationFrame(loop);
    })();
  });
}

/* 하단 탭 활성화 표시 */
export function setActiveTabByHash(){
  const map = { "#/main":"0", "#/map":"1", "#/control":"2", "#/store":"3", "#/settings":"4" };
  const idx = map[location.hash] ?? "0";
  document.querySelectorAll(".tab").forEach(t=>{
    const active = t.dataset.index === idx;
    t.dataset.active = active ? "true" : "false";
    t.setAttribute("aria-selected", active ? "true" : "false");
  });
}

/* 헤더 배지 갱신 */
export function updateAuthBadge(){
  const { token, user } = State.get();
  const badge = document.getElementById("badgeAuth");
  if (badge) {
    badge.textContent = token ? `환영합니다. ${user?.name || "사용자"}님` : "로그인";
    badge.style.cursor = "pointer";
    badge.title = token ? "클릭하여 로그아웃" : "클릭하여 로그인";
  }
}
