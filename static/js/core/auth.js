// core/auth.js
import { Api } from '../api.js';
import { State } from '../state.js';
import { updateAuthBadge, getScrim, startUserStatusCheck, stopUserStatusCheck } from './shared.js';
import { UI } from '../ui/components.js';
import { navigate } from '../app.js';

export function openLoginDialog() {
    const scrim = getScrim();
    scrim?.classList.add('show');
    scrim?.setAttribute('aria-hidden', 'false');
    document.body.classList.add('modal-open');
    setTimeout(() => document.getElementById('id')?.focus(), 30);
}
export function closeLoginDialog() {
    const scrim = getScrim();
    scrim?.classList.remove('show');
    scrim?.setAttribute('aria-hidden', 'true');
    document.body.classList.remove('modal-open');
    const id = document.getElementById('id');
    const pw = document.getElementById('pw');
    if (id) id.value = '';
    if (pw) pw.value = '';
}

export function openSignupDialog() {
    const scrim = document.getElementById('dlgSignupScrim');
    scrim?.classList.add('show');
    scrim?.setAttribute('aria-hidden', 'false');
    document.body.classList.add('modal-open');
    setTimeout(() => document.getElementById('signupUsername')?.focus(), 30);
}

export function closeSignupDialog() {
    const scrim = document.getElementById('dlgSignupScrim');
    scrim?.classList.remove('show');
    scrim?.setAttribute('aria-hidden', 'true');
    document.body.classList.remove('modal-open');
    const fields = ['signupUsername', 'signupPassword', 'signupName', 'signupEmail', 'signupPhone'];
    fields.forEach((id) => {
        const field = document.getElementById(id);
        if (field) field.value = '';
    });
}

export function openProfileDialog() {
    const { user } = State.get();
    const scrim = document.getElementById('dlgProfileScrim');
    scrim?.classList.add('show');
    scrim?.setAttribute('aria-hidden', 'false');
    document.body.classList.add('modal-open');

    // 현재 사용자 정보로 필드 채우기
    if (user) {
        document.getElementById('profileName').value = user.name || '';
        document.getElementById('profileEmail').value = user.email || '';
        document.getElementById('profilePhone').value = user.phone || '';
    }

    setTimeout(() => document.getElementById('profileName')?.focus(), 30);
}

export function closeProfileDialog() {
    const scrim = document.getElementById('dlgProfileScrim');
    scrim?.classList.remove('show');
    scrim?.setAttribute('aria-hidden', 'true');
    document.body.classList.remove('modal-open');
}
export async function doLogin() {
    const id = document.getElementById('id')?.value?.trim();
    const pw = document.getElementById('pw')?.value;
    const res = await Api.login(id, pw);
    if (!res.ok) {
        // 계정 정지 상태인 경우 특별한 메시지 표시
        if (res.status === 'suspended') {
            UI.toast('⚠️ ' + (res.message || '계정이 정지되었습니다. 관리자에게 문의하세요.'));
        } else {
            UI.toast(res.message || '로그인 실패');
        }
        return;
    }
    State.setToken(res.token);
    State.setUser(res.user);
    UI.toast('로그인 되었습니다.');
    await updateAuthBadge();

    // 로그인 성공 시 사용자 상태 주기적 확인 시작
    startUserStatusCheck();

    closeLoginDialog();
    location.hash = '#/main';
    await navigate();
}

export async function doSignup() {
    const username = document.getElementById('signupUsername')?.value?.trim();
    const password = document.getElementById('signupPassword')?.value;
    const name = document.getElementById('signupName')?.value?.trim();
    const email = document.getElementById('signupEmail')?.value?.trim();
    const phone = document.getElementById('signupPhone')?.value?.trim();

    if (!username || !password || !name || !email) {
        UI.toast('모든 필수 항목을 입력해주세요.');
        return;
    }

    const res = await Api.register(username, password, name, email, phone);
    if (!res.ok) {
        // 409 Conflict = 중복 사용자명
        if (res.status === 409) {
            UI.toast('이미 존재하는 사용자명입니다. 다른 사용자명을 선택해주세요.');
        } else {
            UI.toast(res.message || '회원가입 실패');
        }
        return;
    }

    UI.toast('회원가입이 완료되었습니다. 로그인해주세요.');
    closeSignupDialog();
    openLoginDialog();
}

export async function doProfileSave() {
    const name = document.getElementById('profileName')?.value?.trim();
    const email = document.getElementById('profileEmail')?.value?.trim();
    const phone = document.getElementById('profilePhone')?.value?.trim();

    if (!name || !email) {
        UI.toast('이름과 이메일은 필수 항목입니다.');
        return;
    }

    // 현재는 로컬 상태만 업데이트 (나중에 BE API 연동 가능)
    const { user } = State.get();
    const updatedUser = { ...user, name, email, phone };
    State.setUser(updatedUser);
    await updateAuthBadge();

    UI.toast('프로필이 업데이트되었습니다.');
    closeProfileDialog();
}

/* 문서 위임: 로그인/회원가입 버튼들 */
export function attachAuthDelegates() {
    document.addEventListener('click', async (e) => {
        const t = e.target;
        if (!(t instanceof Element)) return;

        // 로그인 관련
        if (t.id === 'btnOpenLogin' || t.id === 'btnOpenLogin2') {
            e.preventDefault();
            openLoginDialog();
        }
        if (t.id === 'btnLoginCancel') {
            e.preventDefault();
            closeLoginDialog();
        }
        if (t.id === 'btnLoginDo') {
            e.preventDefault();
            doLogin();
        }

        // 메인페이지 회원가입 버튼
        if (t.id === 'btnSkip') {
            e.preventDefault();
            openSignupDialog();
        }

        // 헤더 뱃지 클릭 (로그인/프로필)
        if (t.id === 'badgeAuth') {
            e.preventDefault();
            const { token } = State.get();
            if (token) {
                // 프로필 수정 모달 열기
                openProfileDialog();
            } else {
                // 로그인 모달 열기
                openLoginDialog();
            }
        }

        // 로그아웃 버튼 클릭
        if (t.id === 'btnLogout') {
            e.preventDefault();

            // 사용자 상태 확인 중지
            stopUserStatusCheck();

            State.setToken(null);
            State.setUser(null);
            await updateAuthBadge();
            UI.toast('로그아웃 되었습니다.');
            location.hash = '#/main';
            await navigate();
        }

        // 회원가입 관련
        if (t.id === 'btnShowSignup') {
            e.preventDefault();
            closeLoginDialog();
            openSignupDialog();
        }
        if (t.id === 'btnSignupCancel') {
            e.preventDefault();
            closeSignupDialog();
        }
        if (t.id === 'btnSignupDo') {
            e.preventDefault();
            doSignup();
        }
        if (t.id === 'btnBackToLogin') {
            e.preventDefault();
            closeSignupDialog();
            openLoginDialog();
        }

        // 프로필 수정 관련
        if (t.id === 'btnProfileCancel') {
            e.preventDefault();
            closeProfileDialog();
        }
        if (t.id === 'btnProfileSave') {
            e.preventDefault();
            doProfileSave();
        }
    });
}
