import { defineStore } from 'pinia'
import { api } from '../api'

export const useAuthStore = defineStore('auth', {
  state: () => ({ token: localStorage.getItem('token'), user: null }),
  getters: {
    isLoggedIn: (state) => Boolean(state.token),
    // Permissões efetivas vêm de /auth/me (papéis + por pessoa); a API continua sendo quem decide.
    can: (state) => (perm) => Boolean(state.user?.permissions?.includes(perm)),
    seesPayments() {
      return this.can('billing.view_payment') || this.can('permissions.view_own_payments')
    },
    isCardOwner: (state) => (card) => [card?.created_by?.id, card?.assignee?.id].includes(state.user?.id),
    canEditCard() {
      return (card) => this.can('boards.change_card') || this.isCardOwner(card)
    },
    canDeleteCard() {
      return (card) => this.can('boards.delete_card') || this.isCardOwner(card)
    },
  },
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
