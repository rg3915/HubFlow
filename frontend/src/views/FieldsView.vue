<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../api'
import { useAuthStore } from '../stores/auth'
import { useClientsStore } from '../stores/clients'

const KINDS = { text: 'Texto', number: 'Número', date: 'Data', select: 'Seleção', bool: 'Sim/não' }

const route = useRoute()
const auth = useAuthStore()
const clients = useClientsStore()
const projectId = computed(() => Number(route.params.id))
const project = computed(() => clients.projects.find((p) => p.id === projectId.value))

const fields = ref([])
const form = reactive({ name: '', kind: 'text', options: '', required: false })
const error = ref('')

const call = (path, options = {}) => api(path, { token: auth.token, ...options })
// Opções editadas como texto separado por vírgula.
const withText = (field) => ({ ...field, optionsText: field.options.join(', ') })
const toBody = (f, options) => ({ name: f.name, kind: f.kind, required: f.required, options: f.kind === 'select' ? options.split(',').map((o) => o.trim()).filter(Boolean) : [] })

async function load() {
  if (!clients.loaded) await clients.load()
  fields.value = (await call(`/projects/${projectId.value}/fields`)).map(withText)
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
    await call(`/projects/${projectId.value}/fields`, { method: 'POST', body: toBody(form, form.options) })
    Object.assign(form, { name: '', kind: 'text', options: '', required: false })
    await load()
  })

const save = (field) =>
  attempt(async () => {
    Object.assign(field, withText(await call(`/fields/${field.id}`, { method: 'PUT', body: toBody(field, field.optionsText) })), { saved: true })
  })

async function remove(field) {
  if (!confirm(`Excluir o campo "${field.name}"? Os valores dele somem de todos os cards.`)) return
  await attempt(async () => {
    await call(`/fields/${field.id}`, { method: 'DELETE' })
    await load()
  })
}

const move = (index, step) =>
  attempt(async () => {
    const ids = fields.value.map((f) => f.id)
    ;[ids[index], ids[index + step]] = [ids[index + step], ids[index]]
    fields.value = (await call(`/projects/${projectId.value}/fields/order`, { method: 'PUT', body: { ids } })).map(withText)
  })
</script>

<template>
  <div class="max-w-3xl">
    <p v-if="project" class="mb-1 text-muted">{{ project.client_name }} / {{ project.name }}</p>
    <p class="mb-4 text-[13px] text-muted">Campos extras de todos os cards deste projeto. Os obrigatórios precisam ser preenchidos ao criar o card.</p>

    <section class="panel divide-y divide-border">
      <div v-for="(field, index) in fields" :key="field.id" class="flex flex-wrap items-center gap-2 p-3">
        <div class="flex flex-col">
          <button type="button" class="btn btn-ghost h-5 w-6 justify-center px-0 text-muted" :disabled="index === 0" :aria-label="`Subir ${field.name}`" @click="move(index, -1)">▲</button>
          <button type="button" class="btn btn-ghost h-5 w-6 justify-center px-0 text-muted" :disabled="index === fields.length - 1" :aria-label="`Descer ${field.name}`" @click="move(index, 1)">▼</button>
        </div>
        <input v-model="field.name" class="field h-8 min-w-36 flex-1 text-sm" type="text" :aria-label="`Nome do campo ${field.name}`" @input="field.saved = false" />
        <select v-model="field.kind" class="field h-8 w-auto text-sm" :aria-label="`Tipo de ${field.name}`" @change="field.saved = false">
          <option v-for="(label, key) in KINDS" :key="key" :value="key">{{ label }}</option>
        </select>
        <input
          v-if="field.kind === 'select'"
          v-model="field.optionsText"
          class="field h-8 min-w-40 flex-1 text-sm"
          type="text"
          placeholder="Opções, separadas por vírgula"
          :aria-label="`Opções de ${field.name}`"
          @input="field.saved = false"
        />
        <label class="flex items-center gap-1.5 text-sm">
          <input v-model="field.required" type="checkbox" class="h-4 w-4 accent-[var(--accent)]" @change="field.saved = false" /> Obrigatório
        </label>
        <button type="button" class="btn h-8" @click="save(field)">{{ field.saved ? 'Salvo' : 'Salvar' }}</button>
        <button type="button" class="btn btn-ghost h-8 text-danger" @click="remove(field)">Excluir</button>
      </div>
      <p v-if="!fields.length" class="p-3 text-muted">Nenhum campo ainda.</p>
    </section>

    <form class="panel mt-4 flex flex-wrap items-end gap-3 p-4" @submit.prevent="create">
      <div class="min-w-40 flex-1">
        <label class="label" for="field-name">Novo campo</label>
        <input id="field-name" v-model="form.name" class="field h-9" type="text" placeholder="Ex.: Prioridade" required />
      </div>
      <div>
        <label class="label" for="field-kind">Tipo</label>
        <select id="field-kind" v-model="form.kind" class="field h-9 w-auto">
          <option v-for="(label, key) in KINDS" :key="key" :value="key">{{ label }}</option>
        </select>
      </div>
      <div v-if="form.kind === 'select'" class="min-w-48 flex-1">
        <label class="label" for="field-options">Opções</label>
        <input id="field-options" v-model="form.options" class="field h-9" type="text" placeholder="Alta, Média, Baixa" required />
      </div>
      <label class="flex h-9 items-center gap-1.5 text-sm">
        <input v-model="form.required" type="checkbox" class="h-4 w-4 accent-[var(--accent)]" /> Obrigatório
      </label>
      <button type="submit" class="btn btn-primary h-9">Criar campo</button>
    </form>
    <p v-if="error" class="mt-2 text-danger" role="alert">{{ error }}</p>
  </div>
</template>
