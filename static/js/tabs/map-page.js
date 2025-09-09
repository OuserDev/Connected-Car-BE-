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
            // 네이버 Search API를 사용하여 지역 검색
            const response = await fetch(`https://openapi.naver.com/v1/search/local.json?query=${encodeURIComponent(query)}&display=5&start=1&sort=random`, {
                method: 'GET',
                headers: {
                    'X-Naver-Client-Id': 'hCLNYd7oxu5YwWOcJIWq',
                    'X-Naver-Client-Secret': 'ofXo3chVUZ'
                }
            });

            if (!response.ok) {
                throw new Error(`API 요청 실패: ${response.status}`);
            }

            const data = await response.json();
            
            if (data.items && data.items.length > 0) {
                const item = data.items[0];
                
                // 네이버 Search API 응답에서 좌표 추출
                const lat = parseFloat(item.mapy) / 10000000; // 네이버 좌표계를 WGS84로 변환
                const lng = parseFloat(item.mapx) / 10000000;
                
                // HTML 태그 제거
                const title = item.title.replace(/<[^>]*>/g, '');
                const address = item.address;
                const label = `${title} (${address})`;

                if (Number.isFinite(lat) && Number.isFinite(lng)) {
                    markAndCenter(lat, lng, label);
                    UI.toast(`📍 ${title}`);
                } else {
                    UI.toast('좌표를 해석할 수 없습니다.');
                }
            } else {
                UI.toast('검색 결과가 없습니다.');
            }
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
