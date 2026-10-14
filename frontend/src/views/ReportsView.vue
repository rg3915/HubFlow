<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { BASE_URL, api } from '../api'
import { useAuthStore } from '../stores/auth'
import { useClientsStore } from '../stores/clients'

const PERIODS = { week: 'Semana', fortnight: 'Quinzena', month: 'Mês', custom: 'Datas' }
const auth = useAuthStore()
const clients = useClientsStore()

const today = new Date().toISOString().slice(0, 10)
const filters = reactive({ client: '', project: '', period: 'month', date: today, start: today, end: today })
const report = ref(null)
const error = ref('')
const emails = ref('')
const notice = ref('')
const busy = ref(false)

const projects = computed(() => clients.projects.filter((p) => !filters.client || p.client_id === Number(filters.client)))
const maxHours = computed(() => Math.max(1, ...(report.value?.hours.by_user.map((r) => r.hours) || [])))

function params() {
  const query = new URLSearchParams()
  if (filters.project) query.set('project', filters.project)
  else if (filters.client) query.set('client', filters.client)
  if (filters.period === 'custom') {
    query.set('start', filters.start)
    query.set('end', filters.end)
  } else {
    query.set('period', filters.period)
    query.set('date', filters.date)
  }
  return query
}

async function load() {
  error.value = notice.value = ''
  if (!filters.client && !filters.project) {
    report.value = null
    return
  }
  try {
    report.value = await api(`/reports?${params()}`, { token: auth.token })
  } catch (e) {
    error.value = e.message
  }
}

async function downloadPdf() {
  busy.value = true
  try {
    const response = await fetch(`${BASE_URL}/api/reports/pdf?${params()}`, { headers: { Authorization: `Bearer ${auth.token}` } })
    if (!response.ok) throw new Error('Não foi possível gerar o PDF.')
    const name = /filename="([^"]+)"/.exec(response.headers.get('Content-Disposition') || '')?.[1] || 'relatorio.pdf'
    const link = Object.assign(document.createElement('a'), { href: URL.createObjectURL(await response.blob()), download: name })
    link.click()
    URL.revokeObjectURL(link.href)
  } catch (e) {
    error.value = e.message
  } finally {
    busy.value = false
  }
}

async function send() {
  error.value = notice.value = ''
  busy.value = true
  try {
    const body = Object.fromEntries(params())
    if (body.client) body.client = Number(body.client)
    if (body.project) body.project = Number(body.project)
    body.emails = emails.value.split(',').map((e) => e.trim()).filter(Boolean)
    const { sent_to } = await api('/reports/send', { method: 'POST', body, token: auth.token })
    notice.value = `Relatório enviado para ${sent_to.join(', ')}.`
  } catch (e) {
    error.value = e.message
  } finally {
    busy.value = false
  }
}

const br = (iso) => new Date(`${iso}T00:00`).toLocaleDateString('pt-BR')
const money = (value) => Number(value).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })

watch(() => filters.client, () => (filters.project = ''))
watch(filters, load, { deep: true })
onMounted(async () => {
  if (!clients.loaded) await clients.load()
  filters.client = clients.clients[0]?.id ?? ''
})
</script>

