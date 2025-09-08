// tabs/settings.js
import { Api } from '../api.js';
import { State } from '../state.js';
import { UI } from '../ui/components.js';
import { updateTabsDisabledState } from '../core/shared.js';

// 차량 등록 모달 함수
function showVehicleRegistrationModal() {
    // 기존 모달이 있다면 제거
    const existingModal = document.getElementById('vehicleRegistrationModal');
    if (existingModal) existingModal.remove();

    // 모달 생성
    const modal = document.createElement('div');
    modal.id = 'vehicleRegistrationModal';
    modal.style.cssText = `
        position: fixed; top: 0; left: 0; right: 0; bottom: 0;
        background: rgba(0,0,0,0.8); display: flex; align-items: center; justify-content: center;
        z-index: 10000; padding: 20px;
    `;

    modal.innerHTML = `
        <div style="background: linear-gradient(180deg, #173147, #0d1b2d); border: 1px solid #2b5d80; 
                    border-radius: 16px; padding: 24px; max-width: 400px; width: 100%;
                    box-shadow: 0 20px 60px rgba(0,0,0,0.5);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <h3 style="margin: 0; color: #52e8c6; font-size: 18px;">🚗 차량 추가 등록</h3>
                <button id="closeModal" style="background: none; border: none; color: #88a9bf; 
                                               font-size: 24px; cursor: pointer; padding: 0; line-height: 1;">×</button>
            </div>
            
            <p style="margin: 0 0 20px 0; color: #88a9bf; font-size: 14px;">
                새로운 차량을 등록하려면 라이선스 플레이트와 VIN 코드를 입력하세요.
            </p>
            
            <div style="margin-bottom: 16px;">
                <label style="display: block; margin-bottom: 6px; font-weight: 600; color: #3b82f6;">라이선스 플레이트</label>
                <input type="text" id="modalLicensePlate" placeholder="예: 12가 3456" 
                       style="width: 100%; padding: 12px; border: 1px solid #2b5d80; 
                              background: rgba(0,0,0,0.3); color: white; border-radius: 8px;
                              font-size: 14px; box-sizing: border-box;" maxlength="20">
            </div>
            
            <div style="margin-bottom: 20px;">
                <label style="display: block; margin-bottom: 6px; font-weight: 600; color: #3b82f6;">VIN 코드</label>
                <input type="text" id="modalVinCode" placeholder="예: KMHL24JA1PA234567" 
                       style="width: 100%; padding: 12px; border: 1px solid #2b5d80; 
                              background: rgba(0,0,0,0.3); color: white; border-radius: 8px;
                              font-size: 14px; box-sizing: border-box;" maxlength="17">
            </div>
            
            <div style="display: flex; gap: 10px; margin-bottom: 16px;">
                <button class="btn brand" id="modalBtnVerify" style="flex: 1;">
                    🔍 차량 정보 확인
                </button>
                <button class="btn" id="modalBtnRegister" style="flex: 1;" disabled>
                    ✅ 등록 완료
                </button>
            </div>
            
            <div id="modalVehicleResult" style="display: none;">
                <!-- 차량 정보 확인 결과 -->
            </div>
        </div>
    `;

    // 모달을 DOM에 추가
    document.body.appendChild(modal);

    // 이벤트 리스너 추가
    const closeBtn = modal.querySelector('#closeModal');
    const verifyBtn = modal.querySelector('#modalBtnVerify');
    const registerBtn = modal.querySelector('#modalBtnRegister');
    const resultDiv = modal.querySelector('#modalVehicleResult');

    // 모달 닫기
    closeBtn.addEventListener('click', () => modal.remove());
    modal.addEventListener('click', (e) => {
        if (e.target === modal) modal.remove();
    });

    // 차량 정보 확인
    verifyBtn.addEventListener('click', async () => {
        const licensePlate = modal.querySelector('#modalLicensePlate').value.trim();
        const vinCode = modal.querySelector('#modalVinCode').value.trim();

        if (!licensePlate || !vinCode) {
            UI.toast('라이선스 플레이트와 VIN 코드를 모두 입력해주세요.');
            return;
        }

        try {
            const response = await fetch('/api/cars/verify', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ licensePlate, vinCode }),
            });

            const data = await response.json();

            if (data.success) {
                resultDiv.style.display = 'block';
                resultDiv.innerHTML = `
                    <div style="padding: 12px; background: rgba(34, 197, 94, 0.1); 
                                border: 1px solid rgba(34, 197, 94, 0.3); border-radius: 8px;">
                        <div style="color: #22c55e; font-weight: 600; margin-bottom: 8px;">
                            ✅ 차량 정보가 확인되었습니다!
                        </div>
                        <div style="font-size: 14px; color: #88a9bf;">
                            <strong>${data.car.model_name}</strong> · ${data.car.manufacturer} · ${data.car.year}
                            <br>연료: ${data.car.fuel_type} · 번호판: ${data.car.license_plate}
                        </div>
                    </div>
                `;
                registerBtn.disabled = false;
                registerBtn.dataset.carId = data.car.id;
            } else {
                resultDiv.style.display = 'block';
                resultDiv.innerHTML = `
                    <div style="padding: 12px; background: rgba(239, 68, 68, 0.1); 
                                border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 8px;">
                        <div style="color: #ef4444; font-weight: 600; margin-bottom: 4px;">
                            ❌ 차량 정보를 찾을 수 없습니다
                        </div>
                        <div style="font-size: 14px; color: #88a9bf;">
                            입력한 정보가 올바른지 확인해주세요.
                        </div>
                    </div>
                `;
                registerBtn.disabled = true;
            }
        } catch (error) {
            UI.toast('차량 정보 확인 중 오류가 발생했습니다.');
        }
    });

    // 차량 등록 완료
    registerBtn.addEventListener('click', async () => {
        const licensePlate = modal.querySelector('#modalLicensePlate').value.trim();
        const vinCode = modal.querySelector('#modalVinCode').value.trim();
        const carId = registerBtn.dataset.carId;

        try {
            const response = await fetch('/api/cars/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ carId: parseInt(carId), licensePlate, vinCode }),
            });

            const data = await response.json();

            if (data.success) {
                UI.toast('🎉 차량이 성공적으로 등록되었습니다!');
                modal.remove();

                // 탭 상태 업데이트 (차량 등록 완료로 인해 지도/제어/스토어 탭 활성화)
                await updateTabsDisabledState();

                // 메인 페이지로 이동
                setTimeout(() => {
                    location.hash = '#/main';
                }, 1000);
            } else {
                UI.toast(data.error || '차량 등록에 실패했습니다.');
            }
        } catch (error) {
            UI.toast('차량 등록 중 오류가 발생했습니다.');
        }
    });
}

