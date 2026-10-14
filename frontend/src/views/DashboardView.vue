<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { api } from '../api'
import Heatmap from '../components/Heatmap.vue'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const overview = ref(null)
const deadlines = ref({ overdue: [], upcoming: [] })
const activity = ref([])
const heatmap = ref(null)
const week = ref(null)
const billing = ref(null)
const now = ref(Date.now())
let tick

const columns = { backlog: 'Backlog', sprint: 'Sprint', doing: 'Em desenvolvimento', qa: 'QA', done: 'Concluído', archived: 'Arquivadas' }

async function load() {
  const token = auth.token
  ;[overview.value, deadlines.value, activity.value, heatmap.value, week.value, billing.value] = await Promise.all([
    api('/dashboard', { token }),
    api('/dashboard/deadlines', { token }),
    api('/dashboard/activity?limit=12', { token }),
    api('/dashboard/heatmap', { token }),
    api('/dashboard/week', { token }),
    api('/dashboard/billing', { token }),
  ])
}
onMounted(() => {
  load()
  tick = setInterval(() => (now.value = Date.now()), 1000)
})
onBeforeUnmount(() => clearInterval(tick))

function money(value) {
  return Number(value || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}
function elapsed(iso) {
  const seconds = Math.max(0, Math.floor((now.value - new Date(iso)) / 1000))
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  return `${h}:${String(m).padStart(2, '0')}:${String(seconds % 60).padStart(2, '0')}`
}
function when(iso) {
  return new Date(iso).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' })
}
function date(value) {
  return new Date(value + 'T00:00').toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' })
}
function describe(item) {
  const d = item.data
  return {
    created: 'criou',
    moved: `moveu de ${columns[d.from_column]} para ${columns[d.to_column]}`,
    comment: `comentou: “${d.text}”`,
    time: `registrou ${d.hours}h em`,
  }[item.kind]
}
</script>

<template>
  <div v-if="overview" class="mx-auto max-w-6xl space-y-4">
    <div class="grid grid-cols-2 gap-3 md:grid-cols-4">
      <div class="panel p-4"><p class="text-muted">Clientes ativos</p><p class="text-2xl font-semibold tabular-nums">{{ overview.totals.clients }}</p></div>
      <div class="panel p-4"><p class="text-muted">Projetos ativos</p><p class="text-2xl font-semibold tabular-nums">{{ overview.totals.projects }}</p></div>
      <div class="panel p-4"><p class="text-muted">Cards em aberto</p><p class="text-2xl font-semibold tabular-nums">{{ overview.totals.open_cards }}</p></div>
      <div class="panel p-4"><p class="text-muted">Cronômetros rodando</p><p class="text-2xl font-semibold tabular-nums">{{ overview.totals.running_timers }}</p></div>
    </div>

    <div class="grid gap-3 lg:grid-cols-3">
      <section class="panel p-4 lg:col-span-2">
        <h2 class="mb-2 font-medium">Cards por etapa</h2>
        <ol class="grid grid-cols-2 gap-2 sm:grid-cols-3 md:grid-cols-6">
          <li v-for="col in overview.by_column" :key="col.key" class="rounded-[var(--radius-control)] bg-surface-2 px-3 py-2">
            <p class="text-[13px] text-muted">{{ col.label }}</p>
            <p class="text-xl font-semibold tabular-nums">{{ col.count }}</p>
          </li>
        </ol>
      </section>
      <section v-if="billing" class="panel p-4">
        <h2 class="mb-2 font-medium">Faturamento</h2>
        <dl class="space-y-1 text-sm">
          <div class="flex justify-between"><dt class="text-muted">Recebido no mês</dt><dd class="tabular-nums">{{ money(billing.current.received) }}</dd></div>
          <div class="flex justify-between"><dt class="text-muted">Pendente no mês</dt><dd class="tabular-nums">{{ money(billing.current.pending) }}</dd></div>
          <div class="flex justify-between"><dt class="text-muted">Mês anterior</dt><dd class="tabular-nums">{{ money(billing.previous.received) }}</dd></div>
          <div class="flex justify-between border-t border-border pt-1"><dt class="text-muted">Pendente total</dt><dd class="font-medium tabular-nums">{{ money(billing.pending_total) }}</dd></div>
        </dl>
        <RouterLink to="/payments" class="mt-2 inline-block text-accent hover:underline">Ver pagamentos</RouterLink>
      </section>
    </div>

    <div class="grid gap-3 lg:grid-cols-2">
      <section class="panel p-4">
        <h2 class="mb-2 font-medium">Em desenvolvimento agora</h2>
        <ul class="divide-y divide-border">
          <li v-for="card in overview.in_progress" :key="card.id" class="flex items-center gap-2 py-2 text-sm">
            <RouterLink :to="`/projects/${card.project_id}`" class="truncate hover:underline">
              <span class="text-muted">{{ card.client_name }} / {{ card.project_name }}</span> · #{{ card.number }} {{ card.title }}
            </RouterLink>
            <span v-if="card.time.running" class="ml-auto text-[13px] text-accent">⏱ rodando</span>
            <span v-else-if="card.time.hours" class="ml-auto text-[13px] text-muted">{{ card.time.hours }}h</span>
          </li>
          <li v-if="!overview.in_progress.length" class="py-2 text-sm text-muted">Nada em desenvolvimento.</li>
        </ul>
      </section>

      <section class="panel p-4">
        <h2 class="mb-2 font-medium">Cronômetros abertos</h2>
        <ul class="divide-y divide-border">
          <li v-for="timer in overview.running_timers" :key="timer.id" class="flex items-center gap-2 py-2 text-sm">
            <span class="font-medium tabular-nums text-accent">{{ elapsed(timer.started_at) }}</span>
            <RouterLink :to="`/projects/${timer.project_id}`" class="truncate hover:underline">{{ timer.project_name }} · #{{ timer.card_number }} {{ timer.card_title }}</RouterLink>
            <span class="ml-auto text-[13px] text-muted">{{ timer.mine ? 'você' : timer.user.name || timer.user.email }}</span>
          </li>
          <li v-if="!overview.running_timers.length" class="py-2 text-sm text-muted">Nenhum cronômetro aberto.</li>
        </ul>
      </section>

      <section class="panel p-4">
        <h2 class="mb-2 font-medium">Prazos</h2>
        <ul class="divide-y divide-border text-sm">
          <li v-for="card in deadlines.overdue" :key="card.id" class="flex items-center gap-2 py-2">
            <span class="rounded px-1 font-medium text-danger tabular-nums">{{ date(card.due_date) }}</span>
            <RouterLink :to="`/projects/${card.project_id}`" class="truncate hover:underline">{{ card.project_name }} · #{{ card.number }} {{ card.title }}</RouterLink>
            <span class="ml-auto text-[13px] text-danger">atrasado</span>
          </li>
          <li v-for="card in deadlines.upcoming" :key="card.id" class="flex items-center gap-2 py-2">
            <span class="text-muted tabular-nums">{{ date(card.due_date) }}</span>
            <RouterLink :to="`/projects/${card.project_id}`" class="truncate hover:underline">{{ card.project_name }} · #{{ card.number }} {{ card.title }}</RouterLink>
          </li>
          <li v-if="!deadlines.overdue.length && !deadlines.upcoming.length" class="py-2 text-muted">Nada vencido nem vencendo em 7 dias.</li>
        </ul>
      </section>

      <section class="panel p-4">
        <h2 class="mb-2 font-medium">Atividade recente</h2>
        <ol class="space-y-2 text-sm">
          <li v-for="(item, index) in activity" :key="index" class="flex gap-2">
            <span class="w-24 shrink-0 text-[13px] text-muted tabular-nums">{{ when(item.created) }}</span>
            <span class="min-w-0">
              <span class="font-medium">{{ item.user?.name || item.user?.email || 'Sistema' }}</span>
              {{ describe(item) }}
              <RouterLink :to="`/projects/${item.project_id}`" class="hover:underline">#{{ item.card_number }} {{ item.card_title }}</RouterLink>
              <span class="text-muted"> · {{ item.project_name }}</span>
            </span>
          </li>
          <li v-if="!activity.length" class="text-muted">Sem atividade ainda.</li>
        </ol>
      </section>
    </div>

    <div class="grid gap-3 lg:grid-cols-3">
      <section v-if="heatmap" class="panel p-4 lg:col-span-2">
        <h2 class="mb-2 font-medium">Horas por dia <span class="font-normal text-muted">· {{ heatmap.total_hours }}h em 26 semanas</span></h2>
        <Heatmap :days="heatmap.days" :weeks="heatmap.weeks" />
      </section>
      <section v-if="week" class="panel p-4">
        <h2 class="mb-2 font-medium">Esta semana <span class="font-normal text-muted">· {{ week.total_hours }}h</span></h2>
        <ul class="space-y-2 text-sm">
          <li v-for="row in week.by_project" :key="row.project_id">
            <div class="flex justify-between"><span>{{ row.client_name }} / {{ row.project_name }}</span><span class="tabular-nums">{{ row.hours }}h</span></div>
            <div class="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-surface-2"><div class="h-full rounded-full bg-accent" :style="{ width: `${week.total_hours ? (row.hours / week.total_hours) * 100 : 0}%` }"></div></div>
          </li>
          <li v-if="!week.by_project.length" class="text-muted">Nenhuma hora registrada esta semana.</li>
        </ul>
      </section>
    </div>
  </div>
</template>
