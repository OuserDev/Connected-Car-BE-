// mockApi.js - local demo-only API with coordinates for real map
const delay = (ms=200) => new Promise(r=>setTimeout(r,ms));
// 하드코딩된 이미지 경로 제거 - 실제 차량 이미지는 model_id 기반으로 처리
const DEFAULT_CAR_IMAGE = null;

// mockApi.js 상단 근처
const userKey = (id) => `cc_user_${id}`;
// ✅ 제어 로그 (유저별 보관)
const KEY_CTRL_LOGS = "ctrl_logs";
const _logsKey = () => {
  const uid = localStorage.getItem("cc_user_id") || "guest";
  return `${KEY_CTRL_LOGS}_${uid}`;
};
function _readLogs(){ try{ return JSON.parse(localStorage.getItem(_logsKey()) || "[]"); }catch{ return []; } }
function _writeLogs(list){ localStorage.setItem(_logsKey(), JSON.stringify(list)); }
function _pushLog(entry){
  const list = _readLogs();
  list.push({ id: "log_"+Date.now()+"_"+Math.random().toString(36).slice(2,6), ...entry });
  // (선택) 500개 초과 시 오래된 것 제거
  if(list.length > 500) list.splice(0, list.length - 500);
  _writeLogs(list);
}


// ✅ 제어 상태 로컬스토리지 유틸
const CTL_KEY = "cc_control";
function _readControl(){
  const d = JSON.parse(localStorage.getItem(CTL_KEY) || "null");
  return d || { locked:true, engineOn:false, acOn:false, targetTemp:22 };
}
function _writeControl(s){ localStorage.setItem(CTL_KEY, JSON.stringify(s)); }
function _actionMsg(a, s){
  switch(a){
    case "lock": return "🔒 문을 잠갔습니다.";
    case "unlock": return "🔓 문을 열었습니다.";
    case "engineOn": return "▶️ 시동을 켰습니다.";
    case "engineOff": return "⏹️ 시동을 껐습니다.";
    case "horn": return "📣 경적을 울렸습니다.";
    case "flash": return "💡 비상등 점멸.";
    case "acOn": return "❄️ 에어컨을 켰습니다.";
    case "acOff": return "🛑 에어컨을 껐습니다.";
    case "setTemp": return `🌡️ 목표온도 ${s.targetTemp}℃`;
    default: return "처리되었습니다.";
  }
}

// ===== STORE / PAYMENT (mock) =====
const KEY_NEW   = "store_new";
const KEY_USED  = "store_used";
const KEY_CARDS = "store_cards";
const KEY_CARD_SEL = "store_active_card";

function _seedNew(){
  if(localStorage.getItem(KEY_NEW)) return;
  const items = [
    {id:"n1", title:"IoT 블랙박스",   price:179000, img:"📷", desc:"주행영상+이벤트 감지"},
    {id:"n2", title:"공기청정기 모듈", price:129000, img:"🌬️", desc:"초미세먼지 자동제거"},
    {id:"n3", title:"차량용 냉온컵",   price:59000,  img:"🥤", desc:"냉/온 듀얼 컵홀더"},
    {id:"n4", title:"부스터 충전기",   price:39000,  img:"⚡", desc:"PD 45W 듀얼 포트"},
  ];
  localStorage.setItem(KEY_NEW, JSON.stringify(items));
}
function _seedCards(){
  if(localStorage.getItem(KEY_CARDS)) return;
  const cards = [
    { id:"c_test_1", brand:"VISA", last4:"4242", exp:"12/30", holder:"DEMO USER",
      isTest:true, fullNumber:"4242 4242 4242 4242" },
    { id:"c_real_1", brand:"Mastercard", last4:"0077", exp:"03/28", holder:"홍길동",
      isTest:false } // 실제 카드는 절대 전체번호를 저장/표시하지 않음
  ];
  localStorage.setItem(KEY_CARDS, JSON.stringify(cards));
  localStorage.setItem(KEY_CARD_SEL, "c_test_1");
}
function _read(k, def){ try{ return JSON.parse(localStorage.getItem(k)||"null") ?? def; }catch{ return def; } }
function _write(k, v){ localStorage.setItem(k, JSON.stringify(v)); }

