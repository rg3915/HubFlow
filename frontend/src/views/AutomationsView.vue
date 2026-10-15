<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../api'
import { useAuthStore } from '../stores/auth'
import { useClientsStore } from '../stores/clients'

const COLUMNS = { backlog: 'Backlog', sprint: 'Sprint', doing: 'Em desenvolvimento', qa: 'QA', done: 'Concluído', archived: 'Arquivadas' }
const TRIGGERS = { created: 'um card for criado', entered_column: 'o card entrar na coluna', sla_breached: 'o SLA estourar' }
const ACTIONS = { move: 'mover para', assign: 'definir responsável', add_label: 'adicionar etiqueta', notify: 'avisar quem criou e o responsável' }

const route = useRoute()
const auth = useAuthStore()
const clients = useClientsStore()
const projectId = computed(() => Number(route.params.id))
const project = computed(() => clients.projects.find((p) => p.id === projectId.value))

const rules = ref([])
const sla = ref({})
const slaSaved = ref(false)
const users = ref([])
const labels = ref([])
const error = ref('')
const blank = () => ({ name: '', trigger: 'entered_column', trigger_column: 'qa', action: 'move', action_column: 'done', action_user_id: null, action_label_id: null })
const form = reactive(blank())

const call = (path, options = {}) => api(path, { token: auth.token, ...options })
const body = (rule) => ({
  name: rule.name,
  is_active: rule.is_active ?? true,
  trigger: rule.trigger,
  trigger_column: rule.trigger === 'created' ? '' : rule.trigger_column,
  action: rule.action,
  action_column: rule.action === 'move' ? rule.action_column : '',
  action_user_id: rule.action === 'assign' ? rule.action_user_id : null,
  action_label_id: rule.action === 'add_label' ? rule.action_label_id : null,
})

async function load() {
  if (!clients.loaded) await clients.load()
  ;[rules.value, users.value, labels.value, sla.value] = await Promise.all([
    call(`/projects/${projectId.value}/automations`),
    call('/users'),
    call(`/projects/${projectId.value}/labels`),
    call(`/projects/${projectId.value}/sla`),
  ])
}
onMounted(load)

async function attempt(action) {
  error.value = ''
  try {
    await action()
  } catch (e) {
    error.value = e.message
  }
}

const create = () =>
  attempt(async () => {
    rules.value.push(await call(`/projects/${projectId.value}/automations`, { method: 'POST', body: body(form) }))
    Object.assign(form, blank())
  })

const toggle = (rule) =>
  attempt(async () => {
    Object.assign(rule, await call(`/automations/${rule.id}`, { method: 'PUT', body: { ...body(rule), is_active: !rule.is_active } }))
  })

const saveSla = () =>
  attempt(async () => {
    const body = Object.fromEntries(Object.entries(sla.value).map(([column, hours]) => [column, hours === '' || hours === null ? null : Number(hours)]))
    sla.value = await call(`/projects/${projectId.value}/sla`, { method: 'PUT', body })
    slaSaved.value = true
  })

async function remove(rule) {
  if (!confirm(`Excluir a automação "${rule.name}"?`)) return
  await attempt(async () => {
    await call(`/automations/${rule.id}`, { method: 'DELETE' })
    rules.value = rules.value.filter((r) => r.id !== rule.id)
  })
}
</script>

