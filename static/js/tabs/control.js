// tabs/control.js
import { Api } from '../api.js';
import { UI } from '../ui/components.js';
import { State } from '../state.js';
import { getRoot } from '../core/shared.js';

export async function renderControl() {
    const root = getRoot();
    const { user } = State.get();
    let { selectedCarId } = State.get();

    // 선택된 차량 정보 및 상태
    let currentCar = null;
    let vehicleStatus = null;

    // ─────────────────────────────────────────────────────────
    // 공통 유틸
    // ─────────────────────────────────────────────────────────
    function mountCarArt(carInfo) {
        const wrap = document.getElementById('vehicleSvg');
        if (!wrap) return;

        if (carInfo && carInfo.id) {
            // API에서 제공하는 controlImageUrl 사용
            const img = new Image();
            img.src = carInfo.controlImageUrl || `/static/assets/cars/control_car_images/${carInfo.id}.png`;
            img.alt = carInfo.model_name || carInfo.model || '차량';
            img.decoding = 'async';
            img.fetchPriority = 'high';
            img.addEventListener('error', () => {
                // 이미지 로드 실패시 폴백
                wrap.innerHTML = '';
                try {
                    wrap.appendChild(UI.svgFallback('#58d3ff', carInfo.model_name || 'Vehicle', carInfo.license_plate || '등록번호'));
                } catch {
                    wrap.innerHTML = `<div style="width:220px;height:120px;border-radius:60px;background:#102235;border:1px solid #2b5d80"></div>`;
                }
            });
            wrap.appendChild(img);
        } else {
            // 차량 정보 없을 때 기본 이미지 (첫 번째 차량 이미지 사용)
            const img = new Image();
            img.src = '/static/assets/cars/control_car_images/1.png';
            img.alt = '차량';
            img.addEventListener('error', () => {
                wrap.innerHTML = `<div style="width:220px;height:120px;border-radius:60px;background:#102235;border:1px solid #2b5d80"></div>`;
            });
            wrap.appendChild(img);
        }
    }

    const fmtDate = (iso) => (iso ? new Date(iso).toLocaleString() : '-');
    const safe = (v) => (typeof v === 'number' && Number.isFinite(v) ? v : '-');

    // ─────────────────────────────────────────────────────────
    // ① 제어 홈
    // ─────────────────────────────────────────────────────────
    async function renderHome() {
        // 선택된 차량 정보 로드
        try {
            // selectedCarId가 없으면 먼저 차량 목록을 가져와서 첫 번째 차량을 선택
            if (!selectedCarId) {
                const carsResponse = await fetch('/api/cars', { credentials: 'include' });
                if (carsResponse.ok) {
                    const carsData = await carsResponse.json();
                    if (carsData.success && carsData.data && carsData.data.length > 0) {
                        const firstCarId = carsData.data[0].id;
                        State.setSelectedCarId(firstCarId);
                        selectedCarId = firstCarId;
                        console.log(`자동으로 첫 번째 차량 선택: ${firstCarId}`);
                    } else {
                        console.warn('등록된 차량이 없습니다');
                        // 차량이 없는 경우 데모 모드로 진행
                        selectedCarId = null;
                    }
                }
            }

            const vehicleResponse = await Api.vehicleStatus();
            if (vehicleResponse.ok) {
                if (vehicleResponse.allCars && vehicleResponse.allCars.length > 1) {
                    // 여러 차량 중 선택된 차량 찾기
                    currentCar = vehicleResponse.allCars.find((car) => car.id === selectedCarId) || vehicleResponse.carInfo;
                } else {
                    currentCar = vehicleResponse.carInfo;
                }
                vehicleStatus = vehicleResponse.status;
            }
        } catch (error) {
            console.error('차량 정보 로드 실패:', error);
        }

        root.innerHTML = `
      <div class="card control-stage">
        <div class="kicker">제어</div>
        
        ${
            currentCar
                ? `
        <div class="car-info" style="text-align: center; margin-bottom: 16px;">
            <div style="font-weight: 600; color: #fff;">${currentCar.model_name || currentCar.model}</div>
            <div style="font-size: 14px; color: #8b9dc3;">${currentCar.license_plate || currentCar.licensePlate}</div>
        </div>
        `
                : ''
        }

        ${
            !user?.hasCar
                ? `
          <div class="cta" style="margin:6px 0 8px">
            <div>차량이 미등록 상태입니다. 아래 제어는 데모로 동작합니다.</div>
          </div>`
                : ``
        }

        <div class="vehicle-wrap">
          <div id="vehicleSvg" class="car" aria-label="차량"></div>

          <div class="hex-grid">
            <button id="hEngine"  class="hex-btn hex-pos-engine" title="시동 On/Off">⏻</button>
            <button id="hLock"    class="hex-btn hex-pos-lock"   title="문 잠금/해제">🔒</button>
            <button id="hHorn"    class="hex-btn hex-pos-horn"   title="경적">📣</button>
            <button id="hFlash"   class="hex-btn hex-pos-flash"  title="비상등">⚠️</button>
            <button id="hAC"      class="hex-btn hex-pos-window" title="에어컨">❄️</button>
          </div>
        </div>

        <div class="control-hint">차량 및 경고등을 선택하면 상세 내용을 확인할 수 있습니다.</div>
      </div>

      
      <div class="grid" style="grid-template-columns: repeat(3, minmax(0,1fr)); gap:8px; margin:10px 0 6px">
        <div class="chip"><span class="k">도어</span><b id="stLocked">—</b></div>
        <div class="chip"><span class="k">시동</span><b id="stEngine">—</b></div>
        <div class="chip"><span class="k">에어컨</span><b id="stAC">—</b></div>
      </div>
      
      <div class="grid" style="grid-template-columns: repeat(3, minmax(0,1fr)); gap:8px; margin:0 0 16px">
        <div class="chip"><span class="k">실내온도</span><b id="stCabin">—</b></div>
        <div class="chip"><span class="k">연료</span><b id="stFuel">—</b></div>
        <div class="chip"><span class="k">배터리</span><b id="stBattery">—</b></div>
      </div>

      <div class="ctrl-cards" style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; margin: 16px 0;">
        <div class="ctrl-card clickable" id="cardACLow" role="button" tabindex="0" aria-label="에어컨을 켜고 18도로 설정">
          <div class="value">18℃</div>
          <div class="title">가장 시원하게</div>
          <div>❄️ 에어컨 ON</div>
        </div>

        <div class="ctrl-card" style="text-align: center;">
          <div class="value" id="stTarget">—</div>
          <div class="title">현재 설정</div>
          <div style="display:flex; gap:4px; justify-content: center; flex-wrap: wrap;">
            <button class="btn" id="btnTempDown" style="font-size: 12px; padding: 4px 8px;">-</button>
            <button class="btn" id="btnTempUp" style="font-size: 12px; padding: 4px 8px;">+</button>
            <button class="btn ghost" id="btnACOff" style="font-size: 12px; padding: 4px 8px;">OFF</button>
          </div>
        </div>
        
        <div class="ctrl-card clickable" id="cardHeat" role="button" tabindex="0" aria-label="히터를 켜고 25도로 설정">
          <div class="value">25℃</div>
          <div class="title">따뜻하게</div>
          <div>🔥 히터 ON</div>
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

        mountCarArt(currentCar);

        const $locked = document.getElementById('stLocked');
        const $engine = document.getElementById('stEngine');
        const $cabin = document.getElementById('stCabin');
        const $target = document.getElementById('stTarget');
        const $ac = document.getElementById('stAC');
        const $fuel = document.getElementById('stFuel');
        const $battery = document.getElementById('stBattery');

        const $hEngine = document.getElementById('hEngine');
        const $hLock = document.getElementById('hLock');
        const $hHorn = document.getElementById('hHorn');
        const $hFlash = document.getElementById('hFlash');
        const $hAC = document.getElementById('hAC');

        const $btnACOff = document.getElementById('btnACOff');
        const $btnTempUp = document.getElementById('btnTempUp');
        const $btnTempDw = document.getElementById('btnTempDown');
        const $cardACLow = document.getElementById('cardACLow');
        const $cardHeat = document.getElementById('cardHeat');

        function reflect(state) {
            console.log('reflect called with state:', state);
            vehicleStatus = state;

            // state가 없거나 undefined인 경우 기본값 처리
            if (!state) {
                console.warn('reflect: state is undefined');
                $locked.textContent = '—';
                $engine.textContent = '—';
                $ac.textContent = '—';
                $cabin.textContent = '—';
                $target.textContent = '—';
                $fuel.textContent = '—';
                $battery.textContent = '—';
                return;
            }

            // 도어 상태 표시 (실제 API boolean과 MockAPI 문자열 모두 지원)
            let doorState;
            if (state.door_state !== undefined) {
                doorState = state.door_state ? 'locked' : 'unlocked'; // boolean → string
            } else if (state.doorState !== undefined) {
                doorState = state.doorState;
            } else if (state.locked !== undefined) {
                doorState = state.locked ? 'locked' : 'unlocked';
            } else {
                doorState = 'unlocked';
            }
            const doorText = doorState === 'locked' ? '잠김' : '열림';
            console.log('Door state:', state.door_state, '-> doorState:', doorState, '-> Display:', doorText);
            $locked.textContent = doorText;

            // 시동 상태 표시 (실제 API boolean과 MockAPI 문자열 모두 지원)
            let engineState;
            if (state.engine_state !== undefined) {
                engineState = state.engine_state ? 'on' : 'off'; // boolean → string
            } else if (state.engineState !== undefined) {
                engineState = state.engineState;
            } else if (state.engineOn !== undefined) {
                engineState = state.engineOn ? 'on' : 'off';
            } else {
                engineState = 'off';
            }
            const engineText = engineState === 'on' ? 'ON' : 'OFF';
            console.log('Engine state:', state.engine_state, '-> engineState:', engineState, '-> Display:', engineText);
            $engine.textContent = engineText;

            // 에어컨 상태 표시 (실제 API boolean과 MockAPI 문자열 모두 지원)
            let acState;
            const acValue = state.climate?.ac_state || state.ac_state;
            if (acValue !== undefined) {
                acState = acValue ? 'on' : 'off'; // boolean → string
            } else if (state.acOn !== undefined) {
                acState = state.acOn ? 'on' : 'off';
            } else {
                acState = 'off';
            }
            const acText = acState === 'on' ? 'ON' : 'OFF';
            console.log('AC state:', acValue, '-> acState:', acState, '-> Display:', acText);
            $ac.textContent = acText;

            // 온도 표시 (MockAPI와 실제 API 형식 모두 지원)
            const currentTemp = state.climate?.current_temp || state.current_temp || state.cabinTemp;
            const targetTemp = state.climate?.target_temp || state.target_temp || state.targetTemp || state.cabinTempTarget || 22;
            console.log('Temperature - current:', currentTemp, 'target:', targetTemp);
            $cabin.textContent = currentTemp !== null ? `${currentTemp.toFixed(2)}℃` : '—';
            $target.textContent = `${targetTemp}℃`;

            // 연료 및 배터리 표시 (실제 API와 MockAPI 형식 모두 지원)
            const fuel = state.fuel || 75;
            let battery = state.battery;
            if (!battery && state.battery_voltage) {
                battery = state.battery_voltage; // 실제 API에서 battery_voltage 사용
            } else if (!battery && state.batteryPct) {
                battery = state.batteryPct / 100 * 12.6; // MockAPI batteryPct를 전압으로 변환
            } else if (!battery) {
                battery = 12.6; // 기본값
            }
            
            console.log('Fuel:', fuel, 'Battery:', battery);
            $fuel.textContent = `${fuel}%`;
            $battery.textContent = `${battery.toFixed(1)}V`;

            // 버튼 상태 업데이트
            $hEngine.classList.toggle('active', engineState === 'on');
            $hLock.classList.toggle('active', doorState === 'locked');
            $hAC.classList.toggle('active', acState === 'on');

            // 차량 시각적 효과
            const $veh = document.getElementById('vehicleSvg');
            if ($veh) $veh.classList.toggle('glow', engineState === 'on');
        }

        async function load() {
            const res = await Api.vehicleStatus();
            if (!res.ok) {
                UI.toast('상태를 불러오지 못했습니다.');
                return;
            }
            reflect(res.status);
        }

        async function doAct(action, data) {
            try {
                if (!selectedCarId) {
                    UI.toast('차량을 선택해주세요');
                    return;
                }
                
                const res = await Api.vehicleControl(selectedCarId, action, data);
                if (!res.ok) {
                    UI.toast(res.message || '제어 실패');
                    return;
                }
                UI.toast(res.message || '제어 완료');

                // 응답에 status가 있는 경우에만 reflect 호출
                console.log('doAct result:', res);
                if (res.status) {
                    console.log('Updating status with:', res.status);
                    reflect(res.status);
                } else {
                    console.log('No status in response, reloading...');
                    // status가 없으면 전체 상태를 다시 로드
                    setTimeout(() => load(), 500); // 약간의 지연 후 상태 새로고침
                }
            } catch (error) {
                console.error('doAct error:', error);
                UI.toast('제어 요청 중 오류가 발생했습니다');
            }
        }

        async function acLowQuick() {
            try {
                await doAct('ac_state', { value: true });
                await doAct('target_temp', { value: 18 });
                UI.toast('❄️ 에어컨 ON · 18℃');
            } catch (error) {
                UI.toast('에어컨 제어 실패');
            }
        }

        async function heatQuick() {
            try {
                await doAct('heater_state', { value: true });
                await doAct('target_temp', { value: 25 });
                UI.toast('🔥 히터 ON · 25℃');
            } catch (error) {
                UI.toast('히터 제어 실패');
            }
        }

        // 육각 버튼 이벤트
        $hEngine.addEventListener('click', () => {
            // 실제 API는 boolean, MockAPI는 string 처리
            let currentState;
            if (vehicleStatus?.engine_state !== undefined) {
                currentState = vehicleStatus.engine_state; // boolean
            } else if (vehicleStatus?.engineState !== undefined) {
                currentState = vehicleStatus.engineState === 'on'; // string → boolean
            } else if (vehicleStatus?.engineOn !== undefined) {
                currentState = vehicleStatus.engineOn; // boolean
            } else {
                currentState = false;
            }
            const newState = !currentState; // boolean toggle
            doAct('engine_state', { value: newState });
        });

        $hLock.addEventListener('click', () => {
            // 실제 API는 boolean, MockAPI는 string 처리
            let currentState;
            if (vehicleStatus?.door_state !== undefined) {
                currentState = vehicleStatus.door_state; // boolean
            } else if (vehicleStatus?.doorState !== undefined) {
                currentState = vehicleStatus.doorState === 'locked'; // string → boolean
            } else if (vehicleStatus?.locked !== undefined) {
                currentState = vehicleStatus.locked; // boolean
            } else {
                currentState = false;
            }
            const newState = !currentState; // boolean toggle
            doAct('door_state', { value: newState });
        });

        $hHorn.addEventListener('click', () => {
            doAct('horn', { value: true });
        });

        $hFlash.addEventListener('click', () => {
            doAct('flash', { value: true });
        });

        $hAC.addEventListener('click', () => {
            // 실제 API는 boolean, MockAPI는 string 처리
            let currentState;
            const acValue = vehicleStatus?.climate?.ac_state || vehicleStatus?.ac_state;
            if (acValue !== undefined) {
                currentState = acValue; // boolean
            } else if (vehicleStatus?.acOn !== undefined) {
                currentState = vehicleStatus.acOn; // boolean
            } else {
                currentState = false;
            }
            const newState = !currentState; // boolean toggle
            doAct('ac_state', { value: newState });
        });

        // 카드 동작
        $btnACOff.addEventListener('click', () => doAct('ac_state', { value: false }));
        $btnTempUp.addEventListener('click', () => {
            const currentTemp = vehicleStatus?.climate?.target_temp || vehicleStatus?.target_temp || vehicleStatus?.targetTemp || vehicleStatus?.cabinTempTarget || 22;
            doAct('target_temp', { value: Math.min(currentTemp + 1, 30), target: Math.min(currentTemp + 1, 30) });
        });
        $btnTempDw.addEventListener('click', () => {
            const currentTemp = vehicleStatus?.climate?.target_temp || vehicleStatus?.target_temp || vehicleStatus?.targetTemp || vehicleStatus?.cabinTempTarget || 22;
            doAct('target_temp', { value: Math.max(currentTemp - 1, 16), target: Math.max(currentTemp - 1, 16) });
        });

        $cardACLow.addEventListener('click', acLowQuick);
        $cardACLow.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                acLowQuick();
            }
        });

        $cardHeat.addEventListener('click', heatQuick);
        $cardHeat.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                heatQuick();
            }
        });

        // 상세 진입
        document.getElementById('btnGoStatus')?.addEventListener('click', renderStatusView);
        document.getElementById('btnGoLogs')?.addEventListener('click', renderLogsView);
        document.getElementById('btnGoVideos')?.addEventListener('click', rendervideosView);

        // 초기 상태 로드
        if (vehicleStatus) {
            reflect(vehicleStatus);
        } else {
            await load();
        }
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
    async function renderStatusView() {
        // 기본값 (API 데이터가 없을 경우에만)
        let detail = {
            engine_state: 'unknown',
            door_state: 'unknown',
            fuel: 0,
            battery: 0,
            voltage: '알 수 없음',
            tire_pressure: null,
            odometer: null,
        };
        // 홈에서 가져온 최신 차량 상태 반영
        if (vehicleStatus) {
            detail = {
                ...detail,
                engine_state: vehicleStatus.engine_state || vehicleStatus.engineState || 'off',
                door_state: vehicleStatus.door_state || vehicleStatus.doorState || 'unlocked',
                fuel: vehicleStatus.fuel || 0,
                battery: vehicleStatus.battery_voltage || vehicleStatus.battery || 0,
                voltage: vehicleStatus.target_voltage ? `${vehicleStatus.target_voltage}V` : '알 수 없음',
                // car-api에서 제공하는 실제 타이어 압력 데이터 사용
                tire_pressure: vehicleStatus.tire_pressure || null,
                // car-api에서 제공하는 실제 주행 거리 데이터 사용 (Trip A/B는 서버에서 미제공)
                odometer: vehicleStatus.odometer ? {
                    ...vehicleStatus.odometer,
                    // Trip A/B는 car-api에서 제공하지 않으므로 기본값 사용
                    trip_a_km: vehicleStatus.odometer.trip_a_km || null,
                    trip_b_km: vehicleStatus.odometer.trip_b_km || null,
                    last_updated: vehicleStatus.last_updated || new Date().toISOString()
                } : null,
                // 기타 car-api 제공 데이터
                climate: vehicleStatus.climate || null,
                location: vehicleStatus.location || null,
                last_updated: vehicleStatus.last_updated || new Date().toISOString()
            };
        }

        // 실시간용 타이머
        let liveTimer = null; // "N초 전" 갱신
        let pollTimer = null; // 주기적 새로고침
        let lastUpdatedMs = Date.now();

        const safe = (v) => (typeof v === 'number' && Number.isFinite(v) ? v : '-');
        const fmtDate = (iso) => (iso ? new Date(iso).toLocaleString() : '-');
        const rel = (ms) => {
            const diff = Math.floor((Date.now() - ms) / 1000);
            if (diff < 1) return '방금 전';
            if (diff < 60) return `${diff}초 전`;
            const m = Math.floor(diff / 60);
            if (m < 60) return `${m}분 전`;
            return new Date(ms).toLocaleString();
        };
        const cleanup = () => {
            if (liveTimer) {
                clearInterval(liveTimer);
                liveTimer = null;
            }
            if (pollTimer) {
                clearInterval(pollTimer);
                pollTimer = null;
            }
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
            <div class="chip"><span class="k">보조배터리</span><b>${safe(p.battery)} (${p.voltage || '-'})</b></div>
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
            권장 ${safe(p.tire_pressure?.recommended)} ${p.tire_pressure?.unit || ''} ·
            경고 ${safe(p.tire_pressure?.warning_threshold)} ·
            최종 점검 ${fmtDate(p.tire_pressure?.last_checked)}
          </div>
        </div></div>

        <div class="card"><div class="body">
          <div class="kicker">주행 정보</div>
          <div class="grid" style="grid-template-columns:repeat(${p.odometer?.trip_a_km || p.odometer?.trip_b_km ? '3' : '1'},minmax(0,1fr)); gap:10px;">
            <div class="chip"><span class="k">총 주행</span><b>${typeof p.odometer?.total_km === 'number' ? p.odometer.total_km.toLocaleString() : '-'} km</b></div>
            ${p.odometer?.trip_a_km ? `<div class="chip"><span class="k">Trip A</span><b>${safe(p.odometer.trip_a_km)} km</b></div>` : ''}
            ${p.odometer?.trip_b_km ? `<div class="chip"><span class="k">Trip B</span><b>${safe(p.odometer.trip_b_km)} km</b></div>` : ''}
          </div>
          <div class="muted" id="odoMeta" style="margin-top:6px">
            업데이트: <span id="odoRel">-</span> <span class="muted">(${fmtDate(p.odometer?.last_updated)})</span>
          </div>
        </div></div>
      `;

            // 이벤트
            document.getElementById('btnBackHome')?.addEventListener('click', () => {
                cleanup();
                renderHome();
            });
            document.getElementById('btnRefresh')?.addEventListener('click', async () => {
                await fetchLatest(true);
            });

            // 실시간 "N초 전" 갱신
            const updateRel = () => {
                const el = document.getElementById('odoRel');
                if (el) el.textContent = rel(lastUpdatedMs);
            };
            updateRel();
            if (liveTimer) clearInterval(liveTimer);
            liveTimer = setInterval(updateRel, 1000);
        };

        // API에서 최신 상태 가져오기 (가능하면 서버 시간이 있으면 사용)
        async function fetchLatest(showToast = false) {
            try {
                let next = null;
                if (typeof Api.vehicleStatusDetail === 'function') {
                    const r = await Api.vehicleStatusDetail();
                    if (r?.ok && r.status) next = r.status;
                }
                // 없으면 데모+홈 스냅 반영 유지
                if (!next) next = detail;

                // 홈에서 가져온 최신 상태 반영 (엔진/도어 최신화)
                if (vehicleStatus) {
                    next = {
                        ...next,
                        engine_state: vehicleStatus.engine_state || vehicleStatus.engineState || 'off',
                        door_state: vehicleStatus.door_state || vehicleStatus.doorState || 'unlocked',
                    };
                }

                // 서버가 last_updated를 주면 그걸 사용, 없으면 지금 시각
                const serverISO = next?.odometer?.last_updated;
                lastUpdatedMs = serverISO ? Date.parse(serverISO) : Date.now();
                // lastUpdatedMs = Date.now();
                detail = next;
                draw(detail);
                if (showToast) UI.toast('업데이트 되었습니다.');
            } catch (e) {
                // 실패해도 '업데이트 시도 시각'으로 표기
                lastUpdatedMs = Date.now();
                draw(detail);
                if (showToast) UI.toast('네트워크 상태를 확인해주세요.');
            }
        }

        // 최초 렌더 + 주기적 폴링(15초)
        await fetchLatest(false);
        pollTimer = setInterval(fetchLatest, 15000);
    }
    // ─────────────────────────────────────────────────────────
    // ③ 제어 기록 (실제 API 연동)
    // ─────────────────────────────────────────────────────────
    async function renderLogsView() {
        let logs = [];
        let loading = true;

        // 로딩 상태 표시
        root.innerHTML = `
      <div class="card"><div class="body">
        <div class="row" style="gap:8px; align-items:center;">
          <button class="btn ghost" id="btnBackHome2">← 뒤로가기</button>
          <div class="kicker">차량 제어 기록</div>
          <div class="spacer"></div>
          <button class="btn ghost" id="btnRefreshLogs">새로고침</button>
        </div>
      </div></div>

      <div class="card"><div class="body">
        <div id="logsContent">로딩 중...</div>
      </div></div>
    `;

        const $content = document.getElementById('logsContent');
        
        async function loadLogs() {
            console.log('🔍 [DEBUG] control.js loadLogs() 시작');
            
            try {
                loading = true;
                $content.innerHTML = '로딩 중...';
                console.log('🔍 [DEBUG] loading 상태 설정, UI 업데이트됨');
                
                // RealAPI에서 제어 로그 가져오기
                console.log('🔍 [DEBUG] Api.controlLogs() 호출 시작');
                const result = await Api.controlLogs();
                console.log('🔍 [DEBUG] Api.controlLogs() 결과:', result);
                
                if (result.ok) {
                    logs = result.logs || [];
                    console.log('🔍 [DEBUG] 로그 데이터 설정됨, 개수:', logs.length);
                    console.log('🔍 [DEBUG] 첫 번째 로그 샘플:', logs[0]);
                    renderLogsList();
                } else {
                    console.error('❌ [ERROR] controlLogs 실패:', result.message);
                    $content.innerHTML = `<div class="muted">제어 기록을 불러올 수 없습니다: ${result.message}</div>`;
                }
            } catch (error) {
                console.error('❌ [ERROR] Control logs error:', error);
                $content.innerHTML = `<div class="muted">제어 기록 로딩 중 오류: ${error.message}</div>`;
            } finally {
                loading = false;
                console.log('🔍 [DEBUG] loadLogs() 완료, loading = false');
            }
        }

        // action을 사용자 친화적 텍스트로 변환
        function convertActionToFriendly(action) {
            const actionMap = {
                'door_state_True': '🔒 문 잠금',
                'door_state_False': '🔓 문 열기',
                'engine_state_True': '🚗 시동 켜기',
                'engine_state_False': '🔴 시동 끄기',
                'ac_state_True': '❄️ 에어컨 켜기',
                'ac_state_False': '🔴 에어컨 끄기',
                'target_temp_18': '🌡️ 온도 18°C 설정',
                'target_temp_19': '🌡️ 온도 19°C 설정',
                'target_temp_20': '🌡️ 온도 20°C 설정',
                'target_temp_21': '🌡️ 온도 21°C 설정',
                'target_temp_22': '🌡️ 온도 22°C 설정',
                'target_temp_23': '🌡️ 온도 23°C 설정',
                'target_temp_24': '🌡️ 온도 24°C 설정',
                'target_temp_25': '🌡️ 온도 25°C 설정',
                'horn_activated': '📣 경적',
                'hazard_lights_activated': '💡 비상등'
            };
            
            // 동적으로 온도 설정 처리
            if (action && action.startsWith('target_temp_')) {
                const temp = action.split('_')[2];
                return `🌡️ 온도 ${temp}°C 설정`;
            }
            
            return actionMap[action] || action;
        }

        function renderLogsList() {
            if (logs.length === 0) {
                $content.innerHTML = '<div class="muted">아직 제어 기록이 없습니다.</div>';
                return;
            }

            const logItems = logs.slice(0, 50).map(log => {
                // 실제 API 응답 구조에 맞게 수정
                const timestamp = new Date(log.timestamp).toLocaleString();
                const statusIcon = (log.result === 'success' || log.result === undefined) ? '✅' : '❌';
                
                // action을 사용자 친화적으로 변환
                const actionText = convertActionToFriendly(log.action) || log.action || '알 수 없는 동작';
                
                return `
                    <div class="chip" style="margin-bottom: 8px; display: flex; align-items: center; gap: 8px;">
                        <span style="font-size: 16px;">${statusIcon}</span>
                        <div style="flex: 1;">
                            <div style="font-weight: 500;">${actionText}</div>
                            <div class="muted" style="font-size: 12px;">
                                ${timestamp}
                                ${log.parameters?.value !== undefined ? ` • ${log.parameters.value}` : ''}
                            </div>
                        </div>
                    </div>
                `;
            }).join('');

            $content.innerHTML = `
                <div style="margin-bottom: 12px;">
                    <span class="muted">최근 ${logs.length}개의 제어 기록</span>
                </div>
                ${logItems}
            `;
        }

        // 이벤트 리스너
        document.getElementById('btnBackHome2')?.addEventListener('click', renderHome);
        document.getElementById('btnRefreshLogs')?.addEventListener('click', loadLogs);

        // 초기 로딩
        await loadLogs();
    }

    // ─────────────────────────────────────────────────────────
    // ③ 주행 영상 기록(지금은 간단 문구)
    // ─────────────────────────────────────────────────────────
    async function rendervideosView() {
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
        document.getElementById('btnBackHome2')?.addEventListener('click', renderHome);
    }

    // 최초 렌더: 홈
    await renderHome();
}
