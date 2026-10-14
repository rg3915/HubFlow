import { defineStore } from 'pinia'
import { api } from '../api'
import { useAuthStore } from './auth'

export const useBoardStore = defineStore('board', {
  state: () => ({ projectId: null, project: null, columns: [], loading: false, selected: null }),
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
    async createCard(title) {
      const token = useAuthStore().token
      const card = await api(`/projects/${this.projectId}/cards`, { method: 'POST', body: { title }, token })
      this.column('backlog').cards.push(card)
      return card
    },
    async updateCard(card, data) {
      const token = useAuthStore().token
      const saved = await api(`/cards/${card.id}`, { method: 'PUT', body: data, token })
      Object.assign(card, saved)
      return saved
    },
    async archiveCard(card) {
      await this.move(card.id, card.column, 'archived', 0)
      this.selected = null
    },
    async deleteCard(card) {
      const token = useAuthStore().token
      await api(`/cards/${card.id}`, { method: 'DELETE', token })
      const column = this.column(card.column)
      column.cards.splice(column.cards.indexOf(card), 1)
      this.selected = null
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
