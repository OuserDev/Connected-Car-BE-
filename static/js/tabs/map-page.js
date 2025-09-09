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
          <input id="map-q" placeholder="장소명을 입력하세요 (예: 스타벅스 강남점, 롯데월드타워)">
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

        UI.toast('🔍 검색 중...');

        try {
            // 네이버 Local Search API 사용 (지역/장소명 검색)
            naver.maps.Service.search(naver.maps.Service.SearchType.PLACE, {
                query: query,
                count: 5
            }, (status, response) => {
                if (status === naver.maps.Service.Status.ERROR) {
                    UI.toast('검색 중 오류가 발생했습니다.');
                    return;
                }
                
                if (response?.places && response.places.length > 0) {
                    const place = response.places[0];
                    const lat = parseFloat(place.y);
                    const lng = parseFloat(place.x);
                    
                    // HTML 태그 제거
                    const title = place.title?.replace(/<[^>]*>/g, '') || place.name || query;
                    const address = place.address || place.roadAddress || '';
                    const label = address ? `${title} (${address})` : title;

                    if (Number.isFinite(lat) && Number.isFinite(lng)) {
                        markAndCenter(lat, lng, label);
                        UI.toast(`📍 ${title}`);
                    } else {
                        UI.toast('좌표를 해석할 수 없습니다.');
                    }
                } else {
                    UI.toast('검색 결과가 없습니다.');
                }
            });
        } catch (err) {
            console.error('Search error:', err);
            UI.toast('검색 중 오류가 발생했습니다.');
        }
    }

    $go.addEventListener('click', doSearch);
    $q.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') doSearch();
    });
}