<template>
  <div class="max-w-[96rem]">
    <p v-if="project" class="mb-1 text-muted">{{ project.client_name }} / {{ project.name }}</p>
    <p class="mb-4 text-[0.93rem] text-muted">Regras que agem sozinhas nos cards deste projeto. Uma ação de automação não dispara outra.</p>

    <section class="panel divide-y divide-border">
      <div v-for="rule in rules" :key="rule.id" class="flex items-center gap-3 p-3">
        <label class="flex shrink-0 items-center" :title="rule.is_active ? 'Ligada' : 'Desligada'">
          <input type="checkbox" class="h-4 w-4 accent-[var(--accent)]" :checked="rule.is_active" :aria-label="`Ligar ${rule.name}`" @change="toggle(rule)" />
        </label>
        <div class="min-w-0 flex-1" :class="{ 'opacity-60': !rule.is_active }">
          <p class="font-medium">{{ rule.name }}</p>
          <p class="text-[0.93rem] text-muted">{{ rule.description }}</p>
        </div>
        <button type="button" class="btn btn-ghost h-8 text-danger" @click="remove(rule)">Excluir</button>
      </div>
      <p v-if="!rules.length" class="p-3 text-muted">Nenhuma automação ainda.</p>
    </section>

    <form class="panel mt-4 space-y-3 p-4" @submit.prevent="create">
      <div>
        <label class="label" for="rule-name">Nova automação</label>
        <input id="rule-name" v-model="form.name" class="field h-9" type="text" placeholder="Ex.: QA aprovado vai para Concluído" required />
      </div>
      <div class="flex flex-wrap items-center gap-2 text-sm">
        <span>Quando</span>
        <select v-model="form.trigger" class="field h-9 w-auto" aria-label="Gatilho">
          <option v-for="(text, key) in TRIGGERS" :key="key" :value="key">{{ text }}</option>
        </select>
        <select v-if="form.trigger !== 'created'" v-model="form.trigger_column" class="field h-9 w-auto" aria-label="Coluna do gatilho" :required="form.trigger === 'entered_column'">
          <option v-if="form.trigger === 'sla_breached'" value="">em qualquer coluna</option>
          <option v-for="(text, key) in COLUMNS" :key="key" :value="key">{{ form.trigger === 'sla_breached' ? `em ${text}` : text }}</option>
        </select>
        <span>→</span>
        <select v-model="form.action" class="field h-9 w-auto" aria-label="Ação">
          <option v-for="(text, key) in ACTIONS" :key="key" :value="key">{{ text }}</option>
        </select>
        <select v-if="form.action === 'move'" v-model="form.action_column" class="field h-9 w-auto" aria-label="Coluna de destino" required>
          <option v-for="(text, key) in COLUMNS" :key="key" :value="key">{{ text }}</option>
        </select>
        <select v-if="form.action === 'assign'" v-model="form.action_user_id" class="field h-9 w-auto" aria-label="Responsável" required>
          <option v-for="user in users" :key="user.id" :value="user.id">{{ user.name || user.email }}</option>
        </select>
        <select v-if="form.action === 'add_label'" v-model="form.action_label_id" class="field h-9 w-auto" aria-label="Etiqueta" required>
          <option v-for="label in labels" :key="label.id" :value="label.id">{{ label.name }}</option>
        </select>
      </div>
      <button type="submit" class="btn btn-primary h-9">Criar automação</button>
    </form>
    <p v-if="error" class="mt-2 text-danger" role="alert">{{ error }}</p>

    <form class="panel mt-6 p-4" @submit.prevent="saveSla">
      <h2 class="font-medium">SLA por coluna</h2>
      <p class="mb-3 text-[0.93rem] text-muted">Tempo máximo, em horas, que um card pode ficar em cada coluna. Vazio = sem SLA. Ao estourar, o card fica marcado no quadro e as automações de "SLA estourar" rodam (verificação a cada 15 minutos).</p>
      <div class="grid grid-cols-2 gap-3 sm:grid-cols-3">
        <div v-for="(text, key) in COLUMNS" :key="key">
          <label class="label" :for="`sla-${key}`">{{ text }}</label>
          <input :id="`sla-${key}`" v-model="sla[key]" class="field h-9" type="number" min="1" step="1" placeholder="—" @input="slaSaved = false" />
        </div>
      </div>
      <button type="submit" class="btn btn-primary mt-3 h-9">{{ slaSaved ? 'Salvo' : 'Salvar SLA' }}</button>
    </form>
  </div>
</template>