export const MockApi = {
//   async login(id, pw){
//     await delay();
//     if(id === "admin" && pw === "passwd"){
//       const user = {
//         id: "admin",
//         name: "Admin",
//         hasCar: true,
//         car: { model: "GRANDEUR", plate: "12가 3456", color: "#79d1ff" }
//       };
//       localStorage.setItem("cc_user", JSON.stringify(user));
//       localStorage.setItem("cc_token", "demo-token");
//       return { ok:true, token:"demo-token", user };
//     }
//     return { ok:false, message:"아이디 또는 비밀번호가 올바르지 않습니다." };
//   },
  async login(id, pw){
    await delay();
    if (id === "admin" && pw === "passwd") {
      const uid = "admin"; // 여러 계정 지원 시 로그인 ID를 uid로 사용
      const prev = JSON.parse(localStorage.getItem(userKey(uid)) || "null") || {};
  
      const base = {
        id: uid,
        name: "Admin",
        hasCar: true,
        car: { model: "GRANDEUR", plate: "12가 3456", color: "#79d1ff" }
      };
  
      const preserve = {
        carPhotoData: prev.carPhotoData ?? null,
        carPhotos: Array.isArray(prev.carPhotos) ? prev.carPhotos : []
      };
  
      const user = { ...base, ...prev, car: { ...base.car, ...(prev.car || {}) }, ...preserve };
  
      // ✅ 유저별로 저장 + 현재 로그인한 유저 id도 저장
      localStorage.setItem(userKey(uid), JSON.stringify(user));
      localStorage.setItem("cc_user_id", uid);
      localStorage.setItem("cc_user", JSON.stringify(user)); // 하위호환용
      localStorage.setItem("cc_token", "demo-token");
      return { ok:true, token:"demo-token", user };
    }
    return { ok:false, message:"아이디 또는 비밀번호가 올바르지 않습니다." };
  },


  async me(token){
  await delay(100);
  if (token === "demo-token"){
      const uid = localStorage.getItem("cc_user_id");
      const saved = uid ? JSON.parse(localStorage.getItem(userKey(uid)) || "null") : null;
      if (saved){
      if (!saved.car) saved.car = {};
      if (!saved.car.imageUrl) saved.car.imageUrl = DEFAULT_CAR_IMAGE;
      // 하위호환용으로 cc_user도 최신화
      localStorage.setItem("cc_user", JSON.stringify(saved));
      return { ok:true, user: saved };
      }
  }
  return { ok:false };
  },

  async setHasCar(hasCar){
  const uid = localStorage.getItem("cc_user_id");
  const key = uid ? userKey(uid) : "cc_user";
  const u = JSON.parse(localStorage.getItem(key) || "{}");
  u.hasCar = !!hasCar;
  if (u.hasCar) {
      u.car = u.car || {};
      u.car.imageUrl = u.car.imageUrl || DEFAULT_CAR_IMAGE;
  }
  localStorage.setItem(key, JSON.stringify(u));
  localStorage.setItem("cc_user", JSON.stringify(u)); // 하위호환
  return { ok:true, user:u };
  },


  // ✅ 상태 조회: 제어 상태(잠금/시동/공조/목표온도) 병합
  async vehicleStatus(){
    await delay(120);
    const ctl = _readControl();
    const base = 312; const jitter = Math.floor(Math.random()*6)-3;
    const battery = 78 + (Math.floor(Math.random()*5)-2);

    return {
      ok:true,
      status:{
        rangeKm: Math.max(0, base + jitter),
        batteryPct: Math.max(0, Math.min(100, battery)),
        charging: false,
        outsideTemp: 24,
        cabinTemp: ctl.acOn ? (ctl.targetTemp + (Math.random() * 2 - 1)) : (28 + (Math.random() * 4 - 2)),  // 약간의 변동 추가
        cabinTempTarget: ctl.targetTemp,
        targetTemp: ctl.targetTemp,  // 추가: 일관성을 위해
        locked: ctl.locked,
        engineOn: ctl.engineOn,
        acOn: ctl.acOn,
        fuel: 75,  // 연료 정보 추가
        battery: Math.max(0, Math.min(100, battery)) / 100 * 12.6,  // 배터리 전압으로 변환
      }
    };
  },

  // ✅ 제어: 액션 적용 후 최신 상태 반환
  async vehicleControl(action, data = {}){
    await delay(180);
    const ctl = _readControl();

    let ok = true;
    let message = "";

    switch(action){
      case "lock":     ctl.locked = true; break;
      case "unlock":   ctl.locked = false; break;
      case "engineOn":  ctl.engineOn = true; break;
      case "engineOff": ctl.engineOn = false; break;
      case "horn":   /* no state change */ break;
      case "flash":  /* no state change */ break;
      case "acOn":   ctl.acOn = true; break;
      case "acOff":  ctl.acOn = false; break;
      case "setTemp":
        if (typeof data.target === "number"){
          ctl.targetTemp = Math.max(16, Math.min(30, Math.round(data.target)));
        }
        break;

      // ✅ 단일 퀵액션: 한 번 호출 = 로그 1건
      case "acLow":
        ctl.acOn = true;
        ctl.targetTemp = 18;
        break;

      default:
        ok = false;
        message = "알 수 없는 제어 요청입니다.";
    }

    if (!ok){
      _pushLog({ ts: Date.now(), action, ok:false, message, data: data||null });
      return { ok:false, message };
    }

    _writeControl(ctl);
    const vs = await this.vehicleStatus(); // 최신 상태
    message = _actionMsg(action, ctl);

    // ✅ 성공 로그 적재 (액션당 1줄)
    _pushLog({ ts: Date.now(), action, ok:true, message, data: data||null });

    return {
      ok:true,
      message,
      status: vs.status
    };
  },
  async recommendedPlaces(){
    await delay(150);
    return {
      ok:true,
      items:[
        {name:"한강 공원(반포)", tag:"야외/피크닉", dist:"3.1km", lat:37.5099, lng:126.9983},
        {name:"성수 카페 거리", tag:"카페/브런치", dist:"5.4km", lat:37.5436, lng:127.0547},
        {name:"남산 N타워",     tag:"전망/야경",   dist:"4.8km", lat:37.5512, lng:126.9882},
        {name:"현대 모터스튜디오", tag:"모빌리티",  dist:"2.5km", lat:37.5253, lng:127.0418},
      ]
    };
  },


  

  async storeNew(){
    _seedNew(); await delay(80);
    return { ok:true, items:_read(KEY_NEW, []) };
  },
  async storeUsedList(){
    await delay(80);
    const list = _read(KEY_USED, []);
    // 최신순
    list.sort((a,b)=>b.createdAt - a.createdAt);
    return { ok:true, items:list };
  },
  async storeUsedCreate({ title, body, price, photoData }){
    await delay(150);
    if(!title || !price) return { ok:false, message:"제목과 금액은 필수입니다." };
    const list = _read(KEY_USED, []);
    const item = {
      id:"u_"+Date.now(),
      title:String(title).slice(0,80),
      body:String(body||"").slice(0,2000),
      price: Number(price)||0,
      photoData: photoData || null,
      createdAt: Date.now(),
      seller:"나",
    };
    list.push(item); _write(KEY_USED, list);
    return { ok:true, item };
  },

  async cardsList(){
    _seedCards(); await delay(60);
    return { ok:true, cards:_read(KEY_CARDS, []), activeId: localStorage.getItem(KEY_CARD_SEL) };
  },
  async cardSelect(id){
    await delay(60);
    const cards = _read(KEY_CARDS, []);
    if(!cards.find(c=>c.id===id)) return { ok:false, message:"카드를 찾을 수 없습니다." };
    localStorage.setItem(KEY_CARD_SEL, id);
    return { ok:true, activeId:id };
  },

  // 새 카드 추가 (민감정보는 저장하지 않음)
  async cardsAdd({ brand, holder, exp, last4, isTest = false, setDefault = false }) {
    await delay(80);
    _seedCards();
    const cards = _read(KEY_CARDS, []);

    // === 서버측(모의) 검증 6가지 ===
    // 1) 이름
    if (!holder || String(holder).trim().length < 2) {
      return { ok: false, message: "이름을 정확히 입력해주세요." };
    }
    // 2) 유효기간 형식
    if (!/^\d{2}\/\d{2}$/.test(exp || "")) {
      return { ok: false, message: "유효기간 형식이 올바르지 않습니다. (MM/YY)" };
    }
    // 3) 월(MM) 범위
    const mm = parseInt(exp.slice(0, 2), 10);
    const yy = parseInt(exp.slice(3, 5), 10);
    if (mm < 1 || mm > 12) {
      return { ok: false, message: "유효기간의 월(MM)이 올바르지 않습니다." };
    }
    // 4) 만료 여부
    const now = new Date();
    const fullY = 2000 + yy;
    const curY = now.getFullYear();
    const curM = now.getMonth() + 1;
    if (fullY < curY || (fullY === curY && mm < curM)) {
      return { ok: false, message: "이미 만료된 카드입니다." };
    }
    // 5) last4 형식
    const digitsLast4 = String(last4 || "").replace(/\D/g, "");
    if (digitsLast4.length !== 4) {
      return { ok: false, message: "카드 끝 4자리가 올바르지 않습니다." };
    }
    // 6) 중복 등록 방지 (last4 + exp + holder 동일)
    if (cards.some((c) => c.last4 === digitsLast4 && c.exp === exp && c.holder === holder)) {
      return { ok: false, message: "이미 등록된 카드입니다." };
    }

    // 민감정보(full PAN, CVC)는 저장 금지(모의 환경에서도 버림)
    const id = "c_" + Math.random().toString(36).slice(2, 10);
    cards.push({
      id,
      brand: brand || "CARD",
      last4: digitsLast4,
      exp,
      holder,
      isTest: !!isTest
      // fullNumber, cvc는 저장하지 않음
    });
    _write(KEY_CARDS, cards);

    if (setDefault) {
      localStorage.setItem(KEY_CARD_SEL, id);
    }
    const activeId = localStorage.getItem(KEY_CARD_SEL) || id;

    return { ok: true, cards, activeId };
  },


  async cardsAddTest(){
    await delay(80);
    const cards = _read(KEY_CARDS, []);
    const id = "c_test_"+(1+cards.filter(c=>c.isTest).length);
    cards.push({
      id, brand:"VISA", last4:"4242", exp:"12/30", holder:"DEMO USER",
      isTest:true, fullNumber:"4242 4242 4242 4242"
    });
    _write(KEY_CARDS, cards);
    return { ok:true, cards, activeId:id };
  },

  async purchase(productId){
    await delay(200);
    const items = _read(KEY_NEW, []);
    const item = items.find(i=>i.id===productId);
    if(!item) return { ok:false, message:"상품을 찾을 수 없습니다." };
    const activeId = localStorage.getItem(KEY_CARD_SEL);
    const cards = _read(KEY_CARDS, []);
    const card = cards.find(c=>c.id===activeId);
    if(!card) return { ok:false, message:"결제 카드를 선택해주세요." };
    // 데모이므로 결제 처리 없이 성공 응답
    return { ok:true, message:`구매 완료: ${item.title} · 카드 **** **** **** ${card.last4}` };
  },
  
  async controlLogs(limit = 200){
    await delay(60);
    let list = _readLogs();

    // 첫 조회가 비어있으면 더미 2줄 자동 시드(한번만)
    if (!list.length) {
      const now = Date.now();
      list = [
        { id:`seed_${now}_1`, ts: now - 1000*60*2, action:"unlock",  ok:true, message:"🔓 문을 열었습니다.", data:null },
        { id:`seed_${now}_2`, ts: now - 1000*60*1, action:"setTemp", ok:true, message:"🌡️ 목표온도 18℃",   data:{target:18} },
      ];
      _writeLogs(list);
    }

    const items = list.slice().sort((a,b)=> b.ts - a.ts).slice(0, limit);
    return { ok:true, items };
  },

  async controlLogsClear(){
    await delay(60);
    _writeLogs([]);
    return { ok:true };
  },


};