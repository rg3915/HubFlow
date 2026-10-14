<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()

const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function submit() {
  error.value = ''
  loading.value = true
  try {
    await auth.login(email.value, password.value)
    router.push(route.query.redirect || '/')
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="panel p-6 sm:p-8">
    <h1 class="text-[28px] font-semibold leading-tight">Entrar</h1>
    <p class="mt-1 text-muted">Use o e-mail da sua conta.</p>

    <form class="mt-6 space-y-4" novalidate @submit.prevent="submit">
      <div>
        <label class="label" for="email">E-mail</label>
        <input id="email" v-model="email" class="field" type="email" autocomplete="email" required autofocus />
      </div>
      <div>
        <div class="mb-1.5 flex items-baseline justify-between">
          <label class="label mb-0" for="password">Senha</label>
          <RouterLink to="/forgot-password" class="text-accent hover:underline">Esqueci minha senha</RouterLink>
        </div>
        <input id="password" v-model="password" class="field" type="password" autocomplete="current-password" required />
      </div>

      <p v-if="error" class="rounded-[var(--radius-control)] border border-danger/40 px-3 py-2 text-danger" role="alert">
        {{ error }}
      </p>

      <button class="btn btn-primary h-10 w-full justify-center text-base" type="submit" :disabled="loading">
        {{ loading ? 'Entrando…' : 'Entrar' }}
      </button>
    </form>
  </section>
</template>
