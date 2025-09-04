// tabs/control.js
import { Api } from "../api.js";
import { UI } from "../ui/components.js";
import { State } from "../state.js";
import { getRoot } from "../core/shared.js";

export async function renderControl(){
  const root = getRoot();
  const { user } = State.get();

  // 내부 상태(홈에서 받아온 스냅) - 상세 화면에서 일부 값 반영용
  let snap = null;

  // ─────────────────────────────────────────────────────────
  // 공통 유틸
  // ─────────────────────────────────────────────────────────
  function mountCarArt(){
    const wrap = document.getElementById("vehicleSvg");
    if(!wrap) return;
    const img = new Image();
    img.src = "./assets/cars/GRHYB.png";
    img.alt = "차량";
    img.decoding = "async";
    img.fetchPriority = "high";
    img.addEventListener("error", ()=>{
      wrap.innerHTML = "";
      try {
        wrap.appendChild(UI.svgFallback("#58d3ff", "Vehicle", "등록번호"));
      } catch {
        wrap.innerHTML = `<div style="width:220px;height:120px;border-radius:60px;background:#102235;border:1px solid #2b5d80"></div>`;
      }
    });
    wrap.appendChild(img);
  }
  const fmtDate = (iso) => iso ? new Date(iso).toLocaleString() : "-";
  const safe = (v) => (typeof v === "number" && Number.isFinite(v)) ? v : "-";

  // ─────────────────────────────────────────────────────────
  // ① 제어 홈
  // ─────────────────────────────────────────────────────────
  async function renderHome(){
    root.innerHTML = `
      <div class="card control-stage">
        <div class="kicker">제어</div>

        ${!user?.hasCar ? `
          <div class="cta" style="margin:6px 0 8px">
            <div>차량이 미등록 상태입니다. 아래 제어는 데모로 동작합니다.</div>
          </div>` : ``}

        <div class="vehicle-wrap">
          <div id="vehicleSvg" class="car" aria-label="차량"></div>

          <div class="hex-grid">
            <button id="hEngine"  class="hex-btn hex-pos-engine" title="시동 On/Off">⏻</button>
            <button id="hLock"    class="hex-btn hex-pos-lock"   title="문 잠금/해제">🔒</button>
            <button id="hHorn"    class="hex-btn hex-pos-horn"   title="경적">📣</button>
            <button id="hFlash"   class="hex-btn hex-pos-flash"  title="비상등">⚠️</button>
            <button id="hWindow"  class="hex-btn hex-pos-window" title="윈도우" disabled>🪟</button>
          </div>
        </div>

        <div class="control-hint">차량 및 경고등을 선택하면 상세 내용을 확인할 수 있습니다.</div>
      </div>

      <div class="ac-line">
        <div>현재 설정 온도</div>
        <div class="spacer"></div>
        <div id="stBottomTemp">—</div>
      </div>
      
      <div class="grid" style="grid-template-columns: repeat(3, minmax(0,1fr)); gap:8px; margin:10px 0 6px">
        <div class="chip"><span class="k">도어</span><b id="stLocked">—</b></div>
        <div class="chip"><span class="k">시동</span><b id="stEngine">—</b></div>
        <div class="chip"><span class="k">실내온도</span><b id="stCabin">—</b></div>
      </div>

      <div class="ctrl-cards">
        <div class="ctrl-card clickable" id="cardACLow" role="button" tabindex="0" aria-label="에어컨을 켜고 18도로 설정">
          <div class="value">Low</div>
          <div class="title">가장 시원하게</div>
          <div>❄️ 에어컨 ON</div>
        </div>

        <div class="ctrl-card">
          <div class="value" id="stTarget">—</div>
          <div class="title">스마트 공조</div>
          <div style="display:flex; gap:6px">
            <button class="btn" id="btnTempDown">- 온도</button>
            <button class="btn" id="btnTempUp">+ 온도</button>
            <button class="btn ghost" id="btnACOff">🛑 OFF</button>
          </div>
        </div>
      </div>

      <!-- 상세 진입 버튼 (세로, 크게) -->
      <div style="margin:14px 0; display:flex; flex-direction:column; gap:10px;">
        <button class="btn" id="btnGoStatus"
          style="width:100%; padding:14px 16px; font-size:16px; line-height:1.2; border-radius:12px;">
          차량상태 조회
        </button>

        <button class="btn" id="btnGoLogs"
          style="width:100%; padding:14px 16px; font-size:16px; line-height:1.2; border-radius:12px;">
          차량제어기록
        </button>

        <button class="btn" id="btnGoVideos"
          style="width:100%; padding:14px 16px; font-size:16px; line-height:1.2; border-radius:12px;">
          차량주행영상기록
        </button>
      </div>
    `;

    mountCarArt();

    const $locked = document.getElementById("stLocked");
    const $engine = document.getElementById("stEngine");
    const $cabin  = document.getElementById("stCabin");
    const $target = document.getElementById("stTarget");
    const $btmT   = document.getElementById("stBottomTemp");

    const $hEngine = document.getElementById("hEngine");
    const $hLock   = document.getElementById("hLock");
    const $hHorn   = document.getElementById("hHorn");
    const $hFlash  = document.getElementById("hFlash");

    const $btnACOff   = document.getElementById("btnACOff");
    const $btnTempUp  = document.getElementById("btnTempUp");
    const $btnTempDw  = document.getElementById("btnTempDown");
    const $cardACLow  = document.getElementById("cardACLow");

    function reflect(state){
      snap = state;
      // (주의) 기존 코드에서 문구가 반대로 되어 있었음: locked=true → "잠김"
      $locked.textContent = state.locked ? "locked" : "unlocked";
      $engine.textContent = state.engineOn ? "ON" : "OFF";
      const cabinNow = Number.isFinite(state.cabinTemp) ? state.cabinTemp : null;
      $cabin.textContent  = (cabinNow !== null ? `${cabinNow}℃` : "—");
      const t = Number.isFinite(state.cabinTempTarget) ? state.cabinTempTarget : 22;
      $target.textContent = `${t}℃`;
      $btmT.textContent   = `${t.toFixed(1)}℃`;

      $hEngine.classList.toggle("active", !!state.engineOn);
      $hLock.classList.toggle("active", !!state.locked);

      const $veh = document.getElementById("vehicleSvg");
      if ($veh) $veh.classList.toggle("glow", !!state.engineOn);
    }

    async function load(){
      const res = await Api.vehicleStatus();
      if(!res.ok){ UI.toast("상태를 불러오지 못했습니다."); return; }
      reflect(res.status);
    }

    async function doAct(action, data){
      const res = await Api.vehicleControl(action, data);
      if(!res.ok){ UI.toast(res.message || "제어 실패"); return; }
      UI.toast(res.message);
      reflect(res.status);
    }

    async function acLowQuick(){
      const on = await Api.vehicleControl("acOn");
      if(!on.ok){ UI.toast(on.message || "제어 실패"); return; }
      const temp = await Api.vehicleControl("setTemp", { target: 18 });
      if(!temp.ok){ UI.toast(temp.message || "제어 실패"); reflect(on.status); return; }
      reflect(temp.status);
      UI.toast("❄️ 에어컨 ON · 18℃");
    }

    // 육각 버튼
    $hEngine.addEventListener("click", () => { snap?.engineOn ? doAct("engineOff") : doAct("engineOn"); });
    $hLock  .addEventListener("click", () => { snap?.locked   ? doAct("unlock")   : doAct("lock"); });
    $hHorn  .addEventListener("click", () => doAct("horn"));
    $hFlash .addEventListener("click", () => doAct("flash"));

    // 카드 동작
    $btnACOff .addEventListener("click", () => doAct("acOff"));
    $btnTempUp.addEventListener("click", () => doAct("setTemp", { target: (snap?.cabinTempTarget ?? 22) + 1 }));
    $btnTempDw.addEventListener("click", () => doAct("setTemp", { target: (snap?.cabinTempTarget ?? 22) - 1 }));
    $cardACLow.addEventListener("click", acLowQuick);
    $cardACLow.addEventListener("keydown", (e)=>{ if(e.key === "Enter" || e.key === " "){ e.preventDefault(); acLowQuick(); } });

    // 상세 진입
    document.getElementById("btnGoStatus")?.addEventListener("click", renderStatusView);
    document.getElementById("btnGoLogs")?.addEventListener("click", renderLogsView);
    document.getElementById("btnGoVideos")?.addEventListener("click", renderVideosView);

    await load();
  }

  // ─────────────────────────────────────────────────────────
  // ② 차량 상태 상세 (요청 항목들 표시)
  // ─────────────────────────────────────────────────────────
  // async function renderStatusView(){
  //   // 기본 데모 상세(요청 포맷). 위치는 제외해달라고 했으므로 미포함.
  //   const DEMO_STATUS = {
  //     engine_state: "off",
  //     door_state: "unlocked",
  //     fuel: 75,
  //     battery: 12.6,
  //     voltage: "12V",
  //     tire_pressure: {
  //       front_left: 33, front_right: 34, rear_left: 34, rear_right: 33,
  //       recommended: 33, unit: "psi", warning_threshold: 30,
  //       last_checked: "2024-01-15T10:00:00Z"
  //     },
  //     odometer: {
  //       total_km: 15420, trip_a_km: 523.7, trip_b_km: 87.3,
  //       last_updated: "2024-01-15T10:00:00Z"
  //     }
  //   };

  //   // 가능하면 API에서 받아오고, 없으면 데모 + 홈 스냅 일부 반영
  //   let detail = DEMO_STATUS;
  //   if (typeof Api.vehicleStatusDetail === "function") {
  //     try {
  //       const r = await Api.vehicleStatusDetail();
  //       if (r?.ok && r.status) detail = r.status;
  //     } catch {}
  //   }
  //   // 홈 스냅 반영(엔진/도어)
  //   if (snap) {
  //     detail = {
  //       ...detail,
  //       engine_state: snap.engineOn ? "on" : "off",
  //       door_state: snap.locked ? "locked" : "unlocked"
  //     };
  //   }

  //   root.innerHTML = `
  //     <div class="card"><div class="body">
  //       <div class="row" style="gap:8px; align-items:center;">
  //         <button class="btn ghost" id="btnBackHome">← 뒤로가기</button>
  //         <div class="kicker">차량 상태</div>
  //       </div>
  //     </div></div>

  //     <div class="card"><div class="body">
  //       <div class="grid" style="grid-template-columns:repeat(2,minmax(0,1fr)); gap:10px;">
  //         <div class="chip"><span class="k">엔진</span><b>${detail.engine_state}</b></div>
  //         <div class="chip"><span class="k">도어</span><b>${detail.door_state}</b></div>
  //         <div class="chip"><span class="k">연료</span><b>${safe(detail.fuel)}%</b></div>
  //         <div class="chip"><span class="k">배터리 전압</span><b>${safe(detail.battery)} (${detail.voltage || "-"})</b></div>
  //       </div>
  //     </div></div>

  //     <div class="card"><div class="body">
  //       <div class="kicker">타이어 압력</div>
  //       <div class="grid" style="grid-template-columns:repeat(4,minmax(0,1fr)); gap:10px;">
  //         <div class="chip"><span class="k">FL</span><b>${safe(detail.tire_pressure?.front_left)}</b></div>
  //         <div class="chip"><span class="k">FR</span><b>${safe(detail.tire_pressure?.front_right)}</b></div>
  //         <div class="chip"><span class="k">RL</span><b>${safe(detail.tire_pressure?.rear_left)}</b></div>
  //         <div class="chip"><span class="k">RR</span><b>${safe(detail.tire_pressure?.rear_right)}</b></div>
  //       </div>
  //       <div class="muted" style="margin-top:6px">
  //         권장 ${safe(detail.tire_pressure?.recommended)} ${detail.tire_pressure?.unit || ""} ·
  //         경고 ${safe(detail.tire_pressure?.warning_threshold)} ·
  //         최종 점검 ${fmtDate(detail.tire_pressure?.last_checked)}
  //       </div>
  //     </div></div>

  //     <div class="card"><div class="body">
  //       <div class="kicker">주행 정보</div>
  //       <div class="grid" style="grid-template-columns:repeat(3,minmax(0,1fr)); gap:10px;">
  //         <div class="chip"><span class="k">총 주행</span><b>${typeof detail.odometer?.total_km === "number" ? detail.odometer.total_km.toLocaleString() : "-" } km</b></div>
  //         <div class="chip"><span class="k">Trip A</span><b>${safe(detail.odometer?.trip_a_km)} km</b></div>
  //         <div class="chip"><span class="k">Trip B</span><b>${safe(detail.odometer?.trip_b_km)} km</b></div>
  //       </div>
  //       <div class="muted" style="margin-top:6px">업데이트: ${fmtDate(detail.odometer?.last_updated)}</div>
  //     </div></div>
  //   `;

  //   document.getElementById("btnBackHome")?.addEventListener("click", renderHome);
  // }
// ─────────────────────────────────────────────────────────
// ② 차량 상태 상세 (실시간 업데이트 표시 + 주기적 새로고침)
// ─────────────────────────────────────────────────────────
  async function renderStatusView(){
    // 데모 기본값 (API 미존재 시)
    const DEMO_STATUS = {
      engine_state: "off",
      door_state: "unlocked",
      fuel: 75,
      battery: 12.6,
      voltage: "12V",
      tire_pressure: {
        front_left: 33, front_right: 34, rear_left: 34, rear_right: 33,
        recommended: 33, unit: "bar", warning_threshold: 30,
        last_checked: "2024-01-15T10:00:00Z"
      },
      odometer: {
        total_km: 15420, trip_a_km: 523.7, trip_b_km: 87.3,
        last_updated: "2024-01-15T10:00:00Z"
      }
    };

    let detail = DEMO_STATUS;
    // 홈 스냅(제어 홈에서 가져온 최신 스냅) 반영
    if (snap) {
      detail = {
        ...detail,
        engine_state: snap.engineOn ? "on" : "off",
        door_state: snap.locked ? "locked" : "unlocked"
      };
    }

    // 실시간용 타이머
    let liveTimer = null;   // "N초 전" 갱신
    let pollTimer = null;   // 주기적 새로고침
    let lastUpdatedMs = Date.now();

    const safe = (v) => (typeof v === "number" && Number.isFinite(v)) ? v : "-";
    const fmtDate = (iso) => iso ? new Date(iso).toLocaleString() : "-";
    const rel = (ms) => {
      const diff = Math.floor((Date.now() - ms) / 1000);
      if (diff < 1) return "방금 전";
      if (diff < 60) return `${diff}초 전`;
      const m = Math.floor(diff / 60);
      if (m < 60) return `${m}분 전`;
      return new Date(ms).toLocaleString();
    };
    const cleanup = ()=> {
      if (liveTimer) { clearInterval(liveTimer); liveTimer = null; }
      if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
    };

    // 화면 렌더
    const draw = (p) => {
      root.innerHTML = `
        <div class="card"><div class="body">
          <div class="row" style="gap:8px; align-items:center;">
            <button class="btn ghost" id="btnBackHome">← 뒤로가기</button>
            <div class="kicker">차량 상태</div>
            <div class="spacer"></div>
            <button class="btn ghost" id="btnRefresh">새로고침</button>
          </div>
        </div></div>

        <div class="card"><div class="body">
          <div class="grid" style="grid-template-columns:repeat(2,minmax(0,1fr)); gap:10px;">
            <div class="chip"><span class="k">엔진</span><b>${p.engine_state}</b></div>
            <div class="chip"><span class="k">도어</span><b>${p.door_state}</b></div>
            <div class="chip"><span class="k">연료</span><b>${safe(p.fuel)}%</b></div>
            <div class="chip"><span class="k">보조배터리</span><b>${safe(p.battery)} (${p.voltage || "-"})</b></div>
          </div>
        </div></div>

        <div class="card"><div class="body">
          <div class="kicker">타이어 압력</div>
          <div class="grid" style="grid-template-columns:repeat(4,minmax(0,1fr)); gap:10px;">
            <div class="chip"><span class="k">FL</span><b>${safe(p.tire_pressure?.front_left)}</b></div>
            <div class="chip"><span class="k">FR</span><b>${safe(p.tire_pressure?.front_right)}</b></div>
            <div class="chip"><span class="k">RL</span><b>${safe(p.tire_pressure?.rear_left)}</b></div>
            <div class="chip"><span class="k">RR</span><b>${safe(p.tire_pressure?.rear_right)}</b></div>
          </div>
          <div class="muted" style="margin-top:6px">
            권장 ${safe(p.tire_pressure?.recommended)} ${p.tire_pressure?.unit || ""} ·
            경고 ${safe(p.tire_pressure?.warning_threshold)} ·
            최종 점검 ${fmtDate(p.tire_pressure?.last_checked)}
          </div>
        </div></div>

        <div class="card"><div class="body">
          <div class="kicker">주행 정보</div>
          <div class="grid" style="grid-template-columns:repeat(3,minmax(0,1fr)); gap:10px;">
            <div class="chip"><span class="k">총 주행</span><b>${typeof p.odometer?.total_km === "number" ? p.odometer.total_km.toLocaleString() : "-"} km</b></div>
            <div class="chip"><span class="k">Trip A</span><b>${safe(p.odometer?.trip_a_km)} km</b></div>
            <div class="chip"><span class="k">Trip B</span><b>${safe(p.odometer?.trip_b_km)} km</b></div>
          </div>
          <div class="muted" id="odoMeta" style="margin-top:6px">
            업데이트: <span id="odoRel">-</span> <span class="muted">(${fmtDate(p.odometer?.last_updated)})</span>
          </div>
        </div></div>
      `;

      // 이벤트
      document.getElementById("btnBackHome")?.addEventListener("click", () => { cleanup(); renderHome(); });
      document.getElementById("btnRefresh")?.addEventListener("click", async () => { await fetchLatest(true); });

      // 실시간 "N초 전" 갱신
      const updateRel = () => {
        const el = document.getElementById("odoRel");
        if (el) el.textContent = rel(lastUpdatedMs);
      };
      updateRel();
      if (liveTimer) clearInterval(liveTimer);
      liveTimer = setInterval(updateRel, 1000);
    };

    // API에서 최신 상태 가져오기 (가능하면 서버 시간이 있으면 사용)
    async function fetchLatest(showToast=false){
      try{
        let next = null;
        if (typeof Api.vehicleStatusDetail === "function") {
          const r = await Api.vehicleStatusDetail();
          if (r?.ok && r.status) next = r.status;
        }
        // 없으면 데모+홈 스냅 반영 유지
        if (!next) next = detail;

        // 홈 스냅(엔진/도어 최신화)
        if (snap) {
          next = {
            ...next,
            engine_state: snap.engineOn ? "on" : "off",
            door_state: snap.locked ? "locked" : "unlocked"
          };
        }

        // 서버가 last_updated를 주면 그걸 사용, 없으면 지금 시각
        const serverISO = next?.odometer?.last_updated;
        lastUpdatedMs = serverISO ? Date.parse(serverISO) : Date.now();
        // lastUpdatedMs = Date.now();
        detail = next;
        draw(detail);
        if (showToast) UI.toast("업데이트 되었습니다.");
      } catch(e){
        // 실패해도 '업데이트 시도 시각'으로 표기
        lastUpdatedMs = Date.now();
        draw(detail);
        if (showToast) UI.toast("네트워크 상태를 확인해주세요.");
      }
    }

    // 최초 렌더 + 주기적 폴링(15초)
    await fetchLatest(false);
    pollTimer = setInterval(fetchLatest, 15000);
  }
  // ─────────────────────────────────────────────────────────
  // ③ 제어 기록(지금은 간단 문구)
  // ─────────────────────────────────────────────────────────
  async function renderLogsView(){
    root.innerHTML = `
      <div class="card"><div class="body">
        <div class="row" style="gap:8px; align-items:center;">
          <button class="btn ghost" id="btnBackHome2">← 뒤로가기</button>
          <div class="kicker">차량 제어 기록</div>
        </div>
      </div></div>

      <div class="card"><div class="body">
        <div>제어 기록 목록이 여기에 표시됩니다.</div>
      </div></div>
    `;
    document.getElementById("btnBackHome2")?.addEventListener("click", renderHome);
  }



  // ─────────────────────────────────────────────────────────
  // ③ 주행 영상 기록(지금은 간단 문구)
  // ─────────────────────────────────────────────────────────
  async function rendervideosView(){
    root.innerHTML = `
      <div class="card"><div class="body">
        <div class="row" style="gap:8px; align-items:center;">
          <button class="btn ghost" id="btnBackHome2">← 뒤로가기</button>
          <div class="kicker">차량 주행 영상 기록</div>
        </div>
      </div></div>

      <div class="card"><div class="body">
        <div>주행 영상 목록이 여기에 표시됩니다.</div>
      </div></div>
    `;
    document.getElementById("btnBackHome2")?.addEventListener("click", renderHome);
  }

  // 최초 렌더: 홈
  await renderHome();
}
