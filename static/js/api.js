// api.js - API facade (mock for now)
import { MockApi } from "./mockApi.js";

export const Api = {
  login: MockApi.login,
  me: MockApi.me,
  setHasCar: MockApi.setHasCar,
  recommendedPlaces: MockApi.recommendedPlaces,
  vehicleStatus: MockApi.vehicleStatus,
  vehicleControl: MockApi.vehicleControl,
  storeNew: MockApi.storeNew,                 // 새 상품 목록
  storeUsedList: MockApi.storeUsedList,       // 중고글 목록
  storeUsedCreate: MockApi.storeUsedCreate,   // 중고글 작성
  cardsList: MockApi.cardsList,               // 결제카드 목록(마스킹)
  cardSelect: MockApi.cardSelect,             // 결제카드 선택
  cardsAddTest: MockApi.cardsAddTest,         // 테스트 카드 추가
  purchase: MockApi.purchase,                 // 구매(데모)
};
