import { defineStore } from 'pinia'
import { api } from '../api'
import { useAuthStore } from './auth'

export const useBoardStore = defineStore('board', {
  state: () => ({
    projectId: null,
    project: null,
    columns: [],
    loading: false,
    selected: null,
    labels: [],
    users: [],
    comments: [],
  }),
  actions: {
    async load(projectId, { archived = false } = {}) {
      const token = useAuthStore().token
      this.loading = true
      try {
        const board = await api(`/projects/${projectId}/board?archived=${archived}`, { token })
        this.projectId = projectId
        this.project = board.project
        this.columns = board.columns
        ;[this.labels, this.users] = await Promise.all([
          api(`/projects/${projectId}/labels`, { token }),
          api('/users', { token }),
        ])
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
    async select(card) {
      this.selected = card
      this.comments = []
      if (card) this.comments = await api(`/cards/${card.id}/comments`, { token: useAuthStore().token })
    },
    async updateCard(card, data) {
      const token = useAuthStore().token
      const body = {
        title: card.title,
        description: card.description,
        due_date: card.due_date,
        assignee_id: card.assignee?.id ?? null,
        ...data,
      }
      const saved = await api(`/cards/${card.id}`, { method: 'PUT', body, token })
      Object.assign(card, saved)
      return saved
    },
    async setLabels(card, labelIds) {
      const token = useAuthStore().token
      const saved = await api(`/cards/${card.id}/labels`, { method: 'PUT', body: { label_ids: labelIds }, token })
      Object.assign(card, saved)
    },
    async createLabel(name, color) {
      const token = useAuthStore().token
      const label = await api(`/projects/${this.projectId}/labels`, { method: 'POST', body: { name, color }, token })
      this.labels.push(label)
      this.labels.sort((a, b) => a.name.localeCompare(b.name))
      return label
    },
    async addComment(card, text) {
      const token = useAuthStore().token
      const comment = await api(`/cards/${card.id}/comments`, { method: 'POST', body: { text }, token })
      this.comments.push(comment)
      return comment
    },
    async deleteComment(comment) {
      await api(`/comments/${comment.id}`, { method: 'DELETE', token: useAuthStore().token })
      this.comments.splice(this.comments.indexOf(comment), 1)
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
