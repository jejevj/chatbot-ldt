/**
 * Auth Store — simpan JWT token admin di localStorage
 */
import { reactive, computed } from 'vue'

const TOKEN_KEY = 'bo_admin_token'
const USER_KEY  = 'bo_admin_user'

const state = reactive({
  token: localStorage.getItem(TOKEN_KEY) || null,
  user:  JSON.parse(localStorage.getItem(USER_KEY) || 'null'),
})

export const authStore = {
  // --- getters ---
  get token()     { return state.token },
  get user()      { return state.user },
  get isLoggedIn(){ return !!state.token },

  // --- actions ---
  login(token, user) {
    state.token = token
    state.user  = user
    localStorage.setItem(TOKEN_KEY, token)
    localStorage.setItem(USER_KEY, JSON.stringify(user))
  },

  logout() {
    state.token = null
    state.user  = null
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
  },
}
