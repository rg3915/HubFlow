<script setup>
import { ref } from 'vue'
import { api } from '../api'

const email = ref('')
const error = ref('')
const sent = ref(false)
const loading = ref(false)

async function submit() {
  error.value = ''
  loading.value = true
  try {
    await api('/auth/password/forgot', { method: 'POST', body: { email: email.value } })
    sent.value = true
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="panel p-6 sm:p-8">
    <template v-if="sent">
      <h1 class="text-[2rem] font-semibold leading-tight">Verifique seu e-mail</h1>
      <p class="mt-2 text-muted">
        Se <strong class="text-text">{{ email }}</strong> estiver cadastrado, você vai receber um link para escolher uma
        nova senha. O link vale por 24 horas.
      </p>
      <RouterLink to="/login" class="btn mt-6 w-full justify-center">Voltar para o login</RouterLink>
    </template>

    <template v-else>
      <h1 class="text-[2rem] font-semibold leading-tight">Esqueci minha senha</h1>
      <p class="mt-1 text-muted">Informe o e-mail da sua conta e enviamos um link para redefinir a senha.</p>

      <form class="mt-6 space-y-4" novalidate @submit.prevent="submit">
        <div>
          <label class="label" for="email">E-mail</label>
          <input id="email" v-model="email" class="field" type="email" autocomplete="email" required autofocus />
        </div>

        <p v-if="error" class="rounded-[var(--radius-control)] border border-danger/40 px-3 py-2 text-danger" role="alert">
          {{ error }}
        </p>

        <button class="btn btn-primary h-10 w-full justify-center text-base" type="submit" :disabled="loading">
          {{ loading ? 'Enviando…' : 'Enviar link' }}
        </button>
        <RouterLink to="/login" class="block text-center text-accent hover:underline">Voltar para o login</RouterLink>
      </form>
    </template>
  </section>
</template>
