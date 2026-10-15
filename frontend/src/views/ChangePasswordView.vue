<script setup>
import { ref } from 'vue'
import { api } from '../api'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()

const current = ref('')
const password = ref('')
const confirmation = ref('')
const error = ref('')
const saved = ref(false)
const loading = ref(false)

async function submit() {
  error.value = ''
  saved.value = false
  if (password.value !== confirmation.value) {
    error.value = 'As senhas não são iguais.'
    return
  }
  loading.value = true
  try {
    await api('/auth/password/change', {
      method: 'POST',
      token: auth.token,
      body: { current_password: current.value, new_password: password.value },
    })
    saved.value = true
    current.value = password.value = confirmation.value = ''
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="panel max-w-[56rem] p-6">
    <form class="space-y-4" novalidate @submit.prevent="submit">
      <input type="email" autocomplete="username" :value="auth.user?.email" hidden />
      <div>
        <label class="label" for="current">Senha atual</label>
        <input id="current" v-model="current" class="field" type="password" autocomplete="current-password" required />
      </div>
      <div>
        <label class="label" for="password">Nova senha</label>
        <input id="password" v-model="password" class="field" type="password" autocomplete="new-password" required />
      </div>
      <div>
        <label class="label" for="confirmation">Repita a nova senha</label>
        <input id="confirmation" v-model="confirmation" class="field" type="password" autocomplete="new-password" required />
      </div>

      <p v-if="error" class="rounded-[var(--radius-control)] border border-danger/40 px-3 py-2 text-danger" role="alert">{{ error }}</p>
      <p v-if="saved" class="rounded-[var(--radius-control)] border border-accent/40 px-3 py-2" role="status">Senha alterada.</p>

      <button class="btn btn-primary" type="submit" :disabled="loading">{{ loading ? 'Salvando…' : 'Salvar nova senha' }}</button>
    </form>
  </section>
</template>
