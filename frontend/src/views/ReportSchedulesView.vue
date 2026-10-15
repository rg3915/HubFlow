<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { api } from '../api'
import { useAuthStore } from '../stores/auth'
import { useClientsStore } from '../stores/clients'

const FREQUENCY = { week: 'Semanal', fortnight: 'Quinzenal', month: 'Mensal' }
const auth = useAuthStore()
const clients = useClientsStore()

const schedules = ref([])
const error = ref('')
const form = reactive({ client: '', project: '', frequency: 'month', emails: '' })
const projects = computed(() => clients.projects.filter((p) => !form.client || p.client_id === Number(form.client)))

const call = (path, options = {}) => api(path, { token: auth.token, ...options })
const emailList = (text) => text.split(',').map((e) => e.trim()).filter(Boolean)
const body = (item) => ({
  client: item.project ? null : Number(item.client) || null,
  project: Number(item.project) || null,
  frequency: item.frequency,
  emails: item.emails,
  is_active: item.is_active ?? true,
})
const br = (iso) => (iso ? new Date(`${iso}T00:00`).toLocaleDateString('pt-BR') : '—')

async function attempt(action) {
  error.value = ''
  try {
    await action()
  } catch (e) {
    error.value = e.message
  }
}

onMounted(async () => {
  if (!clients.loaded) await clients.load()
  schedules.value = await call('/report-schedules')
})

const create = () =>
  attempt(async () => {
    schedules.value.push(await call('/report-schedules', { method: 'POST', body: body({ ...form, emails: emailList(form.emails) }) }))
    Object.assign(form, { client: '', project: '', frequency: 'month', emails: '' })
  })

const toggle = (item) =>
  attempt(async () => {
    const current = { client: item.client_id, project: item.project_id, frequency: item.frequency, emails: item.emails, is_active: !item.is_active }
    Object.assign(item, await call(`/report-schedules/${item.id}`, { method: 'PUT', body: body(current) }))
  })

async function remove(item) {
  if (!confirm(`Cancelar o relatório ${FREQUENCY[item.frequency].toLowerCase()} de ${item.scope}?`)) return
  await attempt(async () => {
    await call(`/report-schedules/${item.id}`, { method: 'DELETE' })
    schedules.value = schedules.value.filter((s) => s.id !== item.id)
  })
}
</script>

<template>
  <div class="mx-auto max-w-[96rem]">
    <p class="mb-4 text-[0.93rem] text-muted">
      O relatório em PDF sai por e-mail quando cada período termina (verificação a cada 15 minutos), com o que você pode ver. Sem e-mails, vão para os do projeto ou do cliente.
    </p>

    <section class="panel divide-y divide-border">
      <div v-for="item in schedules" :key="item.id" class="flex items-center gap-3 p-3">
        <input type="checkbox" class="h-4 w-4 accent-[var(--accent)]" :checked="item.is_active" :aria-label="`Ligar relatório de ${item.scope}`" @change="toggle(item)" />
        <div class="min-w-0 flex-1" :class="{ 'opacity-60': !item.is_active }">
          <p class="font-medium">{{ item.scope }} · {{ FREQUENCY[item.frequency] }}</p>
          <p class="truncate text-[0.93rem] text-muted">
            {{ item.emails.join(', ') || 'e-mails do projeto/cliente' }} · coberto até {{ br(item.last_period_end) }}
          </p>
        </div>
        <button type="button" class="btn btn-ghost h-8 text-danger" @click="remove(item)">Cancelar</button>
      </div>
      <p v-if="!schedules.length" class="p-3 text-muted">Nenhum relatório agendado.</p>
    </section>

    <form class="panel mt-4 flex flex-wrap items-end gap-3 p-4" @submit.prevent="create">
      <div>
        <label class="label" for="s-client">Cliente</label>
        <select id="s-client" v-model="form.client" class="field h-9 w-auto" :required="!form.project">
          <option value="">—</option>
          <option v-for="client in clients.clients" :key="client.id" :value="client.id">{{ client.name }}</option>
        </select>
      </div>
      <div>
        <label class="label" for="s-project">Projeto</label>
        <select id="s-project" v-model="form.project" class="field h-9 w-auto">
          <option value="">Todos do cliente</option>
          <option v-for="project in projects" :key="project.id" :value="project.id">{{ project.name }}</option>
        </select>
      </div>
      <div>
        <label class="label" for="s-frequency">Frequência</label>
        <select id="s-frequency" v-model="form.frequency" class="field h-9 w-auto">
          <option v-for="(text, key) in FREQUENCY" :key="key" :value="key">{{ text }}</option>
        </select>
      </div>
      <div class="min-w-56 flex-1">
        <label class="label" for="s-emails">E-mails (opcional)</label>
        <input id="s-emails" v-model="form.emails" class="field h-9" type="text" placeholder="a@hubflow.com, b@hubflow.com" />
      </div>
      <button type="submit" class="btn btn-primary h-9">Agendar</button>
    </form>
    <p v-if="error" class="mt-2 text-danger" role="alert">{{ error }}</p>
  </div>
</template>