export function renderSettings() {
    const root = document.getElementById('view');
    const { token, user } = State.get();

    // --------- 공통 카드(상단) ----------
    const baseCard = document.createElement('div');
    baseCard.className = 'card';
    
    if (!token) {
        // 로그인하지 않은 상태 - 메인 페이지와 동일한 스타일
        baseCard.innerHTML = `
        <div class="body" style="text-align: center; padding: 40px 20px;">
            <p style="color: #88a9bf; margin-bottom: 24px;">
                차량 정보 보기를 위해 로그인 해주세요.
            </p>
            <div style="display: flex; gap: 12px; justify-content: center; flex-wrap: wrap;">
                <button class="btn brand" id="btnOpenLogin2">로그인</button>
                <button class="btn ghost" id="btnRegister">회원가입</button>
            </div>
        </div>
        `;
    } else {
        // 로그인한 상태
        baseCard.innerHTML = `
        <div class="body">
            <div class="kicker">설정</div>
            <div class="cta">
                <div>인증 상태: <b id="authState">로그인됨</b></div>
                <div class="row" style="margin-top:10px; gap: 8px;">
                    <button class="btn brand" id="btnRegisterVehicle">🚗 차량 등록</button>
                    <button class="btn danger" id="btnLogout">로그아웃</button>
                </div>
            </div>
        </div>
        `;
    }

    // 이벤트 바인딩
    if (token) {
        // 로그아웃 버튼
        baseCard.querySelector('#btnLogout')?.addEventListener('click', async () => {
            State.setToken(null);
            State.setUser(null);
            UI.toast('로그아웃 되었습니다.');

            // 탭 상태 업데이트 (로그아웃으로 인해 모든 탭 비활성화)
            await updateTabsDisabledState();

            renderSettings();
        });

        // 차량 등록 버튼
        baseCard.querySelector('#btnRegisterVehicle')?.addEventListener('click', () => {
            showVehicleRegistrationModal();
        });
    } else {
        // 로그인 버튼
        baseCard.querySelector('#btnOpenLogin2')?.addEventListener('click', () => {
            // 상위에서 로그인 모달 열어주는 위임 로직이 있으므로 버튼만 노출
            const evt = new Event('click', { bubbles: true });
            baseCard.querySelector('#btnOpenLogin2').dispatchEvent(evt);
        });
        
        // 회원가입 버튼
        baseCard.querySelector('#btnRegister')?.addEventListener('click', () => {
            // 회원가입 모달 열기 (app.js에서 전역적으로 처리됨)
            document.querySelector('#btnOpenRegister')?.click();
        });
    }
    // --------- 차량 사진 카드(앨범 업로드 & 선택) ----------
    const photoCard = token
        ? (() => {
              const MAX_PHOTOS = 12; // 앨범 최대 개수
              const MAX_FILE_MB = 2; // 권장 파일 크기
              const MIN_W = 320; // 너무 작은 사진 방지
              const MAX_W = 1600; // 리사이즈 상한

              const c = document.createElement('div');
              c.className = 'card';
              c.innerHTML = `
    <div class="body">
      <div class="kicker">차량 사진 앨범</div>

      <div class="grid" style="gap:12px">
        <!-- 메인 프리뷰 -->
        <div class="hero" id="albumHero" style="aspect-ratio:16/9; border-radius:12px; overflow:hidden; background:#0b253a12; display:grid; place-items:center;">
          <!-- 렌더 시 채움 -->
        </div>

        <!-- 업로드/도구줄 -->
        <div class="row" style="gap:8px; flex-wrap:wrap">
          <input id="carPhotoFiles" type="file" accept="image/*" multiple style="display: none;">
          <button class="btn brand" id="btnAddPhotos">📷 사진 추가</button>
          <button class="btn ghost" id="btnClearAll">전체 삭제</button>
          <div class="spacer"></div>
          <div class="muted" id="albumCount"></div>
        </div>

        <!-- 앨범 썸네일 그리드 -->
        <div id="albumGrid" class="product-grid" style="grid-template-columns:repeat(auto-fill,minmax(140px,1fr)); gap:10px;"></div>

        <div class="muted">권장: 가로 ${MAX_W}px 이하 자동 축소 · 파일당 최대 ${MAX_FILE_MB}MB(초과 시 자동 축소 시도)</div>
      </div>
    </div>
  `;

              // 안전 접근자
              // const getUser = () => State.get().user || {};
              // const saveUser = (u) => State.setUser(u);

              // 안전 접근자
              const getUser = () => State.get().user || {};
              const saveUser = (u) => {
                  State.setUser(u);
                  try {
                      const uid = u?.id || State.get().user?.id;
                      if (uid) localStorage.setItem(`cc_user_${uid}`, JSON.stringify(u)); // ✅ 유저별 저장
                      localStorage.setItem('cc_user', JSON.stringify(u)); // 하위호환
                  } catch (e) {}
              };

              // 요소
              const $files = c.querySelector('#carPhotoFiles');
              const $btnAdd = c.querySelector('#btnAddPhotos');
              const $btnClear = c.querySelector('#btnClearAll');
              const $grid = c.querySelector('#albumGrid');
              const $hero = c.querySelector('#albumHero');
              const $count = c.querySelector('#albumCount');

              // ==== 유틸 ====
              const toDataURL = (file) =>
                  new Promise((res, rej) => {
                      const fr = new FileReader();
                      fr.onload = () => res(fr.result);
                      fr.onerror = rej;
                      fr.readAsDataURL(file);
                  });

              const loadImage = (src) =>
                  new Promise((res, rej) => {
                      const i = new Image();
                      i.onload = () => res(i);
                      i.onerror = rej;
                      i.src = src;
                  });

              async function shrinkIfBig(file) {
                  if (!/^image\//.test(file.type)) throw new Error('이미지 파일이 아닙니다.');
                  const raw = await toDataURL(file);
                  const img = await loadImage(raw);
                  if (img.naturalWidth < MIN_W) {
                      throw new Error(`이미지 가로폭이 너무 작습니다(최소 ${MIN_W}px).`);
                  }
                  // 사이즈/폭 조건을 만족하면 그대로 사용
                  if (file.size <= MAX_FILE_MB * 1024 * 1024 && img.naturalWidth <= MAX_W) return raw;

                  // 리사이즈
                  const scale = Math.min(1, MAX_W / img.naturalWidth);
                  const w = Math.round(img.naturalWidth * scale);
                  const h = Math.round(img.naturalHeight * scale);
                  const canvas = document.createElement('canvas');
                  canvas.width = w;
                  canvas.height = h;
                  const ctx = canvas.getContext('2d');
                  ctx.drawImage(img, 0, 0, w, h);
                  // JPEG 재인코딩
                  const out = canvas.toDataURL('image/jpeg', 0.9);
                  return out;
              }

              // 중복 판정: dataURL 동일 시 중복으로 간주
              const isDup = (photos, dataUrl) => photos.some((p) => p.dataUrl === dataUrl);

              // 사용자 사진 데이터 로드 (서버에서)
              async function loadUserPhotos() {
                  const result = await Api.getCarPhotos();
                  if (result.ok) {
                      return result.photos;
                  }
                  return [];
              }

              // 메인 사진 정보 로드
              async function loadMainPhotoInfo() {
                  const result = await Api.getCarPhotos();
                  if (result.ok) {
                      const mainPhoto = result.photos.find((p) => p.id === result.mainPhotoId);
                      return { mainPhoto, mainPhotoId: result.mainPhotoId };
                  }
                  return { mainPhoto: null, mainPhotoId: null };
              }

              // 앨범/메인 렌더
              async function renderGallery() {
                  const photos = await loadUserPhotos();
                  const { mainPhoto, mainPhotoId } = await loadMainPhotoInfo();

                  // hero
                  if (mainPhoto) {
                      $hero.innerHTML = `<img class="hero-img" src="${mainPhoto.url}" alt="메인 차량 사진">`;
                  } else if (photos.length) {
                      $hero.innerHTML = `<img class="hero-img" src="${photos[0].url}" alt="메인 차량 사진 후보">`;
                  } else {
                      $hero.innerHTML = `<div style="color:#88a9bf;font-size:14px">🚘 아직 업로드한 사진이 없습니다</div>`;
                  }

                  // count
                  $count.textContent = `저장된 사진: ${photos.length}/${MAX_PHOTOS}`;

                  // grid
                  $grid.innerHTML = '';
                  photos
                      .slice() // 복사
                      .sort((a, b) => new Date(b.created_at) - new Date(a.created_at)) // 최신순
                      .forEach((p) => {
                          const isMain = mainPhotoId && mainPhotoId === p.id;
                          const el = document.createElement('div');
                          el.className = 'product-card';
                          el.innerHTML = `
          <div class="thumb" style="position:relative; aspect-ratio:1; overflow:hidden; border-radius:10px;">
            <img src="${p.url}" alt="사진" style="width:100%; height:100%; object-fit:cover;">
            ${isMain ? `<div style="position:absolute; top:6px; left:6px; background:#0ba5ec; color:white; font-size:12px; padding:2px 6px; border-radius:8px;">메인</div>` : ''}
          </div>
          <div class="foot" style="display:flex; gap:6px; margin-top:6px;">
            <button class="btn" data-act="setMain" data-id="${p.id}">선택</button>
            <button class="btn ghost" data-act="delete" data-id="${p.id}">삭제</button>
          </div>
          <div class="muted" style="font-size:12px; margin-top:4px;">${new Date(p.created_at).toLocaleString()}</div>
        `;
                          $grid.appendChild(el);
                      });
              }

              // 사진 추가 처리 (파일 리스트)
              async function addPhotosFromFiles(fileList) {
                  const photos = await loadUserPhotos(); // 서버에서 현재 사진 목록 로드

                  // 검증 1: 앨범 용량
                  if (photos.length >= MAX_PHOTOS) {
                      UI.toast(`최대 ${MAX_PHOTOS}장까지 저장할 수 있습니다.`);
                      return;
                  }

                  // 이미지 데이터 배열 준비
                  const imageDataArray = [];

                  for (const file of Array.from(fileList || [])) {
                      if (photos.length + imageDataArray.length >= MAX_PHOTOS) break;

                      try {
                          // 검증 2: 파일 타입
                          if (!/^image\//.test(file.type)) {
                              UI.toast('이미지 파일만 업로드할 수 있습니다.');
                              continue;
                          }

                          // shrink + 검증 3/4/5 포함 (크기/폭/디코드)
                          const dataUrl = await shrinkIfBig(file);
                          imageDataArray.push(dataUrl);
                      } catch (err) {
                          UI.toast(err?.message || '이미지를 처리하지 못했습니다.');
                      }
                  }

                  // 서버에 업로드
                  if (imageDataArray.length > 0) {
                      const result = await Api.uploadCarPhotos(imageDataArray);
                      if (result.ok) {
                          UI.toast(result.message || `${result.uploadedCount}장의 사진이 업로드되었습니다.`);
                          renderGallery(); // 갱신된 사진 목록으로 다시 렌더링
                      } else {
                          UI.toast(result.message || '업로드에 실패했습니다.');
                      }
                  }
              }

              // 이벤트: 추가 버튼
              $btnAdd?.addEventListener('click', () => $files?.click());
              // 파일 선택 시
              $files?.addEventListener('change', async () => {
                  const fl = $files.files;
                  await addPhotosFromFiles(fl);
                  $files.value = ''; // 같은 파일 재선택 허용
              });

              // 이벤트: 앨범 내 버튼들(위임)
              $grid.addEventListener('click', async (e) => {
                  const btn = e.target.closest('button[data-act]');
                  if (!btn) return;

                  const act = btn.getAttribute('data-act');
                  const id = btn.getAttribute('data-id');

                  if (act === 'setMain') {
                      // 메인으로 설정
                      const result = await Api.setMainCarPhoto(id);
                      if (result.ok) {
                          UI.toast(result.message || '메인 사진이 변경되었습니다.');
                          renderGallery();
                      } else {
                          UI.toast(result.message || '메인 사진 설정에 실패했습니다.');
                      }
                  } else if (act === 'delete') {
                      // 삭제 확인
                      if (confirm('이 사진을 삭제하시겠습니까?')) {
                          const result = await Api.deleteCarPhoto(id);
                          if (result.ok) {
                              UI.toast(result.message || '사진을 삭제했습니다.');
                              renderGallery();
                          } else {
                              UI.toast(result.message || '사진 삭제에 실패했습니다.');
                          }
                      }
                  }
              });

              // 전체 삭제
              $btnClear?.addEventListener('click', async () => {
                  const photos = await loadUserPhotos();
                  if (photos.length === 0) {
                      UI.toast('삭제할 사진이 없습니다.');
                      return;
                  }

                  if (confirm(`모든 사진(${photos.length}장)을 삭제하시겠습니까?`)) {
                      const result = await Api.clearAllCarPhotos();
                      if (result.ok) {
                          UI.toast(result.message || '모든 사진을 삭제했습니다.');
                          renderGallery();
                      } else {
                          UI.toast(result.message || '사진 삭제에 실패했습니다.');
                      }
                  }
              });

              // 최초 렌더
              renderGallery();
              return c;
          })()
        : null;

    //   // --------- 차량 사진 카드(업로드) ----------
    //   // ✅ 로그인한 경우에만 렌더 (비로그인시 아예 렌더하지 않아 중복 안내 제거)
    //   const photoCard = token ? (() => {
    //     const MAX_PHOTOS = 12;           // 앨범 최대 개수
    //     const MAX_FILE_MB = 2;           // 권장 파일 크기
    //     const MIN_W = 320;               // 너무 작은 사진 방지
    //     const MAX_W = 1600;              // 리사이즈 상한

    //     const c = document.createElement("div");
    //     c.className = "card";
    //     c.innerHTML = `
    //     <div class="body">
    //       <div class="kicker">차량 사진 앨범</div>

    //       <div class="grid" style="gap:12px">
    //         <!-- 메인 프리뷰 -->
    //         <div class="hero" id="albumHero" style="aspect-ratio:16/9; border-radius:12px; overflow:hidden; background:#0b253a12; display:grid; place-items:center;">
    //           <!-- 렌더 시 채움 -->
    //         </div>

    //         <!-- 업로드/도구줄 -->
    //         <div class="row" style="gap:8px; flex-wrap:wrap">
    //           <input id="carPhotoFiles" type="file" accept="image/*" multiple>
    //           <button class="btn brand" id="btnAddPhotos">추가</button>
    //           <button class="btn ghost" id="btnClearAll">전체 삭제</button>
    //           <div class="spacer"></div>
    //           <div class="muted" id="albumCount"></div>
    //         </div>

    //         <!-- 앨범 썸네일 그리드 -->
    //         <div id="albumGrid" class="product-grid" style="grid-template-columns:repeat(auto-fill,minmax(140px,1fr)); gap:10px;"></div>

    //         <div class="muted">권장: 가로 ${MAX_W}px 이하 자동 축소 · 파일당 최대 ${MAX_FILE_MB}MB(초과 시 자동 축소 시도)</div>
    //       </div>
    //     </div>
    //   `;
    //     // c.innerHTML = `
    //     //   <div class="body">
    //     //     <div class="kicker">메인 화면 차량 사진</div>
    //     //     <div class="grid" style="gap:12px">
    //     //       <div class="hero" style="aspect-ratio:16/9; border-radius:12px; overflow:hidden;">
    //     //         ${user?.carPhotoData
    //     //           ? `<img id="carPhotoPreview" class="hero-img" src="${user.carPhotoData}" alt="차량 사진">`
    //     //           : `<div id="carPhotoEmpty" class="hero-img" style="display:grid;place-items:center;color:#88a9bf;font-size:14px">🚘 아직 업로드한 사진이 없습니다</div>`
    //     //         }
    //     //       </div>

    //     //       <div class="row" style="gap:8px; flex-wrap:wrap">
    //     //         <input id="carPhotoFile" type="file" accept="image/*">
    //     //         <button class="btn brand" id="btnSaveCarPhoto">저장</button>
    //     //         <button class="btn ghost" id="btnRemoveCarPhoto" ${user?.carPhotoData ? "" : "disabled"}>삭제</button>
    //     //       </div>
    //     //       <div class="muted">권장: 가로 1200px 이상 · 최대 2MB (초과시 자동 축소 저장)</div>
    //     //     </div>
    //     //   </div>
    //     // `;

    //     // 안전 접근자
    //     const getUser = () => State.get().user || {};
    //     const saveUser = (u) => State.setUser(u);

    //     // 업로드 로직
    //     // const $file = c.querySelector("#carPhotoFile");
    //     // const $btnSave = c.querySelector("#btnSaveCarPhoto");
    //     // const $btnDel  = c.querySelector("#btnRemoveCarPhoto");
    //     // const $hero    = c.querySelector(".hero");
    //     // let stagedDataUrl = null;

    //     const $files = c.querySelector("#carPhotoFiles");
    //     const $btnAdd = c.querySelector("#btnAddPhotos");
    //     const $btnClear = c.querySelector("#btnClearAll");
    //     const $grid = c.querySelector("#albumGrid");
    //     const $hero = c.querySelector("#albumHero");
    //     const $count = c.querySelector("#albumCount");

    //     function toDataURL(file){
    //       return new Promise((res, rej)=>{
    //         const fr = new FileReader();
    //         fr.onload = () => res(fr.result);
    //         fr.onerror = rej;
    //         fr.readAsDataURL(file);
    //       });
    //     }
    //     async function shrinkIfBig(file){
    //       if (!/^image\//.test(file.type)) return toDataURL(file);
    //       if (file.size <= 2 * 1024 * 1024) return toDataURL(file);
    //       const img = await new Promise((res, rej)=>{
    //         const i = new Image(); i.onload = ()=>res(i); i.onerror = rej;
    //         i.src = URL.createObjectURL(file);
    //       });
    //       const maxW = 1600;
    //       const scale = Math.min(1, maxW / img.naturalWidth);
    //       const w = Math.round(img.naturalWidth * scale);
    //       const h = Math.round(img.naturalHeight * scale);
    //       const canvas = document.createElement("canvas");
    //       canvas.width = w; canvas.height = h;
    //       const ctx = canvas.getContext("2d");
    //       ctx.drawImage(img, 0, 0, w, h);
    //       return canvas.toDataURL("image/jpeg", 0.9);
    //     }

    //     $file?.addEventListener("change", async ()=>{
    //       const f = $file.files?.[0]; if (!f) return;
    //       try{
    //         const dataUrl = await shrinkIfBig(f);
    //         stagedDataUrl = dataUrl;
    //         $hero.innerHTML = `<img id="carPhotoPreview" class="hero-img" src="${dataUrl}" alt="차량 사진">`;
    //         $btnDel.disabled = false;
    //         UI.toast("미리보기가 업데이트되었습니다.");
    //     });

    //     $btnSave?.addEventListener("click", ()=>{
    //       const cur = State.get().user || {};
    //       const nextData = stagedDataUrl ?? cur.carPhotoData;
    //       if (!nextData){ UI.toast("먼저 파일을 선택하세요."); return; }
    //       State.setUser({ ...cur, carPhotoData: nextData });
    //       UI.toast("차량 사진이 저장되었습니다. 메인에서 확인해보세요.");
    //     });

    //     $btnDel?.addEventListener("click", ()=>{
    //       const cur = State.get().user || {};
    //       State.setUser({ ...cur, carPhotoData: null });
    //       stagedDataUrl = null;
    //       $hero.innerHTML = `<div id="carPhotoEmpty" class="hero-img" style="display:grid;place-items:center;color:#88a9bf;font-size:14px">🚘 아직 업로드한 사진이 없습니다</div>`;
    //       $btnDel.disabled = true;
    //       UI.toast("차량 사진이 삭제되었습니다.");
    //     });

    //     c.querySelector("#btnGoMain")?.addEventListener("click", ()=>{ location.hash = "#/main"; });
    //     return c;
    //   })() : null;


    // --------- 렌더링 ----------
    root.innerHTML = '';
    root.appendChild(baseCard);
    if (photoCard) root.appendChild(photoCard); // 로그인 상태에서만 사진 카드 추가

    // 탭 상태 업데이트 (차량 등록 상태 변경 시 탭 활성화/비활성화)
    updateTabsDisabledState();
}

