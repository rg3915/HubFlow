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
    checklist: [],
    attachments: [],
    activity: [],
    sprints: [],
    sprintId: null,
    time: { entries: [], total_hours: 0, running: null },
  }),
  actions: {
    async load(projectId, { archived = false, sprintId = null } = {}) {
      const token = useAuthStore().token
      this.loading = true
      this.sprintId = sprintId
      try {
        const query = `archived=${archived}` + (sprintId ? `&sprint=${sprintId}` : '')
        const board = await api(`/projects/${projectId}/board?${query}`, { token })
        this.projectId = projectId
        this.project = board.project
        this.columns = board.columns
        ;[this.labels, this.users, this.sprints] = await Promise.all([
          api(`/projects/${projectId}/labels`, { token }),
          api('/users', { token }),
          api(`/projects/${projectId}/sprints`, { token }),
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
      this.comments = this.checklist = this.attachments = this.activity = []
      this.time = { entries: [], total_hours: 0, running: null }
      if (!card) return
      const token = useAuthStore().token
      ;[this.comments, this.checklist, this.attachments, this.activity, this.time] = await Promise.all([
        api(`/cards/${card.id}/comments`, { token }),
        api(`/cards/${card.id}/checklist`, { token }),
        api(`/cards/${card.id}/attachments`, { token }),
        api(`/cards/${card.id}/activity`, { token }),
        api(`/cards/${card.id}/time`, { token }),
      ])
    },
    async refreshTime() {
      this.time = await api(`/cards/${this.selected.id}/time`, { token: useAuthStore().token })
      this.selected.time = { hours: this.time.total_hours, running: Boolean(this.time.running) }
    },
    async startTimer() {
      await api(`/cards/${this.selected.id}/timer/start`, { method: 'POST', token: useAuthStore().token })
      await this.refreshTime()
    },
    async stopTimer() {
      await api(`/cards/${this.selected.id}/timer/stop`, { method: 'POST', token: useAuthStore().token })
      await this.refreshTime()
    },
    async logHours(body) {
      await api(`/cards/${this.selected.id}/time-entries`, { method: 'POST', body, token: useAuthStore().token })
      await this.refreshTime()
    },
    async deleteTimeEntry(entry) {
      await api(`/time-entries/${entry.id}`, { method: 'DELETE', token: useAuthStore().token })
      await this.refreshTime()
    },
    async refreshActivity() {
      this.activity = await api(`/cards/${this.selected.id}/activity`, { token: useAuthStore().token })
    },
    syncChecklistSummary() {
      this.selected.checklist = { done: this.checklist.filter((i) => i.done).length, total: this.checklist.length }
    },
    async addChecklistItem(text) {
      const token = useAuthStore().token
      const item = await api(`/cards/${this.selected.id}/checklist`, { method: 'POST', body: { text }, token })
      this.checklist.push(item)
      this.syncChecklistSummary()
    },
    async toggleChecklistItem(item) {
      const token = useAuthStore().token
      const body = { text: item.text, done: !item.done }
      Object.assign(item, await api(`/checklist/${item.id}`, { method: 'PUT', body, token }))
      this.syncChecklistSummary()
    },
    async deleteChecklistItem(item) {
      await api(`/checklist/${item.id}`, { method: 'DELETE', token: useAuthStore().token })
      this.checklist.splice(this.checklist.indexOf(item), 1)
      this.syncChecklistSummary()
    },
    async reorderChecklist(itemIds) {
      const token = useAuthStore().token
      const body = { item_ids: itemIds }
      this.checklist = await api(`/cards/${this.selected.id}/checklist/order`, { method: 'PUT', body, token })
    },
    async uploadAttachment(file) {
      const form = new FormData()
      form.append('file', file)
      const token = useAuthStore().token
      const attachment = await api(`/cards/${this.selected.id}/attachments`, { method: 'POST', form, token })
      this.attachments.push(attachment)
      this.selected.attachments_count = this.attachments.length
      await this.refreshActivity()
    },
    async deleteAttachment(attachment) {
      await api(`/attachments/${attachment.id}`, { method: 'DELETE', token: useAuthStore().token })
      this.attachments.splice(this.attachments.indexOf(attachment), 1)
      this.selected.attachments_count = this.attachments.length
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
      await this.refreshActivity()
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
