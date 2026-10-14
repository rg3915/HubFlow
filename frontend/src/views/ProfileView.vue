<script setup>
import { computed, ref } from 'vue'
import { BASE_URL, api } from '../api'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const error = ref('')
const loading = ref(false)
const input = ref(null)

const avatarUrl = computed(() => (auth.user?.avatar_url ? BASE_URL + auth.user.avatar_url : null))

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
  <section class="panel max-w-md p-6">
    <div class="flex items-center gap-4">
      <img v-if="avatarUrl" :src="avatarUrl" alt="" class="h-16 w-16 rounded-full object-cover" />
      <span v-else class="flex h-16 w-16 items-center justify-center rounded-full bg-surface-2 text-[13px] font-medium" aria-hidden="true">
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
    <p class="mt-2 text-[13px] text-muted">PNG, JPG ou WebP de até 2 MB.</p>

    <p v-if="error" class="mt-4 rounded-[var(--radius-control)] border border-danger/40 px-3 py-2 text-danger" role="alert">{{ error }}</p>
  </section>
</template>
