// api.js - API facade (now using real BE for auth)
import { MockApi } from "./mockApi.js";

const BASE_URL = "";

// Real BE API calls
const RealApi = {
  async login(username, password) {
    try {
      const response = await fetch(`${BASE_URL}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ username, password })
      });
      
      const data = await response.json();
      if (data.status === 'success') {
        return { 
          ok: true, 
          token: 'session-based', 
          user: { 
            id: data.user.username, 
            name: data.user.name,
            hasCar: true,
            car: { model: "GRANDEUR", plate: "12가 3456", color: "#79d1ff", imageUrl: "/static/assets/cars/USER1_GRANDEUR.jpg" }
          } 
        };
      } else {
        return { ok: false, message: data.error || '로그인 실패' };
      }
    } catch (error) {
      return { ok: false, message: '서버 연결 실패' };
    }
  },

  async register(username, password, name, email, phone) {
    try {
      const response = await fetch(`${BASE_URL}/api/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ username, password, name, email, phone })
      });
      
      const data = await response.json();
      if (data.status === 'success') {
        return { ok: true, user_id: data.user_id };
      } else {
        return { ok: false, message: data.error || '회원가입 실패' };
      }
    } catch (error) {
      return { ok: false, message: '서버 연결 실패' };
    }
  },

  async me() {
    try {
      const response = await fetch(`${BASE_URL}/api/auth/me`, {
        credentials: 'include'
      });
      
      const data = await response.json();
      if (data.status === 'success') {
        return { 
          ok: true, 
          user: { 
            id: data.user.username, 
            name: data.user.name,
            hasCar: true,
            car: { model: "GRANDEUR", plate: "12가 3456", color: "#79d1ff", imageUrl: "/static/assets/cars/USER1_GRANDEUR.jpg" }
          }
        };
      } else {
        return { ok: false };
      }
    } catch (error) {
      return { ok: false };
    }
  }
};

export const Api = {
  // Use real BE for authentication
  login: RealApi.login,
  register: RealApi.register,
  me: RealApi.me,
  
  // Keep mock for other features for now
  setHasCar: MockApi.setHasCar,
  recommendedPlaces: MockApi.recommendedPlaces,
  vehicleStatus: MockApi.vehicleStatus,
  vehicleControl: MockApi.vehicleControl,
  controlLogs: MockApi.controlLogs,           // 제어 로그 조회
  controlLogsClear: MockApi.controlLogsClear, // 제어 로그 초기화
  storeNew: MockApi.storeNew,
  storeUsedList: MockApi.storeUsedList,
  storeUsedCreate: MockApi.storeUsedCreate,
  cardsList: MockApi.cardsList,
  cardSelect: MockApi.cardSelect,
  cardsAddTest: MockApi.cardsAddTest,
  purchase: MockApi.purchase,
};
