// core/auth.js
import { Api } from "../api.js";
import { State } from "../state.js";
import { updateAuthBadge, getScrim } from "./shared.js";
import { UI } from "../ui/components.js";
import { navigate } from "../app.js";

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

export function openSignupDialog(){
  const scrim = document.getElementById("dlgSignupScrim");
  scrim?.classList.add("show");
  scrim?.setAttribute("aria-hidden","false");
  document.body.classList.add("modal-open");
  setTimeout(()=>document.getElementById("signupUsername")?.focus(), 30);
}

export function closeSignupDialog(){
  const scrim = document.getElementById("dlgSignupScrim");
  scrim?.classList.remove("show");
  scrim?.setAttribute("aria-hidden","true");
  document.body.classList.remove("modal-open");
  const fields = ["signupUsername", "signupPassword", "signupName", "signupEmail", "signupPhone"];
  fields.forEach(id => {
    const field = document.getElementById(id);
    if(field) field.value = "";
  });
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

export async function doSignup(){
  const username = document.getElementById("signupUsername")?.value?.trim();
  const password = document.getElementById("signupPassword")?.value;
  const name = document.getElementById("signupName")?.value?.trim();
  const email = document.getElementById("signupEmail")?.value?.trim();
  const phone = document.getElementById("signupPhone")?.value?.trim();
  
  if(!username || !password || !name || !email){
    UI.toast("모든 필수 항목을 입력해주세요.");
    return;
  }
  
  const res = await Api.register(username, password, name, email, phone);
  if(!res.ok){ 
    UI.toast(res.message || "회원가입 실패"); 
    return; 
  }
  
  UI.toast("회원가입이 완료되었습니다. 로그인해주세요.");
  closeSignupDialog();
  openLoginDialog();
}

/* 문서 위임: 로그인/회원가입 버튼들 */
export function attachAuthDelegates(){
  document.addEventListener("click", async (e)=>{
    const t = e.target;
    if(!(t instanceof Element)) return;
    
    // 로그인 관련
    if(t.id === "btnOpenLogin" || t.id === "btnOpenLogin2"){ e.preventDefault(); openLoginDialog(); }
    if(t.id === "btnLoginCancel"){ e.preventDefault(); closeLoginDialog(); }
    if(t.id === "btnLoginDo"){ e.preventDefault(); doLogin(); }
    
    // 메인페이지 회원가입 버튼
    if(t.id === "btnSkip"){ e.preventDefault(); openSignupDialog(); }
    
    // 헤더 뱃지 클릭
    if(t.id === "badgeAuth"){ 
      e.preventDefault(); 
      const { token } = State.get();
      if(token) {
        // 로그아웃
        State.setToken(null);
        State.setUser(null);
        updateAuthBadge();
        UI.toast("로그아웃 되었습니다.");
        location.hash = "#/main";
        await navigate();
      } else {
        // 로그인 모달 열기
        openLoginDialog();
      }
    }
    
    // 회원가입 관련
    if(t.id === "btnShowSignup"){ e.preventDefault(); closeLoginDialog(); openSignupDialog(); }
    if(t.id === "btnSignupCancel"){ e.preventDefault(); closeSignupDialog(); }
    if(t.id === "btnSignupDo"){ e.preventDefault(); doSignup(); }
    if(t.id === "btnBackToLogin"){ e.preventDefault(); closeSignupDialog(); openLoginDialog(); }
  });
}
