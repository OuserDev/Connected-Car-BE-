// state.js - simple localStorage-backed state
const KEY_TOKEN = "cc_token";
const KEY_USER  = "cc_user";

export const State = {
  get(){ 
    const token = localStorage.getItem(KEY_TOKEN) || null;
    let user = null;
    try {
      user = JSON.parse(localStorage.getItem(KEY_USER) || "null");
    } catch(e) {
      user = null;
    }
    return { token, user }; 
  },
  setToken(t){ 
    if(t) localStorage.setItem(KEY_TOKEN, t); 
    else localStorage.removeItem(KEY_TOKEN); 
  },
  setUser(u){ 
    if(u) localStorage.setItem(KEY_USER, JSON.stringify(u)); 
    else localStorage.removeItem(KEY_USER); 
  },
};
