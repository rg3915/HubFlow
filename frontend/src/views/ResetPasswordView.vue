<script setup>
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../api'

const route = useRoute()

const password = ref('')
const confirmation = ref('')
const error = ref('')
const done = ref(false)
const loading = ref(false)

async function submit() {
  error.value = ''
  if (password.value !== confirmation.value) {
    error.value = 'As senhas não são iguais.'
    return
  }
  loading.value = true
  try {
    const { uid, token } = route.params
    await api('/auth/password/reset', { method: 'POST', body: { uid, token, password: password.value } })
    done.value = true
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="panel p-6 sm:p-8">
    <template v-if="done">
      <h1 class="text-[28px] font-semibold leading-tight">Senha redefinida</h1>
      <p class="mt-2 text-muted">Sua nova senha já vale. Entre para continuar.</p>
      <RouterLink to="/login" class="btn btn-primary mt-6 h-10 w-full justify-center text-base">Entrar</RouterLink>
    </template>

    <template v-else>
      <h1 class="text-[28px] font-semibold leading-tight">Nova senha</h1>
      <p class="mt-1 text-muted">Escolha uma senha com pelo menos 8 caracteres.</p>

      <form class="mt-6 space-y-4" novalidate @submit.prevent="submit">
        <div>
          <label class="label" for="password">Nova senha</label>
          <input id="password" v-model="password" class="field" type="password" autocomplete="new-password" required autofocus />
        </div>
        <div>
          <label class="label" for="confirmation">Repita a senha</label>
          <input id="confirmation" v-model="confirmation" class="field" type="password" autocomplete="new-password" required />
        </div>

        <p v-if="error" class="rounded-[var(--radius-control)] border border-danger/40 px-3 py-2 text-danger" role="alert">
          {{ error }}
          <RouterLink v-if="error.includes('Link')" to="/forgot-password" class="ml-1 underline">Pedir um novo link</RouterLink>
        </p>

        <button class="btn btn-primary h-10 w-full justify-center text-base" type="submit" :disabled="loading">
          {{ loading ? 'Salvando…' : 'Salvar nova senha' }}
        </button>
      </form>
    </template>
  </section>
</template>
