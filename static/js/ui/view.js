// ui/views.js
import { api } from "../api.js";
import { Icon, toast } from "./components.js";

export async function mountControlsTab(root){
  root.classList.add("controls");
  let state = await api.getVehicleState();
  render();

  function render(){
    root.innerHTML = `
      <div class="row" aria-live="polite">
        <div>
          <h3>도어</h3>
          <div class="small">현재 상태: 
            <span class="status ${state.door}">
              ${state.door === "locked" ? Icon("lock") + "잠김" : Icon("unlock") + "열림"}
            </span>
          </div>
        </div>
        <div class="group">
          <button type="button" class="btn outline" data-action="door_unlock" ${state.door==="unlocked" ? "disabled":""}>
            ${Icon("unlock")} 문 열기
          </button>
          <button type="button" class="btn solid" data-action="door_lock" ${state.door==="locked" ? "disabled":""}>
            ${Icon("lock")} 문 잠그기
          </button>
        </div>
      </div>

      <div class="row" aria-live="polite">
        <div>
          <h3>엔진</h3>
          <div class="small">현재 상태: 
            <span class="status ${state.engine}">
              ${state.engine === "on" ? Icon("power") + "시동 켜짐" : Icon("power-off") + "시동 꺼짐"}
            </span>
          </div>
        </div>
        <div class="group">
          <button type="button" class="btn outline" data-action="engine_off" ${state.engine==="off" ? "disabled":""}>
            ${Icon("power-off")} 시동 끄기
          </button>
          <button type="button" class="btn solid" data-action="engine_on" ${state.engine==="on" ? "disabled":""}>
            ${Icon("power")} 시동 켜기
          </button>
        </div>
      </div>
    `;

    root.querySelectorAll("button[data-action]").forEach(btn=>{
      btn.addEventListener("click", onActionClick, { once:false });
    });
  }

  let inFlight = false;
  async function onActionClick(e){
    if(inFlight) return;
    const btn = e.currentTarget;
    const action = btn.dataset.action;
    try{
      inFlight = true;
      setBusy(btn, true);

      // API 호출
      const res = await api.actions[action]();

      // 상태 반영 (idempotent)
      if(action.startsWith("door_")){
        state.door = res.door ?? (action === "door_lock" ? "locked" : "unlocked");
        toast(state.door === "locked" ? "문을 잠갔습니다." : "문을 열었습니다.");
      } else if(action.startsWith("engine_")){
        state.engine = res.engine ?? (action === "engine_on" ? "on" : "off");
        toast(state.engine === "on" ? "시동을 켰습니다." : "시동을 껐습니다.");
      }

      render();
    } catch(err){
      toast(`실패: ${err.message || err}`, "error", 3000);
      setBusy(btn, false);
    } finally{
      inFlight = false;
    }
  }

  function setBusy(el, busy){
    el.toggleAttribute("disabled", busy);
    el.setAttribute("aria-busy", String(busy));
  }
}
