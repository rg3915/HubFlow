<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { BASE_URL, api } from '../api'
import { useAuthStore } from '../stores/auth'
import { useClientsStore } from '../stores/clients'

const route = useRoute()
const auth = useAuthStore()
const clients = useClientsStore()
const projectId = computed(() => Number(route.params.id))
const project = computed(() => clients.projects.find((p) => p.id === projectId.value))

const settings = ref(null)
const form = ref({ token: '', gitlab_project_id: '', create_issues: false, webhook_secret: '' })
const status = ref('') // mensagem de resultado (salvo, conexão, importação)
const error = ref('')
const busy = ref(false)

async function load() {
  if (!clients.loaded) await clients.load()
  settings.value = await api(`/projects/${projectId.value}/repo`, { token: auth.token })
  form.value = { token: '', gitlab_project_id: settings.value.gitlab_project_id ?? '', create_issues: settings.value.create_issues, webhook_secret: '' }
}
onMounted(load)

const webhookUrl = computed(() => (settings.value ? `${BASE_URL}${settings.value.webhook_path}` : ''))

async function run(action, okMessage) {
  error.value = status.value = ''
  busy.value = true
  try {
    const result = await action()
    status.value = typeof okMessage === 'function' ? okMessage(result) : okMessage
  } catch (e) {
    error.value = e.message
  } finally {
    busy.value = false
  }
}

function save() {
  return run(async () => {
    const body = {
      token: form.value.token || null, // vazio = mantém o atual
      gitlab_project_id: form.value.gitlab_project_id === '' ? null : Number(form.value.gitlab_project_id),
      create_issues: form.value.create_issues,
      webhook_secret: form.value.webhook_secret || null,
    }
    settings.value = await api(`/projects/${projectId.value}/repo`, { method: 'PUT', body, token: auth.token })
    form.value.token = form.value.webhook_secret = ''
  }, 'Integração salva.')
}

function clearToken() {
  return run(async () => {
    settings.value = await api(`/projects/${projectId.value}/repo`, {
      method: 'PUT',
      body: { token: '', gitlab_project_id: settings.value.gitlab_project_id, create_issues: settings.value.create_issues },
      token: auth.token,
    })
  }, 'Token removido.')
}

function check() {
  return run(
    () => api(`/projects/${projectId.value}/repo/check`, { method: 'POST', token: auth.token }),
    (r) => `Conectado a ${r.name} (${r.private ? 'privado' : 'público'}), ${r.open_issues} issues abertas.`,
  )
}

function importIssues(includeClosed) {
  return run(
    () => api(`/projects/${projectId.value}/import-issues`, { method: 'POST', body: { include_closed: includeClosed }, token: auth.token }),
    (r) => `${r.created} cards criados, ${r.skipped} issues puladas.`,
  )
}

function generateSecret() {
  const bytes = crypto.getRandomValues(new Uint8Array(24))
  form.value.webhook_secret = Array.from(bytes, (b) => b.toString(16).padStart(2, '0')).join('')
}
</script>

<template>
  <div v-if="settings && project" class="max-w-[84rem] space-y-4">
    <section class="panel p-4">
      <h2 class="font-medium">Repositório</h2>
      <p class="mt-1 text-muted">
        <a :href="settings.repository_url" target="_blank" rel="noopener" class="text-accent hover:underline">{{ settings.repository_url }}</a>
        · {{ settings.provider === 'github' ? 'GitHub' : 'GitLab' }}
      </p>

      <form class="mt-4 space-y-4" @submit.prevent="save">
        <div>
          <label class="label" for="repo-token">Token de acesso</label>
          <div class="flex gap-2">
            <input id="repo-token" v-model="form.token" class="field" type="password" autocomplete="off" :placeholder="settings.has_token ? 'Token configurado (deixe vazio para manter)' : settings.provider === 'github' ? 'ghp_…' : 'glpat-…'" />
            <button v-if="settings.has_token" type="button" class="btn" @click="clearToken">Remover</button>
          </div>
          <p class="mt-1 text-[0.93rem] text-muted">
            {{ settings.provider === 'github' ? 'Token pessoal com permissão de issues no repositório.' : 'Token com escopo api no projeto.' }} O token nunca é exibido depois de salvo.
          </p>
        </div>
        <div v-if="settings.provider === 'gitlab'">
          <label class="label" for="gitlab-id">Id numérico do projeto no GitLab</label>
          <input id="gitlab-id" v-model="form.gitlab_project_id" class="field w-48" type="number" min="1" />
        </div>
        <label class="flex items-center gap-2">
          <input v-model="form.create_issues" type="checkbox" class="h-4 w-4 accent-[var(--accent)]" />
          Criar a issue no repositório ao criar um card
        </label>
        <div>
          <label class="label" for="webhook-secret">Segredo do webhook</label>
          <div class="flex gap-2">
            <input id="webhook-secret" v-model="form.webhook_secret" class="field" type="text" autocomplete="off" :placeholder="settings.has_webhook_secret ? 'Segredo configurado (deixe vazio para manter)' : 'Gere um segredo e cole no repositório'" />
            <button type="button" class="btn" @click="generateSecret">Gerar</button>
          </div>
          <p class="mt-1 text-[0.93rem] text-muted">
            Configure no repositório um webhook de push e pull request para <code class="break-all rounded bg-surface-2 px-1">{{ webhookUrl }}</code> com este segredo.
            Commits e PRs com "close #N" concluem o card.
          </p>
        </div>
        <div class="flex flex-wrap gap-2">
          <button type="submit" class="btn btn-primary" :disabled="busy">Salvar</button>
          <button type="button" class="btn" :disabled="busy || !settings.has_token" @click="check">Testar conexão</button>
        </div>
      </form>
    </section>

    <section class="panel p-4">
      <h2 class="font-medium">Importar issues</h2>
      <p class="mt-1 text-muted">Traz as issues do repositório como cards no Backlog, sem duplicar as já importadas. Pull requests ficam de fora.</p>
      <div class="mt-3 flex flex-wrap gap-2">
        <button type="button" class="btn" :disabled="busy || !settings.has_token" @click="importIssues(false)">Importar abertas</button>
        <button type="button" class="btn" :disabled="busy || !settings.has_token" @click="importIssues(true)">Importar abertas e fechadas</button>
      </div>
    </section>

    <p v-if="status" class="rounded-[var(--radius-control)] border border-accent/40 px-3 py-2" role="status">{{ status }}</p>
    <p v-if="error" class="rounded-[var(--radius-control)] border border-danger/40 px-3 py-2 text-danger" role="alert">{{ error }}</p>
  </div>
</template>
