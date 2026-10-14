<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../api'
import { useAuthStore } from '../stores/auth'
import { useClientsStore } from '../stores/clients'

const route = useRoute()
const auth = useAuthStore()
const clients = useClientsStore()
const projectId = computed(() => Number(route.params.id))

const sprints = ref([])
const form = ref({ name: '', start_date: '', end_date: '' })
const error = ref('')

async function load() {
  if (!clients.loaded) await clients.load()
  sprints.value = await api(`/projects/${projectId.value}/sprints`, { token: auth.token })
}
onMounted(load)

const current = computed(() => sprints.value.find((s) => s.is_open))

async function create() {
  error.value = ''
  try {
    const body = {
      name: form.value.name,
      start_date: form.value.start_date || null,
      end_date: form.value.end_date || null,
    }
    await api(`/projects/${projectId.value}/sprints`, { method: 'POST', body, token: auth.token })
    form.value = { name: '', start_date: '', end_date: '' }
    await load()
  } catch (e) {
    error.value = e.message
  }
}

async function close(sprint) {
  if (!confirm(`Fechar a Sprint ${sprint.number}? Os cards continuam onde estão.`)) return
  await api(`/sprints/${sprint.id}/close`, { method: 'POST', token: auth.token })
  await load()
}

function period(sprint) {
  const fmt = (d) => (d ? new Date(d + 'T00:00').toLocaleDateString('pt-BR') : '…')
  return sprint.start_date || sprint.end_date ? `${fmt(sprint.start_date)} – ${fmt(sprint.end_date)}` : 'sem datas'
}
</script>

<template>
  <div class="max-w-3xl">
    <table class="panel w-full border-separate border-spacing-0 overflow-hidden">
      <thead>
        <tr class="text-left text-muted">
          <th class="border-b border-border px-4 py-2 font-medium">Sprint</th>
          <th class="border-b border-border px-4 py-2 font-medium">Período</th>
          <th class="border-b border-border px-4 py-2 font-medium">Cards</th>
          <th class="border-b border-border px-4 py-2 font-medium">Situação</th>
          <th class="border-b border-border px-4 py-2"></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="sprint in sprints" :key="sprint.id" :class="{ 'bg-surface-2/60': sprint.id === current?.id }">
          <td class="border-b border-border px-4 py-2.5">
            <RouterLink :to="`/projects/${projectId}?sprint=${sprint.id}`" class="font-medium hover:underline">
              Sprint {{ sprint.number }}<span v-if="sprint.name" class="font-normal text-muted"> · {{ sprint.name }}</span>
            </RouterLink>
            <span v-if="sprint.milestone" class="ml-2 text-[13px] text-muted">{{ sprint.milestone.title }}</span>
          </td>
          <td class="border-b border-border px-4 py-2.5 text-muted">{{ period(sprint) }}</td>
          <td class="border-b border-border px-4 py-2.5 tabular-nums">{{ sprint.cards_count }}</td>
          <td class="border-b border-border px-4 py-2.5">
            <span v-if="sprint.is_open">{{ sprint.id === current?.id ? 'atual' : 'aberta' }}</span>
            <span v-else class="text-muted">fechada</span>
          </td>
          <td class="border-b border-border px-4 py-2.5 text-right">
            <button v-if="sprint.is_open" type="button" class="text-accent hover:underline" @click="close(sprint)">Fechar</button>
          </td>
        </tr>
        <tr v-if="!sprints.length">
          <td colspan="5" class="px-4 py-3 text-muted">Nenhuma sprint ainda. A primeira é criada junto com o primeiro card, ou aqui embaixo.</td>
        </tr>
      </tbody>
    </table>

    <form class="panel mt-4 flex flex-wrap items-end gap-3 p-4" @submit.prevent="create">
      <div class="min-w-48 flex-1">
        <label class="label" for="sprint-name">Nova sprint</label>
        <input id="sprint-name" v-model="form.name" class="field h-9" type="text" placeholder="Nome (opcional)" />
      </div>
      <div>
        <label class="label" for="sprint-start">Início</label>
        <input id="sprint-start" v-model="form.start_date" class="field h-9" type="date" />
      </div>
      <div>
        <label class="label" for="sprint-end">Fim</label>
        <input id="sprint-end" v-model="form.end_date" class="field h-9" type="date" />
      </div>
      <button type="submit" class="btn btn-primary h-9">Criar sprint</button>
      <p v-if="error" class="w-full text-danger" role="alert">{{ error }}</p>
    </form>
  </div>
</template>
