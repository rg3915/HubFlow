import { defineStore } from 'pinia'
import { api } from '../api'

export const useAuthStore = defineStore('auth', {
  state: () => ({ token: localStorage.getItem('token'), user: null }),
  getters: { isLoggedIn: (state) => Boolean(state.token) },
  actions: {
    async login(email, password) {
      const { token } = await api('/auth/login', { method: 'POST', body: { email, password } })
      this.token = token
      localStorage.setItem('token', token)
    },
    async fetchUser() {
      this.user = await api('/auth/me', { token: this.token })
    },
    async logout() {
      await api('/auth/logout', { method: 'POST', token: this.token }).catch(() => {})
      this.token = null
      this.user = null
      localStorage.removeItem('token')
    },
  },
})
