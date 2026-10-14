import { defineStore } from 'pinia'
import { api } from '../api'
import { useAuthStore } from './auth'

export const useClientsStore = defineStore('clients', {
  state: () => ({ clients: [], projects: [], loaded: false }),
  getters: {
    // Barra lateral: Cliente → Projetos
    tree: (state) =>
      state.clients.map((client) => ({
        ...client,
        projects: state.projects.filter((p) => p.client_id === client.id),
      })),
  },
  actions: {
    async load() {
      const token = useAuthStore().token
      ;[this.clients, this.projects] = await Promise.all([api('/clients', { token }), api('/projects', { token })])
      this.loaded = true
    },
    async saveClient(id, data) {
      const token = useAuthStore().token
      const saved = id
        ? await api(`/clients/${id}`, { method: 'PUT', body: data, token })
        : await api('/clients', { method: 'POST', body: data, token })
      await this.load()
      return saved
    },
    async saveProject(id, data) {
      const token = useAuthStore().token
      const saved = id
        ? await api(`/projects/${id}`, { method: 'PUT', body: data, token })
        : await api('/projects', { method: 'POST', body: data, token })
      await this.load()
      return saved
    },
  },
})
