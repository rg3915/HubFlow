<script setup>
import { computed, onMounted, ref } from 'vue'
import { BASE_URL, api, mediaUrl } from '../api'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const error = ref('')
const loading = ref(false)
const input = ref(null)

const avatarUrl = computed(() => mediaUrl(auth.user?.avatar_url))

// Contas do Google/GitHub ligadas; "Conectar" refaz o login pelo provedor (liga quando o e-mail é o mesmo).
const linked = ref([])
const providers = ref([])
const unlinked = computed(() => providers.value.filter((p) => !linked.value.some((a) => a.provider === p.id)))
async function loadSocial() {
  ;[linked.value, providers.value] = await Promise.all([api('/auth/social', { token: auth.token }), api('/auth/social/providers')])
}
onMounted(() => loadSocial().catch(() => {}))
async function unlink(account) {
  if (!confirm(`Desvincular ${account.name}? Você continua entrando com e-mail e senha.`)) return
  await send(() => api(`/auth/social/${account.provider}`, { method: 'DELETE', token: auth.token }))
  await loadSocial()
}

async function send(request) {
  error.value = ''
  loading.value = true
  try {
    await request()
    await auth.fetchUser()
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

function upload(event) {
  const [file] = event.target.files
  if (!file) return
  const form = new FormData()
  form.append('file', file)
  send(() => api('/auth/me/avatar', { method: 'POST', form, token: auth.token }))
  event.target.value = ''
}

function remove() {
  send(() => api('/auth/me/avatar', { method: 'DELETE', token: auth.token }))
}
</script>

<template>
  <section class="panel max-w-[56rem] p-6">
    <div class="flex items-center gap-4">
      <img v-if="avatarUrl" :src="avatarUrl" alt="" class="h-16 w-16 rounded-full object-cover" />
      <span v-else class="flex h-16 w-16 items-center justify-center rounded-full bg-surface-2 text-[0.93rem] font-medium" aria-hidden="true">
        {{ auth.user?.first_name }}
      </span>
      <div class="min-w-0">
        <p class="truncate font-medium">{{ auth.user?.name || auth.user?.first_name }}</p>
        <p class="truncate text-muted">{{ auth.user?.email }}</p>
      </div>
    </div>

    <input ref="input" type="file" accept="image/png,image/jpeg,image/webp" hidden @change="upload" />
    <div class="mt-4 flex gap-2">
      <button class="btn btn-primary" type="button" :disabled="loading" @click="input.click()">
        {{ avatarUrl ? 'Trocar foto' : 'Enviar foto' }}
      </button>
      <button v-if="avatarUrl" class="btn btn-ghost" type="button" :disabled="loading" @click="remove">Remover</button>
    </div>
    <p class="mt-2 text-[0.93rem] text-muted">PNG, JPG ou WebP de até 2 MB.</p>

    <p v-if="error" class="mt-4 rounded-[var(--radius-control)] border border-danger/40 px-3 py-2 text-danger" role="alert">{{ error }}</p>
  </section>

  <section v-if="providers.length || linked.length" class="panel mt-4 max-w-[56rem] p-6">
    <h2 class="font-medium">Contas conectadas</h2>
    <p class="mt-1 text-[0.93rem] text-muted">Entre com Google ou GitHub usando o mesmo e-mail da sua conta no HubFlow.</p>
    <ul class="mt-3 divide-y divide-border">
      <li v-for="account in linked" :key="account.provider" class="flex items-center gap-2 py-2">
        <span class="font-medium">{{ account.name }}</span>
        <span class="truncate text-[0.93rem] text-muted">{{ account.email }}</span>
        <button type="button" class="btn btn-ghost ml-auto h-8 text-danger" :disabled="loading" @click="unlink(account)">Desvincular</button>
      </li>
      <li v-for="provider in unlinked" :key="provider.id" class="flex items-center gap-2 py-2">
        <span class="font-medium">{{ provider.name }}</span>
        <span class="text-[0.93rem] text-muted">não conectado</span>
        <a :href="`${BASE_URL}/api/auth/social/${provider.id}/start`" class="btn ml-auto h-8">Conectar</a>
      </li>
    </ul>
  </section>
</template>