<template>
  <div class="mx-auto max-w-5xl space-y-4">
    <section class="panel flex flex-wrap items-end gap-3 p-4">
      <div>
        <label class="label" for="r-client">Cliente</label>
        <select id="r-client" v-model="filters.client" class="field h-9 w-auto">
          <option value="">—</option>
          <option v-for="client in clients.clients" :key="client.id" :value="client.id">{{ client.name }}</option>
        </select>
      </div>
      <div>
        <label class="label" for="r-project">Projeto</label>
        <select id="r-project" v-model="filters.project" class="field h-9 w-auto">
          <option value="">Todos</option>
          <option v-for="project in projects" :key="project.id" :value="project.id">{{ project.name }}</option>
        </select>
      </div>
      <div>
        <label class="label" for="r-period">Período</label>
        <select id="r-period" v-model="filters.period" class="field h-9 w-auto">
          <option v-for="(text, key) in PERIODS" :key="key" :value="key">{{ text }}</option>
        </select>
      </div>
      <div v-if="filters.period !== 'custom'">
        <label class="label" for="r-date">Contendo o dia</label>
        <input id="r-date" v-model="filters.date" class="field h-9" type="date" />
      </div>
      <template v-else>
        <div>
          <label class="label" for="r-start">De</label>
          <input id="r-start" v-model="filters.start" class="field h-9" type="date" />
        </div>
        <div>
          <label class="label" for="r-end">Até</label>
          <input id="r-end" v-model="filters.end" class="field h-9" type="date" />
        </div>
      </template>
      <button type="button" class="btn ml-auto h-9" :disabled="!report || busy" @click="downloadPdf">Baixar PDF</button>
    </section>

    <p v-if="error" class="text-danger" role="alert">{{ error }}</p>
    <p v-if="!report && !error" class="text-muted">Escolha um cliente ou projeto.</p>

    <template v-if="report">
      <p class="text-muted">
        <span class="font-medium text-text">{{ report.scope.project || report.scope.client }}</span>
        · {{ report.period.label }} de {{ br(report.period.start) }} a {{ br(report.period.end) }}
      </p>
      <div class="grid grid-cols-2 gap-3 md:grid-cols-5">
        <div class="panel p-3"><p class="text-[13px] text-muted">Horas registradas</p><p class="text-xl font-semibold tabular-nums">{{ report.hours.total }}h</p></div>
        <div class="panel p-3"><p class="text-[13px] text-muted">Cards criados</p><p class="text-xl font-semibold tabular-nums">{{ report.cards.created }}</p></div>
        <div class="panel p-3"><p class="text-[13px] text-muted">Cards concluídos</p><p class="text-xl font-semibold tabular-nums">{{ report.cards.done }}</p></div>
        <div class="panel p-3"><p class="text-[13px] text-muted">Dias até concluir</p><p class="text-xl font-semibold tabular-nums">{{ report.cards.avg_days_to_done ?? '—' }}</p></div>
        <div class="panel p-3"><p class="text-[13px] text-muted">SLAs estourados</p><p class="text-xl font-semibold tabular-nums" :class="{ 'text-danger': report.sla_breached }">{{ report.sla_breached }}</p></div>
      </div>

      <div class="grid gap-4 md:grid-cols-2">
        <section class="panel p-4">
          <h2 class="mb-3 font-medium">Horas por pessoa</h2>
          <ul v-if="report.hours.by_user.length" class="space-y-2">
            <li v-for="row in report.hours.by_user" :key="row.name" class="text-sm">
              <div class="flex justify-between"><span>{{ row.name }}</span><span class="tabular-nums text-muted">{{ row.hours }}h</span></div>
              <div class="mt-1 h-2 rounded-full bg-surface-2"><div class="h-full rounded-full bg-accent" :style="{ width: `${(row.hours / maxHours) * 100}%` }"></div></div>
            </li>
          </ul>
          <p v-else class="text-muted">Nenhuma hora no período.</p>
        </section>
        <section class="panel p-4">
          <h2 class="mb-3 font-medium">Cards com mais horas</h2>
          <table v-if="report.hours.by_card.length" class="w-full text-sm">
            <tr v-for="row in report.hours.by_card" :key="`${row.project}-${row.number}`" class="border-b border-border last:border-0">
              <td class="py-1.5 text-muted">{{ row.project }}</td>
              <td class="py-1.5">#{{ row.number }} {{ row.title }}</td>
              <td class="py-1.5 text-right tabular-nums">{{ row.hours }}h</td>
            </tr>
          </table>
          <p v-else class="text-muted">Nenhum card com horas no período.</p>
        </section>
      </div>

      <section v-if="report.billing" class="panel flex gap-8 p-4">
        <div><p class="text-[13px] text-muted">Recebido no período</p><p class="text-lg font-semibold tabular-nums">{{ money(report.billing.received) }}</p></div>
        <div><p class="text-[13px] text-muted">Pendente no período</p><p class="text-lg font-semibold tabular-nums">{{ money(report.billing.pending) }}</p></div>
      </section>

      <form class="panel flex flex-wrap items-end gap-3 p-4" @submit.prevent="send">
        <div class="min-w-64 flex-1">
          <label class="label" for="r-emails">Enviar por e-mail</label>
          <input id="r-emails" v-model="emails" class="field h-9" type="text" placeholder="Vazio = e-mails do projeto/cliente; ou: a@hubflow.com, b@hubflow.com" />
        </div>
        <button type="submit" class="btn btn-primary h-9" :disabled="busy">Enviar PDF</button>
        <p v-if="notice" class="w-full text-muted" role="status">{{ notice }}</p>
      </form>
    </template>
  </div>
</template>
