// tabs/main.js
import { Api } from "../api.js";
import { State } from "../state.js";
import { UI } from "../ui/components.js";
import { getRoot, waitForNaver } from "../core/shared.js";
import { mount as mountMap } from "../ui/map.js";

export async function renderMain(){
  const root = getRoot();
  root.innerHTML = "";

  const [{ ok: okP, items = [] } = {}, { ok: okS, status = null } = {}] =
    await Promise.all([Api.recommendedPlaces(), Api.vehicleStatus()]);

  const { user } = State.get();
  root.appendChild(user && user.hasCar ? UI.carHero(user, okS ? status : null) : UI.loginCallout());

  // 추천 리스트
  const listCard = UI.el("div","card");
  const listBody = UI.el("div","body");
  listBody.innerHTML = `<div class="kicker">가볼만한 곳</div>`;
  const list = UI.el("div","list");
  listBody.appendChild(list);
  if(!okP || !items.length){
    const empty = UI.el("div","muted","추천 데이터를 불러오는 중이거나 항목이 없습니다."); empty.style.padding="6px 2px";
    list.appendChild(empty);
  } else {
    items.forEach(p=>{
      const row = UI.el("div","place");
      row.innerHTML = `
        <div class="pin">📍</div>
        <div style="flex:1">
          <div class="title">${p.name}</div>
          <div class="meta">${p.tag} · ${p.dist}</div>
        </div>
        <button class="btn ghost">자세히</button>`;
      list.appendChild(row);
    });
  }
  listCard.appendChild(listBody);
  root.appendChild(listCard);

  // 지도
  const mapCard = UI.el("div","card");
  const mapBody = UI.el("div","body");
  mapBody.innerHTML = `
    <div class="kicker">지도</div>
    <div class="map"><div id="map-main"></div></div>`;
  mapCard.appendChild(mapBody);
  root.appendChild(mapCard);

  try{
    await waitForNaver();
    mountMap("#map-main", { places: items });
  }catch(e){
    const m = document.getElementById("map-main");
    if(m) m.innerHTML = `<div style="padding:14px" class="muted">지도를 초기화하지 못했습니다.<br>${String(e.message || e)}</div>`;
  }
}
