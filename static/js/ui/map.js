// // ui/map.js - NAVER Maps JS API v3 기반 실제 지도 표시 (SPA 재마운트 안전)
// let _map = null;
// let _listenerHandles = [];

// function _removeListeners(){
//   try { _listenerHandles.forEach(h => naver.maps.Event.removeListener(h)); }
//   catch(e){ /* ignore */ }
//   finally { _listenerHandles = []; }
// }
// function _disposeMap(){ if (_map) { _removeListeners(); _map = null; } }

// function _fitToPoints(points){
//   if (!_map || !points || points.length === 0) return;
//   const bounds = new naver.maps.LatLngBounds(points[0], points[0]);
//   for (let i = 1; i < points.length; i++) bounds.extend(points[i]);
//   _map.fitBounds(bounds, { top:24, right:24, bottom:24, left:24 });
// }

// export function mount(selectorOrEl, { places = [], centerOnCurrent = true } = {}){
//   const el = typeof selectorOrEl === "string" ? document.querySelector(selectorOrEl) : selectorOrEl;
//   if (!el) return;
//   if (!window.naver || !naver.maps) { console.error("NAVER Maps not ready. Check ncpClientId and service URL allowlist."); return; }

//   _disposeMap();

//   const DEFAULT_CENTER = new naver.maps.LatLng(37.5665, 126.9780); // 서울시청
//   _map = new naver.maps.Map(el, {
//     center: DEFAULT_CENTER, zoom: 12, mapDataControl: true, scaleControl: true,
//   });

//   const points = [];

//   // 추천 장소 마커 + 인포윈도우
//   places.forEach(p => {
//     if (typeof p.lat === "number" && typeof p.lng === "number") {
//       const pos = new naver.maps.LatLng(p.lat, p.lng);
//       points.push(pos);
//       const marker = new naver.maps.Marker({ position: pos, map: _map });
//       const info = new naver.maps.InfoWindow({
//         content: `
//           <div style="padding:8px 10px; min-width:180px">
//             <b>${p.name}</b><br/>
//             <span style="color:#8892a6">${p.tag} · ${p.dist}</span>
//           </div>`,
//       });
//       const h = naver.maps.Event.addListener(marker, "click", () => info.open(_map, marker));
//       _listenerHandles.push(h);
//     }
//   });

//   // 현재 위치(권한 허용 시 → 중심을 '현재 위치'로)
//   if (navigator.geolocation && centerOnCurrent) {
//     navigator.geolocation.getCurrentPosition(
//       (pos) => {
//         const me = new naver.maps.LatLng(pos.coords.latitude, pos.coords.longitude);
//         points.push(me);
//         new naver.maps.Marker({
//           position: me,
//           icon: {
//             content:
//               '<div style="width:14px;height:14px;border-radius:50%;background:#4ea9ff;border:2px solid #fff;box-shadow:0 0 0 2px rgba(78,169,255,.35)"></div>',
//             size: new naver.maps.Size(18, 18),
//             anchor: new naver.maps.Point(9, 9),
//           },
//           map: _map,
//         });

//         // ✅ 핵심: 현재 위치를 지도 중심으로 고정
//         _map.setCenter(me);
//         // 장소가 전혀 없으면 기본 줌을 조금 더 확대
//         if (places.length === 0 && _map.getZoom() < 14) {
//           _map.setZoom(14, true);
//         }
//         // (의도적으로 fitBounds 호출 안 함)
//       },
//       // 실패하면 장소들로 fitBounds, 없으면 기본 중심 유지
//       () => { if (points.length) _fitToPoints(points); },
//       { enableHighAccuracy: true, timeout: 3000 }
//     );
//   } else {
//     // 지오로케이션 불가 시: 장소가 있으면 fitBounds
//     if (points.length) _fitToPoints(points);
//   }
// }

// // === 검색 결과 중심 이동 유틸 (기존 그대로 유지) ===
// let _searchMarker = null;
// export function markAndCenter(lat, lng, label){
//   if(!_map) return;
//   const latlng = new naver.maps.LatLng(lat, lng);
//   if(!_searchMarker){
//     _searchMarker = new naver.maps.Marker({ position: latlng, map: _map, title: label || '' });
//   }else{
//     _searchMarker.setPosition(latlng);
//   }
//   _map.setCenter(latlng);
//   if(_map.getZoom() < 14) _map.setZoom(14, true);
// }


// ui/map.js - NAVER Maps JS API v3 기반 실제 지도 표시 (SPA 재마운트 안전)
let _map = null;
let _listenerHandles = [];

// 🔴 추천 장소 마커 전용 보관소
let _placeMarkers = [];

// 🔎 검색 마커(별도 관리: 추천 마커 클리어 대상 아님)
let _searchMarker = null;

function _removeListeners(){
  try { _listenerHandles.forEach(h => naver.maps.Event.removeListener(h)); }
  catch(e){ /* ignore */ }
  finally { _listenerHandles = []; }
}
function _clearPlaceMarkers(){
  _placeMarkers.forEach(m => m.setMap(null));
  _placeMarkers = [];
}
function _disposeMap(){
  if (_map) { _removeListeners(); _map = null; }
  _clearPlaceMarkers();
  _searchMarker = null;
}

function _fitToPoints(points){
  if (!_map || !points || points.length === 0) return;
  const bounds = new naver.maps.LatLngBounds(points[0], points[0]);
  for (let i = 1; i < points.length; i++) bounds.extend(points[i]);
  _map.fitBounds(bounds, { top:24, right:24, bottom:24, left:24 });
}

