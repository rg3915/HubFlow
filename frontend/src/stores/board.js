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
    column(key) {
      return this.columns.find((c) => c.key === key)
    },
    // Aplica a mudança na hora e confirma com a API; se falhar, recarrega o quadro.
    async move(cardId, fromKey, toKey, position) {
      const from = this.column(fromKey)
      const [card] = from.cards.splice(from.cards.findIndex((c) => c.id === cardId), 1)
      card.column = toKey
      this.column(toKey).cards.splice(position, 0, card)
      try {
        await api(`/cards/${cardId}/move`, {
          method: 'POST',
          body: { column: toKey, position },
          token: useAuthStore().token,
        })
      } catch (e) {
        await this.load(this.projectId)
        throw e
      }
    },
  },
})
