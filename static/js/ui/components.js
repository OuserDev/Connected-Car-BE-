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
    let t = document.getElementById("toast");
    if (t) {
      t.textContent = msg;
      t.classList.add("show");
      setTimeout(() => t.classList.remove("show"), ms);
      return;
    }
    // fallback toast (DOM에 #toast 없을 때)
    const f = document.createElement("div");
    f.className = "toast";
    Object.assign(f.style, {
      position:"fixed", right:"16px", bottom:"16px",
      padding:"12px 14px", background:"#0d1430", color:"#fff",
      border:"1px solid #1f3347", borderRadius:"12px",
      zIndex:"9999", opacity:"0", transition:"opacity .15s ease"
    });
    f.textContent = msg;
    document.body.appendChild(f);
    requestAnimationFrame(()=> f.style.opacity = "1");
    setTimeout(()=> {
      f.style.opacity = "0";
      setTimeout(()=> f.remove(), 180);
    }, ms);
  };

  const svgFallback = (color = "#79d1ff", model = "Vehicle", plate = "등록번호") => {
    const wrap = el("div");
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
  const PLACEHOLDER_IMG = "./assets/cars/USER1_GRANDEUR.jpg";
  // const PLACEHOLDER_IMG = "./assets/cars/GRHYB.png";

  // ✅ 메인 히어로: 업로드한 사진(State.user.carPhotoData)을 최우선으로 사용
  const carHero = (user, status) => {
    const card = el("div", "card");
    const hero = el("div", "hero");

    const model = user?.car?.model || "Vehicle";
    const plate = user?.car?.plate || "등록번호";
    const caption = el("div", "caption", `${model} · ${plate}`);

    // 우선순위: user.carPhotoData > user.car.imageUrl > PLACEHOLDER > SVG
    const prefer = [
      user?.carPhotoData,
      user?.car?.imageUrl,
      PLACEHOLDER_IMG
    ].filter(Boolean);

    const img = new Image();
    img.className = "hero-img";
    img.alt = `${model} (${plate})`;
    img.loading = "lazy";

    let tryIndex = 0;
    const tryNext = () => {
      if (tryIndex < prefer.length) {
        img.src = prefer[tryIndex++];
      } else {
        // 모든 시도 실패 → SVG 폴백
        hero.innerHTML = "";
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

    // 메트릭 칩
    const metrics = el("div", "hero-metrics");
    const chip = (label, value, cls = "") => {
      const d = el("div", `chip ${cls}`);
      d.innerHTML = `<span class="k">${label}</span><b>${value}</b>`;
      return d;
    };

    const rangeKm = (status && typeof status.rangeKm === "number") ? `${status.rangeKm}km` : "—";
    const battPct = (status && typeof status.batteryPct === "number") ? `${status.batteryPct}%` : "—";
    const battCls = (status && typeof status.batteryPct === "number")
      ? (status.batteryPct < 15 ? "danger" : (status.batteryPct < 30 ? "warn" : ""))
      : "";

    metrics.appendChild(chip("주행가능 거리", rangeKm));
    // 필요 시 다시 활성화
    // metrics.appendChild(chip("배터리", battPct, battCls));

    hero.appendChild(metrics);
    card.appendChild(hero);
    return card;
  };

  const loginCallout = () => {
    const card = el("div", "card");
    const body = el("div", "body");
    body.innerHTML = `
      <div class="kicker">접속 필요</div>
      <div class="cta">
        <div>차량 정보 보기를 위해 <b>로그인</b> 해주세요.</div>
        <div class="row">
          <button class="btn brand" id="btnOpenLogin">로그인</button>
          <button class="btn ghost" id="btnSkip">회원가입</button>
        </div>
      </div>`;
    card.appendChild(body);
    return card;
  };

  // ⬅️ svgFallback을 포함해 내보냄 (control 탭에서 UI.svgFallback 사용)
  // return { el, toast, svgFallback, carHero, loginCallout };
  return { el, toast, svgFallback, carHero, loginCallout };
})();


// ===== (선택) 아이콘/스피너 유틸 =====
// ＊다른 파일에서 직접 쓰고 있을 수 있어 유지 (중복 toast 함수는 제거)
export const Icon = (name, {className=""} = {}) =>
  `<svg class="icon ${className}" aria-hidden="true"><use href="assets/icons.svg#${name}"></use></svg>`;

export const Spinner = `<span class="spinner" aria-hidden="true">${Icon("loader")}</span>`;
