// ui/components.js - small UI factory utilities

export const UI = (() => {
    const el = (tag, cls, html) => {
        const n = document.createElement(tag);
        if (cls) n.className = cls;
        if (html !== undefined) n.innerHTML = html;
        return n;
    };

    // ✅ 단일 토스트 유틸: #toast가 있으면 그걸 쓰고, 없으면 임시 토스트를 만들어 사용
    const toast = (msg, ms = 1800) => {
        let t = document.getElementById('toast');
        if (t) {
            t.textContent = msg;
            t.classList.add('show');
            setTimeout(() => t.classList.remove('show'), ms);
            return;
        }
        // fallback toast (DOM에 #toast 없을 때)
        const f = document.createElement('div');
        f.className = 'toast';
        Object.assign(f.style, {
            position: 'fixed',
            right: '16px',
            bottom: '16px',
            padding: '12px 14px',
            background: '#0d1430',
            color: '#fff',
            border: '1px solid #1f3347',
            borderRadius: '12px',
            zIndex: '9999',
            opacity: '0',
            transition: 'opacity .15s ease',
        });
        f.textContent = msg;
        document.body.appendChild(f);
        requestAnimationFrame(() => (f.style.opacity = '1'));
        setTimeout(() => {
            f.style.opacity = '0';
            setTimeout(() => f.remove(), 180);
        }, ms);
    };

    const svgFallback = (color = '#79d1ff', model = 'Vehicle', plate = '등록번호') => {
        const wrap = el('div');
        wrap.innerHTML = `
      <svg viewBox="0 0 640 280" role="img" aria-label="차량">
        <defs>
          <linearGradient id="g" x1="0" x2="1">
            <stop offset="0%" stop-color="${color}"/>
            <stop offset="100%" stop-color="#2d5bff"/>
          </linearGradient>
        </defs>
        <g>
          <rect x="30" y="160" width="580" height="40" rx="20" fill="rgba(0,0,0,.35)"/>
          <path d="M80,160 C120,70 180,50 260,50 L420,50 C500,50 560,70 600,160 L600,190 L80,190 Z" fill="url(#g)"/>
          <circle cx="180" cy="190" r="38" fill="#0a0f24" stroke="#314082" stroke-width="6"/>
          <circle cx="500" cy="190" r="38" fill="#0a0f24" stroke="#314082" stroke-width="6"/>
          <rect x="260" y="70" width="160" height="40" rx="8" fill="#9fd6ff" opacity=".75"/>
          <rect x="300" y="120" width="120" height="12" rx="6" fill="#0a0f24" opacity=".6"/>
        </g>
      </svg>`;
        return wrap.firstElementChild;
    };

    // 차량 이미지 기본 경로(플레이스홀더)
    const PLACEHOLDER_IMG = './assets/cars/USER1_GRANDEUR.jpg';
    // const PLACEHOLDER_IMG = "./assets/cars/GRHYB.png";

    // ✅ 메인 히어로: 업로드한 사진(State.user.carPhotoData)을 최우선으로 사용
    const carHero = (user, status, carInfo = null) => {
        const card = el('div', 'card');
        const hero = el('div', 'hero');

        const model = carInfo?.model_name || carInfo?.model || user?.car?.model || 'Vehicle';
        const plate = carInfo?.license_plate || carInfo?.licensePlate || user?.car?.plate || '등록번호';
        const caption = el('div', 'caption', `${model} · ${plate}`);

        // 차량 ID에 맞는 이미지 경로 생성 (main_car_images 폴더 사용)
        let carImagePath = PLACEHOLDER_IMG;
        if (carInfo?.id) {
            carImagePath = `/static/assets/cars/main_car_images/${carInfo.id}.jpg`;
        }

        // 우선순위: user.carPhotoData > 차량별 이미지 > carInfo.imageUrl > user.car.imageUrl > PLACEHOLDER > SVG
        const prefer = [user?.carPhotoData, carImagePath, carInfo?.imageUrl, user?.car?.imageUrl, PLACEHOLDER_IMG].filter(Boolean);

        const img = new Image();
        img.className = 'hero-img';
        img.alt = `${model} (${plate})`;
        img.loading = 'lazy';

        let tryIndex = 0;
        const tryNext = () => {
            if (tryIndex < prefer.length) {
                img.src = prefer[tryIndex++];
            } else {
                // 모든 시도 실패 → SVG 폴백
                hero.innerHTML = '';
                hero.appendChild(svgFallback(user?.car?.color, model, plate));
                hero.appendChild(caption);
            }
        };

        img.onerror = tryNext;

        // 최초 시도
        if (prefer.length) {
            tryNext();
            hero.appendChild(img);
            hero.appendChild(caption);
        } else {
            // 아무 소스도 없으면 바로 폴백
            hero.appendChild(svgFallback(user?.car?.color, model, plate));
            hero.appendChild(caption);
        }

        // 디버깅: 실제 status 데이터 확인
        console.log('🔧 carHero status data:', status);

        // 메트릭을 모델명과 동일한 스타일로 변경
        const metrics = el('div', 'hero-metrics');

        // 모델명과 동일한 스타일의 박스 생성
        const createStatusBox = (label, value, isWarning = false) => {
            const box = el('div');
            box.style.cssText = `
                background: rgba(0,0,0,0.6); 
                padding: 8px 12px; 
                border-radius: 8px; 
                backdrop-filter: blur(8px);
                color: ${isWarning ? '#ef4444' : '#3b82f6'};
                font-weight: 600;
                font-size: 14px;
                margin: 4px;
            `;
            box.innerHTML = `${label}: ${value}`;
            return box;
        };

        // 실제 차량 상태 데이터 사용
        const fuel = status && typeof status.fuel === 'number' ? `${status.fuel}%` : '데이터 없음';
        const engineState = status?.engine_state === true ? 'ON' : status?.engine_state === false ? 'OFF' : '알 수 없음';

        // 연료가 낮으면 경고 색상
        const isFuelLow = status && typeof status.fuel === 'number' && status.fuel < 30;

        metrics.appendChild(createStatusBox('연료', fuel, isFuelLow));
        metrics.appendChild(createStatusBox('시동', engineState));

        hero.appendChild(metrics);
        card.appendChild(hero);
        return card;
    };

    const loginCallout = () => {
        const card = el('div', 'card');
        const body = el('div', 'body');
        body.innerHTML = `
      <div class="kicker">접속 필요</div>
      <div class="cta" style="text-align: center; padding: 24px 16px;">
        <div style="margin-bottom: 20px;">차량 정보 보기를 위해 <b>로그인</b> 해주세요.</div>
        <div class="row" style="justify-content: center; gap: 12px;">
          <button class="btn brand" id="btnOpenLogin">로그인</button>
          <button class="btn ghost" id="btnSkip">회원가입</button>
        </div>
      </div>`;
        card.appendChild(body);
        return card;
    };

    // 차량이 없는 경우 UI
    const noCarCallout = () => {
        const card = el('div', 'card');
        const body = el('div', 'body');
        body.innerHTML = `
      <div class="kicker">차량 등록 필요</div>
      <div class="cta" style="text-align: center; padding: 24px 16px;">
        <div style="font-size: 48px; margin-bottom: 16px;">🚗</div>
        <div style="margin-bottom: 12px; font-weight: 600;">등록된 차량이 없습니다</div>
        <div style="margin-bottom: 20px; color: #6b7280;">라이선스 플레이트와 VIN 코드를 입력하여 차량을 등록하세요</div>
        <div class="row" style="justify-content: center; gap: 12px;">
          <button class="btn brand" id="btnRegisterCar">차량 등록하기</button>
        </div>
      </div>
      
      <!-- 차량 등록 모달 -->
      <dialog class="modal" id="dlgCarRegister">
        <div class="hd">
          차량 등록
          <button type="button" class="btn-close" id="btnCloseCarRegister">×</button>
        </div>
        <form method="dialog" id="carRegisterForm">
          <div class="bd">
            <div class="form-row">
              <label>라이선스 플레이트 (번호판)</label>
              <input type="text" id="licensePlate" placeholder="12가3456" required />
            </div>
            <div class="form-row">
              <label>VIN 코드</label>
              <input type="text" id="vinCode" placeholder="KMHL14JA1PA123456" required />
            </div>
          </div>
          <div class="ft">
            <button class="btn ghost" type="button" id="btnCancelCarRegister">취소</button>
            <button class="btn brand" id="btnSubmitCarRegister" type="submit">확인</button>
          </div>
        </form>
      </dialog>
      
      <!-- 차량 확인 모달 -->
      <dialog class="modal" id="dlgCarConfirm" style="display: none;">
        <div class="hd">
          차량 정보 확인
          <button type="button" class="btn-close" id="btnCloseCarConfirm">×</button>
        </div>
        <div class="bd" id="carConfirmContent">
          <!-- 차량 정보가 동적으로 표시됩니다 -->
        </div>
        <div class="ft">
          <button class="btn ghost" type="button" id="btnCancelCarConfirm">아니오</button>
          <button class="btn brand" id="btnConfirmCarRegister">네, 맞습니다</button>
        </div>
      </dialog>`;
        card.appendChild(body);
        return card;
    };

    // 여러 차량 선택 UI
    const carSelector = (cars, selectedCarId = null) => {
        const card = el('div', 'card');
        const body = el('div', 'body');

        const header = el('div', 'kicker', '내 차량 목록');
        body.appendChild(header);

        cars.forEach((car, index) => {
            const carItem = el('div', 'car-item');
            carItem.style.cssText = `
        padding: 12px 16px; margin: 8px 0; border: 1px solid #e5e7eb; 
        border-radius: 8px; cursor: pointer; transition: all 0.2s;
        ${selectedCarId === car.id ? 'border-color: #3b82f6; background: #eff6ff;' : ''}
      `;

            carItem.innerHTML = `
        <div style="display: flex; align-items: center;">
          <div style="flex: 1;">
            <div style="font-weight: 600; color: #3b82f6;">${car.model_name || 'Unknown'}</div>
            <div style="font-size: 14px; color: #6b7280;">${car.license_plate || '번호판 미등록'}</div>
          </div>
          <div style="color: #3b82f6;">
            ${selectedCarId === car.id ? '✓ 선택됨' : '선택하기'}
          </div>
        </div>
      `;

            carItem.addEventListener('click', () => {
                // 차량 선택 이벤트 발생
                window.dispatchEvent(new CustomEvent('carSelected', { detail: car }));
            });

            body.appendChild(carItem);
        });

        card.appendChild(body);
        return card;
    };

    // ⬅️ svgFallback을 포함해 내보냄 (control 탭에서 UI.svgFallback 사용)
    // return { el, toast, svgFallback, carHero, loginCallout };
    return { el, toast, svgFallback, carHero, loginCallout, noCarCallout, carSelector };
})();

// ===== (선택) 아이콘/스피너 유틸 =====
// ＊다른 파일에서 직접 쓰고 있을 수 있어 유지 (중복 toast 함수는 제거)
export const Icon = (name, { className = '' } = {}) => `<svg class="icon ${className}" aria-hidden="true"><use href="assets/icons.svg#${name}"></use></svg>`;

export const Spinner = `<span class="spinner" aria-hidden="true">${Icon('loader')}</span>`;
