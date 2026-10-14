<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useBoardStore } from '../stores/board'

const board = useBoardStore()
const auth = useAuthStore()
const now = ref(Date.now())
const error = ref('')
const form = ref({ hours: '', date: new Date().toISOString().slice(0, 10), note: '' })
let tick

onMounted(() => (tick = setInterval(() => (now.value = Date.now()), 1000)))
onBeforeUnmount(() => clearInterval(tick))

// Tempo correndo = fim em aberto medido no navegador (a API guarda o início).
const runningSeconds = computed(() => {
  const running = board.time.running
  return running ? Math.max(0, Math.floor((now.value - new Date(running.started_at)) / 1000)) : 0
})

function clock(seconds) {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = seconds % 60
  return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

function hours(value) {
  const h = Math.floor(value)
  const m = Math.round((value - h) * 60)
  return m ? `${h}h ${m}min` : `${h}h`
}

function when(entry) {
  const start = new Date(entry.started_at)
  const date = start.toLocaleDateString('pt-BR')
  if (entry.is_manual) return `${date} · manual`
  const end = entry.ended_at ? new Date(entry.ended_at).toLocaleTimeString('pt-BR', { timeStyle: 'short' }) : '…'
  return `${date} ${start.toLocaleTimeString('pt-BR', { timeStyle: 'short' })}–${end}`
}

async function act(action) {
  error.value = ''
  try {
    await action()
  } catch (e) {
    error.value = e.message
  }
}

async function log() {
  await act(async () => {
    await board.logHours({ hours: Number(form.value.hours), date: form.value.date, note: form.value.note })
    form.value = { ...form.value, hours: '', note: '' }
  })
}
</script>

<template>
  <div>
    <div class="flex items-center gap-3">
      <p class="text-xl font-semibold tabular-nums" :class="board.time.running ? 'text-accent' : ''">
        {{ board.time.running ? clock(runningSeconds) : hours(board.time.total_hours) }}
      </p>
      <p v-if="board.time.running" class="text-[13px] text-muted">rodando · total {{ hours(board.time.total_hours) }}</p>
      <button v-if="board.time.running" type="button" class="btn ml-auto h-8" @click="act(board.stopTimer)">Parar</button>
      <button v-else type="button" class="btn btn-primary ml-auto h-8" @click="act(board.startTimer)">Iniciar cronômetro</button>
    </div>

    <ul v-if="board.time.entries.length" class="mt-3 space-y-1 text-sm">
      <li v-for="entry in board.time.entries" :key="entry.id" class="flex items-center gap-2">
        <span class="text-muted tabular-nums">{{ when(entry) }}</span>
        <span class="tabular-nums">{{ entry.is_running ? 'rodando' : hours(entry.hours) }}</span>
        <span v-if="entry.note" class="truncate text-muted">{{ entry.note }}</span>
        <span class="ml-auto text-[13px] text-muted">{{ entry.user.name || entry.user.email }}</span>
        <button
          v-if="entry.user.id === auth.user?.id && !entry.is_running"
          type="button"
          class="text-[13px] text-muted hover:text-danger"
          aria-label="Excluir entrada"
          @click="act(() => board.deleteTimeEntry(entry))"
        >
          ×
        </button>
      </li>
    </ul>
    <p v-else class="mt-2 text-sm text-muted">Nenhum tempo registrado.</p>

    <form class="mt-3 flex flex-wrap items-end gap-2" @submit.prevent="log">
      <div class="w-20">
        <label class="label text-[13px]" for="log-hours">Horas</label>
        <input id="log-hours" v-model="form.hours" class="field h-8 text-sm" type="number" min="0.25" step="0.25" required />
      </div>
      <div>
        <label class="label text-[13px]" for="log-date">Data</label>
        <input id="log-date" v-model="form.date" class="field h-8 text-sm" type="date" required />
      </div>
      <div class="min-w-32 flex-1">
        <label class="label text-[13px]" for="log-note">Nota</label>
        <input id="log-note" v-model="form.note" class="field h-8 text-sm" type="text" placeholder="opcional" />
      </div>
      <button type="submit" class="btn h-8">Lançar horas</button>
    </form>
    <p v-if="error" class="mt-1 text-[13px] text-danger" role="alert">{{ error }}</p>
  </div>
</template>
