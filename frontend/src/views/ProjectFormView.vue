<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useClientsStore } from '../stores/clients'

const route = useRoute()
const router = useRouter()
const store = useClientsStore()

const id = route.params.id ? Number(route.params.id) : null
const form = ref({
  client_id: route.query.client ? Number(route.query.client) : '',
  name: '',
  provider: 'github',
  owner: '',
  repo: '',
  description: '',
  emails: '',
  is_active: true,
  notify_on_created: true,
  notify_on_moved: true,
  notify_on_done: true,
})

const events = [
  ['notify_on_created', 'Card criado'],
  ['notify_on_moved', 'Card movido de coluna'],
  ['notify_on_done', 'Card concluído'],
]
const error = ref('')
const loading = ref(false)

onMounted(async () => {
  if (!store.loaded) await store.load()
  if (!id) return
  const project = store.projects.find((p) => p.id === id)
  if (!project) return router.replace('/projects')
  form.value = { ...project, emails: project.emails.join(', ') }
})

async function submit() {
  error.value = ''
  loading.value = true
  try {
    const emails = form.value.emails.split(',').map((e) => e.trim()).filter(Boolean)
    const data = { ...form.value, client_id: Number(form.value.client_id), emails }
    await store.saveProject(id, data)
    router.push({ path: '/projects', query: { client: data.client_id } })
  } catch (e) {
    error.value = e.status === 422 ? 'Confira os campos: cliente, provedor, owner e repo são obrigatórios.' : e.message
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="panel max-w-[64rem] p-6">
    <form class="space-y-4" novalidate @submit.prevent="submit">
      <div>
        <label class="label" for="client">Cliente</label>
        <select id="client" v-model="form.client_id" class="field" required>
          <option value="" disabled>Escolha o cliente</option>
          <option v-for="client in store.clients" :key="client.id" :value="client.id">{{ client.name }}</option>
        </select>
      </div>
      <div>
        <label class="label" for="name">Nome do projeto</label>
        <input id="name" v-model="form.name" class="field" type="text" required />
      </div>
      <fieldset>
        <legend class="label">Provedor</legend>
        <div class="flex gap-4">
          <label class="flex items-center gap-2"><input v-model="form.provider" type="radio" value="github" class="accent-[var(--accent)]" /> GitHub</label>
          <label class="flex items-center gap-2"><input v-model="form.provider" type="radio" value="gitlab" class="accent-[var(--accent)]" /> GitLab</label>
        </div>
      </fieldset>
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="label" for="owner">Owner</label>
          <input id="owner" v-model="form.owner" class="field" type="text" placeholder="acme" required />
        </div>
        <div>
          <label class="label" for="repo">Repositório</label>
          <input id="repo" v-model="form.repo" class="field" type="text" placeholder="loja" required />
        </div>
      </div>
      <p v-if="form.owner && form.repo" class="-mt-2 text-muted">
        https://{{ form.provider }}.com/{{ form.owner }}/{{ form.repo }}
      </p>
      <div>
        <label class="label" for="description">Descrição</label>
        <textarea id="description" v-model="form.description" class="field h-20 py-2" rows="2"></textarea>
      </div>
      <fieldset class="rounded-[var(--radius-panel)] border border-border p-4">
        <legend class="px-1 font-medium">Avisos por e-mail</legend>
        <div>
          <label class="label" for="emails">Quem recebe</label>
          <input id="emails" v-model="form.emails" class="field" type="text" placeholder="dev@hubflow.com, gerente@hubflow.com" />
          <p class="mt-1 text-muted">Opcional. Vazio = usa os e-mails do cliente.</p>
        </div>
        <div class="mt-3 space-y-1.5">
          <p class="label mb-1">Quando avisar</p>
          <label v-for="[key, label] in events" :key="key" class="flex items-center gap-2">
            <input v-model="form[key]" type="checkbox" class="h-4 w-4 accent-[var(--accent)]" />
            {{ label }}
          </label>
        </div>
      </fieldset>
      <label v-if="id" class="flex items-center gap-2">
        <input v-model="form.is_active" type="checkbox" class="h-4 w-4 accent-[var(--accent)]" />
        Projeto ativo
      </label>

      <p v-if="error" class="rounded-[var(--radius-control)] border border-danger/40 px-3 py-2 text-danger" role="alert">{{ error }}</p>

      <div class="flex gap-2">
        <button class="btn btn-primary" type="submit" :disabled="loading">{{ id ? 'Salvar alterações' : 'Criar projeto' }}</button>
        <RouterLink to="/projects" class="btn btn-ghost">Cancelar</RouterLink>
      </div>
    </form>
  </section>
</template>
