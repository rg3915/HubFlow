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
const project = computed(() => clients.projects.find((p) => p.id === projectId.value))

const labels = ref([])
const name = ref('')
const color = ref('#245e7d')
const error = ref('')

async function load() {
  if (!clients.loaded) await clients.load()
  labels.value = await api(`/projects/${projectId.value}/labels`, { token: auth.token })
}
onMounted(load)

async function create() {
  error.value = ''
  try {
    await api(`/projects/${projectId.value}/labels`, { method: 'POST', body: { name: name.value, color: color.value }, token: auth.token })
    name.value = ''
    await load()
  } catch (e) {
    error.value = e.message
  }
}

async function save(label) {
  error.value = ''
  try {
    await api(`/labels/${label.id}`, { method: 'PUT', body: { name: label.name, color: label.color }, token: auth.token })
    label.saved = true
  } catch (e) {
    error.value = e.message
  }
}

async function remove(label) {
  if (!confirm(`Excluir a etiqueta "${label.name}"? Ela sai de todos os cards.`)) return
  await api(`/labels/${label.id}`, { method: 'DELETE', token: auth.token })
  await load()
}
</script>

<template>
  <div class="max-w-[64rem]">
    <p v-if="project" class="mb-4 text-muted">{{ project.client_name }} / {{ project.name }}</p>

    <section class="panel divide-y divide-border">
      <fieldset v-for="label in labels" :key="label.id" :disabled="!auth.can('boards.change_label')" class="flex items-center gap-2 p-3">
        <input v-model="label.color" type="color" class="h-8 w-10 cursor-pointer rounded-[var(--radius-control)] border border-border bg-surface p-0.5" :aria-label="`Cor de ${label.name}`" />
        <input v-model="label.name" class="field h-8 flex-1 text-sm" type="text" :aria-label="`Nome da etiqueta ${label.name}`" />
        <button v-if="auth.can('boards.change_label')" type="button" class="btn h-8" @click="save(label)">{{ label.saved ? 'Salvo' : 'Salvar' }}</button>
        <button v-if="auth.can('boards.delete_label')" type="button" class="btn btn-ghost h-8 text-danger" @click="remove(label)">Excluir</button>
      </fieldset>
      <p v-if="!labels.length" class="p-3 text-muted">Nenhuma etiqueta ainda.</p>
    </section>

    <form v-if="auth.can('boards.add_label')" class="mt-4 flex items-center gap-2" @submit.prevent="create">
      <input v-model="color" type="color" class="h-9 w-10 cursor-pointer rounded-[var(--radius-control)] border border-border bg-surface p-0.5" aria-label="Cor da nova etiqueta" />
      <label class="sr-only" for="new-label">Nome da nova etiqueta</label>
      <input id="new-label" v-model="name" class="field h-9 flex-1" type="text" placeholder="Nova etiqueta" required />
      <button type="submit" class="btn btn-primary h-9">Criar</button>
    </form>
    <p v-if="error" class="mt-2 text-danger" role="alert">{{ error }}</p>
  </div>
</template>
