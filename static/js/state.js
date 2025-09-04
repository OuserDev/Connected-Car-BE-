// state.js - simple localStorage-backed state
const KEY_TOKEN = "cc_token";
const KEY_USER  = "cc_user";

let _token = localStorage.getItem(KEY_TOKEN) || null;
let _user  = JSON.parse(localStorage.getItem(KEY_USER) || "null");

export const State = {
  get(){ return { token:_token, user:_user }; },
  setToken(t){ _token = t; if(t) localStorage.setItem(KEY_TOKEN, t); else localStorage.removeItem(KEY_TOKEN); },
  setUser(u){ _user = u; if(u) localStorage.setItem(KEY_USER, JSON.stringify(u)); else localStorage.removeItem(KEY_USER); },
};
