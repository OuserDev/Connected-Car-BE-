// core/shared.js
import { State } from "../state.js";

export function getRoot(){
  return document.getElementById("view");
}
export function getScrim(){
  return document.getElementById("dlgScrim");
}

/* NAVER Maps 로드 대기 */
export function waitForNaver(maxMs = 4000){
  return new Promise((resolve, reject)=>{
    const t0 = Date.now();
    (function loop(){
      if (window.naver && naver.maps) return resolve();
      if (Date.now() - t0 > maxMs) return reject(new Error("NAVER Maps 로드를 확인하지 못했습니다."));
      requestAnimationFrame(loop);
    })();
  });
}

/* 하단 탭 활성화 표시 */
export function setActiveTabByHash(){
  const map = { "#/main":"0", "#/map":"1", "#/control":"2", "#/store":"3", "#/settings":"4" };
  const idx = map[location.hash] ?? "0";
  document.querySelectorAll(".tab").forEach(t=>{
    const active = t.dataset.index === idx;
    t.dataset.active = active ? "true" : "false";
    t.setAttribute("aria-selected", active ? "true" : "false");
  });
}

/* 헤더 배지 갱신 */
export function updateAuthBadge(){
  const { token, user } = State.get();
  const badge = document.getElementById("badgeAuth");
  const logoutBtn = document.getElementById("btnLogout");
  
  if (badge) {
    if (token) {
      badge.textContent = `환영합니다. ${user?.name || "사용자"}님`;
      badge.title = "클릭하여 프로필 수정";
      logoutBtn.style.display = "block";
    } else {
      badge.textContent = "로그인";
      badge.title = "클릭하여 로그인";
      logoutBtn.style.display = "none";
    }
  }
  
  // 헤더 차량 정보도 함께 업데이트
  updateHeaderVehicleInfo();
}

/* 헤더 중앙 차량 정보 업데이트 */
export async function updateHeaderVehicleInfo(){
  const { token, selectedCarId } = State.get();
  const headerVehicleInfo = document.getElementById("headerVehicleInfo");
  const headerVehicleModel = document.getElementById("headerVehicleModel");
  const headerVehiclePlate = document.getElementById("headerVehiclePlate");
  
  if (!headerVehicleInfo || !headerVehicleModel || !headerVehiclePlate) return;
  
  if (!token) {
    // 로그인하지 않은 경우 차량 정보 숨기기
    headerVehicleInfo.style.display = "none";
    return;
  }
  
  if (!selectedCarId) {
    // 선택된 차량이 없는 경우 차량 정보 숨기기
    headerVehicleInfo.style.display = "none";
    return;
  }
  
  try {
    // 사용자의 차량 목록 가져오기
    const response = await fetch('/api/cars', { credentials: 'include' });
    if (response.ok) {
      const data = await response.json();
      if (data.success && data.data && data.data.length > 0) {
        // 선택된 차량 찾기
        const selectedCar = data.data.find(car => car.id === selectedCarId);
        if (selectedCar) {
          headerVehicleModel.textContent = selectedCar.model_name || selectedCar.model || '차량';
          headerVehiclePlate.textContent = selectedCar.license_plate || selectedCar.licensePlate || '번호판 미등록';
          headerVehicleInfo.style.display = "block";
        } else {
          headerVehicleInfo.style.display = "none";
        }
      } else {
        headerVehicleInfo.style.display = "none";
      }
    } else {
      headerVehicleInfo.style.display = "none";
    }
  } catch (error) {
    console.error('헤더 차량 정보 업데이트 실패:', error);
    headerVehicleInfo.style.display = "none";
  }
}
