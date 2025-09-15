// tabs/map-page.js
import { Api } from '../api.js';
import { UI } from '../ui/components.js';
import { getRoot, waitForNaver } from '../core/shared.js';
import { mount as mountMap, markAndCenter, enableReverseGeocodeClicks } from '../ui/map.js';

export async function renderMap() {
    const root = getRoot();
    root.innerHTML = '';

    const wrap = UI.el('div', 'card');
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

    try {
        await waitForNaver();
        mountMap('#map-page', { places, addPlaceMarkers: false });
        enableReverseGeocodeClicks(true);
    } catch (e) {
        const m = document.getElementById('map-page');
        if (m) m.innerHTML = `<div style="padding:14px" class="muted">지도를 초기화하지 못했습니다.<br>${String(e.message || e)}</div>`;
        return;
    }

    const $q = document.getElementById('map-q');
    const $go = document.getElementById('map-go');

    async function doSearch() {
        const query = $q.value.trim();
        if (!query) return UI.toast('검색어를 입력하세요.');

        // 네이버 지도 서비스 확인
        if (!window.naver?.maps?.Service) {
            return UI.toast('네이버 지도 서비스를 사용할 수 없습니다');
        }

        UI.toast('🔍 검색 중...');

        try {

            naver.maps.Service.geocode(
                {
                    query: query,
                },
                function (status, response) {

                    if (status !== naver.maps.Service.Status.OK) {

                        return UI.toast('검색 결과를 찾을 수 없습니다');
                    }

                    // 네이버 지도 API v3 응답 구조: response.v2.addresses
                    var result = response.v2;
                    var addresses = result.addresses;


                    if (addresses && addresses.length > 0) {
                        var item = addresses[0];
                        var lat = parseFloat(item.y);
                        var lng = parseFloat(item.x);
                        var label = item.roadAddress || item.jibunAddress || query;


                        if (Number.isFinite(lat) && Number.isFinite(lng)) {
                            markAndCenter(lat, lng, label);
                            UI.toast(`📍 ${label}`);
                        } else {
                            UI.toast('좌표를 해석할 수 없습니다.');
                        }
                    } else {
                        UI.toast('검색 결과가 없습니다.');
                    }
                }
            );
        } catch (err) {
            UI.toast('검색 중 오류가 발생했습니다.');
        }
    }

    $go.addEventListener('click', doSearch);
    $q.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') doSearch();
    });
}
