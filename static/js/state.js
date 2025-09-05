// state.js - simple localStorage-backed state
const KEY_TOKEN = 'cc_token';
const KEY_USER = 'cc_user';
const KEY_SELECTED_CAR_ID = 'cc_selected_car_id';

export const State = {
    get() {
        const token = localStorage.getItem(KEY_TOKEN) || null;
        let user = null;
        try {
            user = JSON.parse(localStorage.getItem(KEY_USER) || 'null');
        } catch (e) {
            user = null;
        }
        const selectedCarId = localStorage.getItem(KEY_SELECTED_CAR_ID) ? parseInt(localStorage.getItem(KEY_SELECTED_CAR_ID)) : null;
        return { token, user, selectedCarId };
    },
    setToken(t) {
        if (t) localStorage.setItem(KEY_TOKEN, t);
        else localStorage.removeItem(KEY_TOKEN);
    },
    setUser(u) {
        if (u) localStorage.setItem(KEY_USER, JSON.stringify(u));
        else localStorage.removeItem(KEY_USER);
    },
    setSelectedCarId(carId) {
        if (carId) localStorage.setItem(KEY_SELECTED_CAR_ID, carId.toString());
        else localStorage.removeItem(KEY_SELECTED_CAR_ID);
    },
    get selectedCarId() {
        const id = localStorage.getItem(KEY_SELECTED_CAR_ID);
        return id ? parseInt(id) : null;
    },
    set selectedCarId(carId) {
        this.setSelectedCarId(carId);
    },
};
