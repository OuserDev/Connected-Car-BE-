// tabs/map-page.js
import { Api } from "../api.js";
import { UI } from "../ui/components.js";
import { getRoot, waitForNaver } from "../core/shared.js";
import { mount as mountMap, markAndCenter, enableReverseGeocodeClicks } from "../ui/map.js";

export async function renderMap(){
  const root = getRoot();
  root.innerHTML = "";

  const wrap = UI.el("div","card");
  wrap.innerHTML = `
    <div class="body">
      <div class="kicker">네이버 지도</div>
      <div class="map">
        <div class="searchbar">
          <input id="map-q" placeholder="주소 또는 장소를 입력하세요 (예: 강남역 / 서울특별시청)">
          <button class="btn brand" id="map-go">검색</button>
        </div>
        <div id="map-page"></div>
      </div>
    </div>`;
  root.appendChild(wrap);

  const res = await Api.recommendedPlaces();
  const places = res.ok ? res.items : [];

  try{
    await waitForNaver();
    mountMap("#map-page", { places, addPlaceMarkers: false });
    enableReverseGeocodeClicks(true);
  }catch(e){
    const m = document.getElementById("map-page");
    if(m) m.innerHTML = `<div style="padding:14px" class="muted">지도를 초기화하지 못했습니다.<br>${String(e.message || e)}</div>`;
    return;
  }

  const $q  = document.getElementById('map-q');
  const $go = document.getElementById('map-go');

  async function doSearch(){
    const query = $q.value.trim();
    if(!query) return UI.toast("검색어를 입력하세요.");

    try{
      naver.maps.Service.geocode({ query }, (status, response) => {
        if (status !== naver.maps.Service.Status.OK) {
          console.warn('Geocode status:', status, response);
          return UI.toast("검색 실패 또는 결과 없음");
        }
        let lat, lng, label = query;

        const v2item = response?.v2?.addresses?.[0];
        if (v2item) {
          lng = parseFloat(v2item.x);
          lat = parseFloat(v2item.y);
          label = v2item.roadAddress || v2item.jibunAddress || label;
        }
        if ((!Number.isFinite(lat) || !Number.isFinite(lng)) && response?.result?.items?.length){
          const it = response.result.items[0];
          lng = Number.isFinite(it?.point?.x) ? it.point.x : parseFloat(it?.point?.x);
          lat = Number.isFinite(it?.point?.y) ? it.point.y : parseFloat(it?.point?.y);
          label = it.address || label;
        }
        if (Number.isFinite(lat) && Number.isFinite(lng)){
          markAndCenter(lat, lng, label);
        } else {
          UI.toast("좌표를 해석할 수 없습니다.");
        }
      });
    }catch(err){
      console.error('Geocode error:', err);
      UI.toast("지오코딩 중 오류가 발생했습니다.");
    }
  }

  $go.addEventListener('click', doSearch);
  $q.addEventListener('keydown', (e)=>{ if(e.key === 'Enter') doSearch(); });
}
