<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { api } from '../api'
import BarChart from '../components/BarChart.vue'
import { useAuthStore } from '../stores/auth'
import { useClientsStore } from '../stores/clients'

const auth = useAuthStore()
const clients = useClientsStore()

const payments = ref([])
const summary = ref({ received: '0', pending: '0', by_client: [], by_month: [], years: [] })
const filters = ref({ year: '', client: '', status: '' })
const editing = ref(null) // null = fechado; {} = novo; {id} = edição
const sprints = ref([])
const error = ref('')

const emptyForm = () => ({
  project_id: '',
  mode: 'month',
  sprint_id: '',
  month: new Date().toISOString().slice(0, 7),
  hourly_rate: '',
  estimated_hours: '',
  fixed_value: '',
  description: '',
  invoice_number: '',
  issue_date: '',
})
const form = ref(emptyForm())

function money(value, short = false) {
  const number = Number(value || 0)
  if (short) return number >= 1000 ? `${Math.round(number / 1000)} mil` : String(Math.round(number))
  return number.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

function query() {
  const params = new URLSearchParams()
  for (const [key, value] of Object.entries(filters.value)) if (value) params.set(key, value)
  const text = params.toString()
  return text ? `?${text}` : ''
}

async function load() {
  if (!clients.loaded) await clients.load()
  const token = auth.token
  const summaryQuery = query().replace(/&?status=[^&]*/, '').replace(/^\?&/, '?')
  ;[payments.value, summary.value] = await Promise.all([
    api(`/payments${query()}`, { token }),
    api(`/payments/summary${summaryQuery === '?' ? '' : summaryQuery}`, { token }),
  ])
}
onMounted(load)
watch(filters, load, { deep: true })

const months = computed(() => summary.value.by_month.map((m) => ({ ...m, label: m.month.slice(5) + '/' + m.month.slice(2, 4) })))
const byClient = computed(() => summary.value.by_client.map((c) => ({ ...c, label: c.client_name })))

async function openForm(payment = null) {
  error.value = ''
  if (payment) {
    form.value = {
      project_id: payment.project_id,
      mode: payment.sprint_id ? 'sprint' : 'month',
      sprint_id: payment.sprint_id || '',
      month: payment.period_start ? payment.period_start.slice(0, 7) : '',
      hourly_rate: payment.hourly_rate,
      estimated_hours: payment.estimated_hours ?? '',
      fixed_value: payment.fixed_value ?? '',
      description: payment.description,
      invoice_number: payment.invoice_number,
      issue_date: payment.issue_date || '',
    }
    editing.value = payment
  } else {
    form.value = emptyForm()
    editing.value = {}
  }
  await loadSprints()
}

async function loadSprints() {
  sprints.value = form.value.project_id ? await api(`/projects/${form.value.project_id}/sprints`, { token: auth.token }) : []
}
watch(() => form.value.project_id, loadSprints)

async function save() {
  error.value = ''
  const body = {
    project_id: Number(form.value.project_id),
    sprint_id: form.value.mode === 'sprint' && form.value.sprint_id ? Number(form.value.sprint_id) : null,
    month: form.value.mode === 'month' ? form.value.month || null : null,
    hourly_rate: form.value.hourly_rate,
    estimated_hours: form.value.estimated_hours || null,
    fixed_value: form.value.fixed_value || null,
    description: form.value.description,
    invoice_number: form.value.invoice_number,
    issue_date: form.value.issue_date || null,
  }
  try {
    const token = auth.token
    if (editing.value.id) await api(`/payments/${editing.value.id}`, { method: 'PUT', body, token })
    else await api('/payments', { method: 'POST', body, token })
    editing.value = null
    await load()
  } catch (e) {
    error.value = e.status === 422 ? 'Confira os campos: projeto e valor por hora são obrigatórios.' : e.message
  }
}

async function act(payment, action) {
  if (action === 'delete' && !confirm(`Excluir o pagamento #${payment.id}?`)) return
  const token = auth.token
  if (action === 'delete') await api(`/payments/${payment.id}`, { method: 'DELETE', token })
  else await api(`/payments/${payment.id}/${action}`, { method: 'POST', token })
  await load()
}

function date(value) {
  return value ? new Date(value + 'T00:00').toLocaleDateString('pt-BR') : '—'
}
</script>

<template>
  <div class="mx-auto max-w-6xl space-y-4">
    <div class="flex flex-wrap items-center gap-2">
      <select v-model="filters.year" class="field h-9 w-auto text-sm" aria-label="Ano">
        <option value="">Todos os anos</option>
        <option v-for="year in summary.years" :key="year" :value="year">{{ year }}</option>
      </select>
      <select v-model="filters.client" class="field h-9 w-auto text-sm" aria-label="Cliente">
        <option value="">Todos os clientes</option>
        <option v-for="client in clients.clients" :key="client.id" :value="client.id">{{ client.name }}</option>
      </select>
      <select v-model="filters.status" class="field h-9 w-auto text-sm" aria-label="Situação">
        <option value="">Pendentes e pagos</option>
        <option value="pending">Pendentes</option>
        <option value="paid">Pagos</option>
      </select>
      <button v-if="auth.can('billing.add_payment')" type="button" class="btn btn-primary ml-auto" @click="openForm()">Novo pagamento</button>
    </div>

    <div class="grid grid-cols-2 gap-3 md:grid-cols-4">
      <div class="panel p-4"><p class="text-muted">Recebido</p><p class="text-2xl font-semibold tabular-nums">{{ money(summary.received) }}</p></div>
      <div class="panel p-4"><p class="text-muted">Pendente</p><p class="text-2xl font-semibold tabular-nums">{{ money(summary.pending) }}</p></div>
      <div class="panel p-4"><p class="text-muted">Clientes faturados</p><p class="text-2xl font-semibold tabular-nums">{{ summary.by_client.length }}</p></div>
      <div class="panel p-4"><p class="text-muted">Pagamentos</p><p class="text-2xl font-semibold tabular-nums">{{ payments.length }}</p></div>
    </div>

    <div class="grid gap-3 md:grid-cols-2">
      <section class="panel p-4">
        <h2 class="mb-2 font-medium">Por mês</h2>
        <BarChart v-if="months.length" :rows="months" :money="money" />
        <p v-else class="text-muted">Sem pagamentos com data de emissão.</p>
      </section>
      <section class="panel p-4">
        <h2 class="mb-2 font-medium">Por cliente</h2>
        <BarChart v-if="byClient.length" :rows="byClient" :money="money" />
        <p v-else class="text-muted">Sem pagamentos.</p>
      </section>
    </div>

    <section v-if="editing" class="panel p-4">
      <h2 class="mb-3 font-medium">{{ editing.id ? `Pagamento #${editing.id}` : 'Novo pagamento' }}</h2>
      <form class="grid gap-3 md:grid-cols-4" @submit.prevent="save">
        <div class="md:col-span-2">
          <label class="label" for="pay-project">Projeto</label>
          <select id="pay-project" v-model="form.project_id" class="field" required>
            <option value="" disabled>Escolha o projeto</option>
            <option v-for="project in clients.projects" :key="project.id" :value="project.id">{{ project.client_name }} / {{ project.name }}</option>
          </select>
        </div>
        <div>
          <label class="label" for="pay-mode">Cobrança</label>
          <select id="pay-mode" v-model="form.mode" class="field">
            <option value="month">Por mês</option>
            <option value="sprint">Por sprint</option>
          </select>
        </div>
        <div v-if="form.mode === 'month'">
          <label class="label" for="pay-month">Mês</label>
          <input id="pay-month" v-model="form.month" class="field" type="month" required />
        </div>
        <div v-else>
          <label class="label" for="pay-sprint">Sprint</label>
          <select id="pay-sprint" v-model="form.sprint_id" class="field" required>
            <option value="" disabled>Escolha</option>
            <option v-for="sprint in sprints" :key="sprint.id" :value="sprint.id">Sprint {{ sprint.number }}{{ sprint.name ? ` · ${sprint.name}` : '' }}</option>
          </select>
        </div>
        <div><label class="label" for="pay-rate">Valor/hora</label><input id="pay-rate" v-model="form.hourly_rate" class="field" type="number" min="0.01" step="0.01" required /></div>
        <div><label class="label" for="pay-hours">Horas estimadas</label><input id="pay-hours" v-model="form.estimated_hours" class="field" type="number" min="0" step="0.5" /></div>
        <div><label class="label" for="pay-fixed">Valor fechado</label><input id="pay-fixed" v-model="form.fixed_value" class="field" type="number" min="0" step="0.01" placeholder="opcional" /></div>
        <div><label class="label" for="pay-invoice">NF</label><input id="pay-invoice" v-model="form.invoice_number" class="field" type="text" /></div>
        <div><label class="label" for="pay-issue">Emissão</label><input id="pay-issue" v-model="form.issue_date" class="field" type="date" /></div>
        <div class="md:col-span-3"><label class="label" for="pay-desc">Descrição</label><input id="pay-desc" v-model="form.description" class="field" type="text" /></div>
        <p v-if="error" class="md:col-span-4 rounded-[var(--radius-control)] border border-danger/40 px-3 py-2 text-danger" role="alert">{{ error }}</p>
        <div class="flex gap-2 md:col-span-4">
          <button type="submit" class="btn btn-primary">{{ editing.id ? 'Salvar' : 'Criar pagamento' }}</button>
          <button type="button" class="btn btn-ghost" @click="editing = null">Cancelar</button>
        </div>
      </form>
    </section>

    <table class="panel w-full border-separate border-spacing-0 overflow-hidden text-sm">
      <thead>
        <tr class="text-left text-muted">
          <th class="border-b border-border px-3 py-2 font-medium">#</th>
          <th class="border-b border-border px-3 py-2 font-medium">Cliente / Projeto</th>
          <th class="border-b border-border px-3 py-2 font-medium">Cobrança</th>
          <th class="border-b border-border px-3 py-2 text-right font-medium">Horas</th>
          <th class="border-b border-border px-3 py-2 text-right font-medium">Valor/h</th>
          <th class="border-b border-border px-3 py-2 text-right font-medium">Total</th>
          <th class="border-b border-border px-3 py-2 font-medium">NF</th>
          <th class="border-b border-border px-3 py-2 font-medium">Emissão</th>
          <th class="border-b border-border px-3 py-2 font-medium">Pagamento</th>
          <th class="border-b border-border px-3 py-2 font-medium">Situação</th>
          <th class="border-b border-border px-3 py-2"></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="payment in payments" :key="payment.id" class="hover:bg-surface-2/60">
          <td class="border-b border-border px-3 py-2 tabular-nums">{{ payment.id }}</td>
          <td class="border-b border-border px-3 py-2">{{ payment.client_name }} / {{ payment.project_name }}</td>
          <td class="border-b border-border px-3 py-2 text-muted">{{ payment.scope }}</td>
          <td class="border-b border-border px-3 py-2 text-right tabular-nums">{{ payment.spent_hours }}</td>
          <td class="border-b border-border px-3 py-2 text-right tabular-nums">{{ money(payment.hourly_rate) }}</td>
          <td class="border-b border-border px-3 py-2 text-right font-medium tabular-nums">{{ money(payment.total_value) }}</td>
          <td class="border-b border-border px-3 py-2">{{ payment.invoice_number || '—' }}</td>
          <td class="border-b border-border px-3 py-2 tabular-nums">{{ date(payment.issue_date) }}</td>
          <td class="border-b border-border px-3 py-2 tabular-nums">{{ date(payment.payment_date) }}</td>
          <td class="border-b border-border px-3 py-2">
            <span :class="payment.status === 'paid' ? 'text-[var(--chart-1)]' : 'text-[var(--chart-2)]'">{{ payment.status === 'paid' ? '● pago' : '○ pendente' }}</span>
          </td>
          <td class="border-b border-border px-3 py-2 text-right whitespace-nowrap">
            <template v-if="auth.can('billing.change_payment')">
              <button type="button" class="text-accent hover:underline" @click="openForm(payment)">Editar</button>
              <button type="button" class="ml-2 text-accent hover:underline" @click="act(payment, 'copy')">Copiar</button>
              <button v-if="payment.status !== 'paid'" type="button" class="ml-2 text-accent hover:underline" @click="act(payment, 'pay')">Pagar</button>
            </template>
            <button v-if="auth.can('billing.delete_payment')" type="button" class="ml-2 text-danger hover:underline" @click="act(payment, 'delete')">Excluir</button>
          </td>
        </tr>
        <tr v-if="!payments.length"><td colspan="11" class="px-3 py-3 text-muted">Nenhum pagamento.</td></tr>
      </tbody>
    </table>
  </div>
</template>
