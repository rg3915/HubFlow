<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api'
import { useAuthStore } from '../stores/auth'

// Sino (notificações) e "meus cards" no cabeçalho; atualiza a cada minuto e a cada troca de página.
const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const root = ref(null)
const open = ref(null) // 'notes' | 'cards' | null
const notes = ref({ unread: 0, items: [] })
const cards = ref([])
let timer

const call = (path, method = 'GET') => api(path, { method, token: auth.token })

async function refresh() {
  if (!auth.token) return
  ;[notes.value, cards.value] = await Promise.all([call('/notifications'), call('/me/cards')]).catch(() => [notes.value, cards.value])
}

function toggle(which) {
  open.value = open.value === which ? null : which
}

const goToCard = (projectId, number) => router.push({ path: `/projects/${projectId}`, query: { card: number } })

async function openNote(note) {
  open.value = null
  if (!note.read) notes.value = await call(`/notifications/${note.id}/read`, 'POST')
  goToCard(note.project_id, note.card_number)
}

async function readAll() {
  notes.value = await call('/notifications/read-all', 'POST')
}

function close(event) {
  if (!root.value?.contains(event.target)) open.value = null
}

const when = (iso) => new Date(iso).toLocaleString('pt-BR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })
const due = (date) => new Date(`${date}T00:00`).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' })

watch(() => route.fullPath, refresh)
onMounted(() => {
  refresh()
  timer = setInterval(refresh, 60_000)
  document.addEventListener('click', close)
})
onBeforeUnmount(() => {
  clearInterval(timer)
  document.removeEventListener('click', close)
})
</script>

<template>
  <div ref="root" class="relative flex items-center gap-1">
    <button
      type="button"
      class="btn btn-ghost relative h-8 w-8 justify-center px-0 text-muted"
      :aria-label="`Meus cards: ${cards.length} em aberto`"
      title="Meus cards"
      :aria-expanded="open === 'cards'"
      @click="toggle('cards')"
    >
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <rect x="3" y="4" width="18" height="16" rx="2" /><path d="M8 9h8M8 13h5" />
      </svg>
      <span v-if="cards.length" class="absolute -right-0.5 -top-0.5 min-w-4 rounded-full bg-surface-2 px-1 text-[10px] font-medium leading-4 text-text tabular-nums">{{ cards.length }}</span>
    </button>

    <button
      type="button"
      class="btn btn-ghost relative h-8 w-8 justify-center px-0 text-muted"
      :aria-label="`Notificações: ${notes.unread} não lidas`"
      title="Notificações"
      :aria-expanded="open === 'notes'"
      @click="toggle('notes')"
    >
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9" /><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0" />
      </svg>
      <span v-if="notes.unread" class="absolute -right-0.5 -top-0.5 min-w-4 rounded-full bg-accent px-1 text-[10px] font-medium leading-4 text-white tabular-nums">{{ notes.unread }}</span>
    </button>

    <div v-if="open === 'notes'" class="panel fixed inset-x-2 top-12 z-30 shadow-sm md:absolute md:inset-x-auto md:right-0 md:top-9 md:w-[22rem]">
      <header class="flex items-center border-b border-border px-3 py-2">
        <h2 class="font-medium">Notificações</h2>
        <button v-if="notes.unread" type="button" class="ml-auto text-[13px] text-accent hover:underline" @click="readAll">Marcar todas como lidas</button>
      </header>
      <ul class="max-h-96 overflow-y-auto">
        <li v-for="note in notes.items" :key="note.id">
          <button type="button" class="flex w-full gap-2 px-3 py-2 text-left hover:bg-surface-2" @click="openNote(note)">
            <span class="mt-1.5 h-2 w-2 shrink-0 rounded-full" :class="note.read ? 'bg-transparent' : 'bg-accent'" aria-hidden="true"></span>
            <span class="min-w-0">
              <span class="block text-sm" :class="{ 'text-muted': note.read }">{{ note.text }}</span>
              <span class="block text-[13px] text-muted">{{ when(note.created) }}</span>
            </span>
          </button>
        </li>
        <li v-if="!notes.items.length" class="px-3 py-4 text-sm text-muted">Nenhuma notificação.</li>
      </ul>
    </div>

    <div v-if="open === 'cards'" class="panel fixed inset-x-2 top-12 z-30 shadow-sm md:absolute md:inset-x-auto md:right-0 md:top-9 md:w-[22rem]">
      <h2 class="border-b border-border px-3 py-2 font-medium">Meus cards</h2>
      <ul class="max-h-96 overflow-y-auto">
        <li v-for="card in cards" :key="card.id">
          <button type="button" class="block w-full px-3 py-2 text-left hover:bg-surface-2" @click="open = null; goToCard(card.project_id, card.number)">
            <span class="block truncate text-sm">#{{ card.number }} {{ card.title }}</span>
            <span class="block text-[13px] text-muted">
              {{ card.client_name }} / {{ card.project_name }}
              <span v-if="card.due_date" :class="{ 'text-danger': card.is_overdue }"> · {{ card.is_overdue ? 'venceu' : 'prazo' }} {{ due(card.due_date) }}</span>
            </span>
          </button>
        </li>
        <li v-if="!cards.length" class="px-3 py-4 text-sm text-muted">Nenhum card em aberto com você.</li>
      </ul>
    </div>
  </div>
</template>
