<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useClientsStore } from '../stores/clients'

const route = useRoute()
const router = useRouter()
const store = useClientsStore()

const id = route.params.id ? Number(route.params.id) : null
const name = ref('')
const emails = ref('')
const isActive = ref(true)
const error = ref('')
const loading = ref(false)

onMounted(async () => {
  if (!id) return
  if (!store.loaded) await store.load()
  const client = store.clients.find((c) => c.id === id)
  if (!client) return router.replace('/clients')
  name.value = client.name
  emails.value = client.emails.join(', ')
  isActive.value = client.is_active
})

async function submit() {
  error.value = ''
  loading.value = true
  try {
    const list = emails.value.split(',').map((e) => e.trim()).filter(Boolean)
    await store.saveClient(id, { name: name.value, emails: list, is_active: isActive.value })
    router.push('/clients')
  } catch (e) {
    error.value = e.status === 422 ? 'Confira os e-mails: um deles não é válido.' : e.message
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="panel max-w-lg p-6">
    <form class="space-y-4" novalidate @submit.prevent="submit">
      <div>
        <label class="label" for="name">Nome</label>
        <input id="name" v-model="name" class="field" type="text" required autofocus />
      </div>
      <div>
        <label class="label" for="emails">E-mails de notificação</label>
        <input id="emails" v-model="emails" class="field" type="text" placeholder="ana@empresa.com, bruno@empresa.com" />
        <p class="mt-1 text-muted">Opcional. Separe vários e-mails por vírgula. Os projetos sem e-mails usam estes.</p>
      </div>
      <label v-if="id" class="flex items-center gap-2">
        <input v-model="isActive" type="checkbox" class="h-4 w-4 accent-[var(--accent)]" />
        Cliente ativo
      </label>

      <p v-if="error" class="rounded-[var(--radius-control)] border border-danger/40 px-3 py-2 text-danger" role="alert">{{ error }}</p>

      <div class="flex gap-2">
        <button class="btn btn-primary" type="submit" :disabled="loading">{{ id ? 'Salvar alterações' : 'Criar cliente' }}</button>
        <RouterLink to="/clients" class="btn btn-ghost">Cancelar</RouterLink>
      </div>
    </form>
  </section>
</template>
