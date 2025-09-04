// core/auth.js
import { Api } from "../api.js";
import { State } from "../state.js";
import { updateAuthBadge, getScrim } from "./shared.js";
import { UI } from "../ui/components.js";

export function openLoginDialog(){
  const scrim = getScrim();
  scrim?.classList.add("show");
  scrim?.setAttribute("aria-hidden","false");
  document.body.classList.add("modal-open");
  setTimeout(()=>document.getElementById("id")?.focus(), 30);
}
export function closeLoginDialog(){
  const scrim = getScrim();
  scrim?.classList.remove("show");
  scrim?.setAttribute("aria-hidden","true");
  document.body.classList.remove("modal-open");
  const id = document.getElementById("id"); const pw = document.getElementById("pw");
  if(id) id.value = ""; if(pw) pw.value = "";
}
export async function doLogin(){
  const id = document.getElementById("id")?.value?.trim();
  const pw = document.getElementById("pw")?.value;
  const res = await Api.login(id, pw);
  if(!res.ok){ UI.toast(res.message || "로그인 실패"); return; }
  State.setToken(res.token); State.setUser(res.user);
  UI.toast("로그인 되었습니다."); updateAuthBadge(); closeLoginDialog();
  location.hash = "#/main"
  await navigate();
}

/* 문서 위임: 로그인 버튼/취소/실행 */
export function attachAuthDelegates(){
  document.addEventListener("click", (e)=>{
    const t = e.target;
    if(!(t instanceof Element)) return;
    if(t.id === "btnOpenLogin" || t.id === "btnOpenLogin2"){ e.preventDefault(); openLoginDialog(); }
    if(t.id === "btnLoginCancel"){ e.preventDefault(); closeLoginDialog(); }
    if(t.id === "btnLoginDo"){ e.preventDefault(); doLogin(); }
  });
}
