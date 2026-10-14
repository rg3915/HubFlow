import { defineStore } from 'pinia'
import { api } from '../api'
import { useAuthStore } from './auth'

export const useBoardStore = defineStore('board', {
  state: () => ({ projectId: null, project: null, columns: [], loading: false }),
  actions: {
    async load(projectId, { archived = false } = {}) {
      const token = useAuthStore().token
      this.loading = true
      try {
        const board = await api(`/projects/${projectId}/board?archived=${archived}`, { token })
        this.projectId = projectId
        this.project = board.project
        this.columns = board.columns
      } finally {
        this.loading = false
      }
    },
  },
})