// ✅ addPlaceMarkers 옵션으로 추천 마커 그릴지 여부 제어
export function mount(selectorOrEl, { places = [], addPlaceMarkers = true, centerOnCurrent = true } = {}){
  const el = typeof selectorOrEl === "string" ? document.querySelector(selectorOrEl) : selectorOrEl;
  if (!el) return;
  if (!window.naver || !naver.maps) { console.error("NAVER Maps not ready. Check ncpClientId and service URL allowlist."); return; }

  _disposeMap();

  const DEFAULT_CENTER = new naver.maps.LatLng(37.5665, 126.9780); // 서울시청
  _map = new naver.maps.Map(el, {
    center: DEFAULT_CENTER, zoom: 12, mapDataControl: true, scaleControl: true,
  });

  const points = [];

  // 🔵 추천 장소 마커 (옵션)
  if (addPlaceMarkers) {
    places.forEach(p => {
      if (typeof p.lat === "number" && typeof p.lng === "number") {
        const pos = new naver.maps.LatLng(p.lat, p.lng);
        points.push(pos);
        const marker = new naver.maps.Marker({ position: pos, map: _map });
        _placeMarkers.push(marker); // <-- 보관!
        const info = new naver.maps.InfoWindow({
          content: `
            <div style="padding:8px 10px; min-width:180px">
              <b>${p.name}</b><br/>
              <span style="color:#8892a6">${p.tag} · ${p.dist}</span>
            </div>`,
        });
        const h = naver.maps.Event.addListener(marker, "click", () => info.open(_map, marker));
        _listenerHandles.push(h);
      }
    });
  }

  // 현재 위치(권한 허용 시)
  if (navigator.geolocation && centerOnCurrent) {
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const me = new naver.maps.LatLng(pos.coords.latitude, pos.coords.longitude);
        // 현재 위치 마커는 place 마커가 아님(클리어 대상 아님)
        new naver.maps.Marker({
          position: me,
          icon: {
            content:
              '<div style="width:14px;height:14px;border-radius:50%;background:#4ea9ff;border:2px solid #fff;box-shadow:0 0 0 2px rgba(78,169,255,.35)"></div>',
            size: new naver.maps.Size(18, 18),
            anchor: new naver.maps.Point(9, 9),
          },
          map: _map,
        });

        // 현재 위치 중심
        _map.setCenter(me);
        if ((!addPlaceMarkers || _placeMarkers.length === 0) && _map.getZoom() < 14) {
          _map.setZoom(14, true);
        }
      },
      () => { if (points.length) _fitToPoints(points); },
      { enableHighAccuracy: true, timeout: 3000 }
    );
  } else {
    if (points.length) _fitToPoints(points);
  }
}

// === 검색 결과 중심 이동 유틸 (추천 마커와 별개) ===
export function markAndCenter(lat, lng, label){
  if(!_map) return;
  const latlng = new naver.maps.LatLng(lat, lng);
  if(!_searchMarker){
    _searchMarker = new naver.maps.Marker({ position: latlng, map: _map, title: label || '' });
  }else{
    _searchMarker.setPosition(latlng);
  }
  _map.setCenter(latlng);
  if(_map.getZoom() < 14) _map.setZoom(14, true);
}

// === 추천 마커만 지우기 ===
export function clearPlaceMarkers(){
  _clearPlaceMarkers();
}

// === (선택) 추천 마커 다시 추가하기 ===
export function addPlaceMarkers(places = []){
  if(!_map) return;
  places.forEach(p => {
    if (typeof p.lat === "number" && typeof p.lng === "number") {
      const pos = new naver.maps.LatLng(p.lat, p.lng);
      const marker = new naver.maps.Marker({ position: pos, map: _map });
      _placeMarkers.push(marker);
    }
  });
}

let _infoWin = null;

function _makeAddress(item) {
  if (!item) return '';
  const name = item.name;
  const region = item.region || {};
  const land = item.land || {};
  const a1 = region.area1?.name || '';
  const a2 = region.area2?.name || '';
  const a3 = region.area3?.name || '';
  const a4 = region.area4?.name || '';
  let rest = '';

  if (land.number1) {
    if (land.type === '2') rest += '산';
    rest += land.number1;
    if (land.number2) rest += '-' + land.number2;
  }
  let dong = a3, ri = a4;
  if (name === 'roadaddr' && land.name) { dong = land.name; ri = ''; }

  return [a1, a2, dong, ri, rest].filter(Boolean).join(' ');
}

export function enableReverseGeocodeClicks(enable = true){
  if(!_map || !enable) return;
  _infoWin = _infoWin || new naver.maps.InfoWindow({ anchorSkew: true });

  const h = naver.maps.Event.addListener(_map, 'click', (e) => {
    const latlng = e.coord;
    _infoWin.close();
    naver.maps.Service.reverseGeocode({
      coords: latlng,
      orders: [
        naver.maps.Service.OrderType.ADDR,
        naver.maps.Service.OrderType.ROAD_ADDR
      ].join(',')
    }, (status, response) => {
      if (status !== naver.maps.Service.Status.OK) return;
      const items = response?.v2?.results || [];
      const html = items.map((it, i) => {
        const tag = it.name === 'roadaddr' ? '[도로명 주소]' : '[지번 주소]';
        return `${i+1}. ${tag} ${_makeAddress(it)}`;
      }).join('<br />');

      _infoWin.setContent(`
        <div style="padding:10px;min-width:220px;line-height:150%;">
          <h4 style="margin-top:5px;">검색 좌표</h4><br />
          ${html}
        </div>`);
      _infoWin.open(_map, latlng);
    });
  });
  _listenerHandles.push(h);
}
