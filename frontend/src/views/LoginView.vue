<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { BASE_URL, api } from '../api'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()

const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)
const providers = ref([]) // só os configurados no backend
onMounted(async () => (providers.value = await api('/auth/social/providers').catch(() => [])))

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

    <template v-if="providers.length">
      <p class="my-5 flex items-center gap-3 text-[13px] text-muted"><span class="h-px flex-1 bg-border"></span>ou<span class="h-px flex-1 bg-border"></span></p>
      <div class="space-y-2">
        <a v-for="provider in providers" :key="provider.id" :href="`${BASE_URL}/api/auth/social/${provider.id}/start`" class="btn h-10 w-full justify-center gap-2">
          <svg v-if="provider.id === 'google'" width="18" height="18" viewBox="0 0 48 48" aria-hidden="true"><path fill="#EA4335" d="M24 9.5c3.5 0 6.6 1.2 9.1 3.6l6.8-6.8C35.8 2.4 30.3 0 24 0 14.6 0 6.6 5.4 2.7 13.3l7.9 6.1C12.5 13.6 17.8 9.5 24 9.5z"/><path fill="#4285F4" d="M46.5 24.5c0-1.6-.1-3.1-.4-4.5H24v9h12.7c-.6 3-2.3 5.5-4.8 7.2l7.7 6c4.5-4.2 6.9-10.3 6.9-17.7z"/><path fill="#FBBC05" d="M10.6 28.6A14.5 14.5 0 0 1 9.5 24c0-1.6.3-3.1.8-4.6l-7.9-6.1A24 24 0 0 0 0 24c0 3.9.9 7.5 2.7 10.7l7.9-6.1z"/><path fill="#34A853" d="M24 48c6.5 0 11.9-2.1 15.9-5.8l-7.7-6c-2.1 1.4-4.9 2.3-8.2 2.3-6.2 0-11.5-4.1-13.4-9.9l-7.9 6.1C6.6 42.6 14.6 48 24 48z"/></svg>
          <svg v-else width="18" height="18" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M8 0C3.6 0 0 3.6 0 8c0 3.5 2.3 6.5 5.5 7.6.4.1.5-.2.5-.4v-1.4c-2.2.5-2.7-1-2.7-1-.4-.9-.9-1.2-.9-1.2-.7-.5.1-.5.1-.5.8.1 1.2.8 1.2.8.7 1.2 1.9.9 2.3.7.1-.5.3-.9.5-1.1-1.8-.2-3.6-.9-3.6-4 0-.9.3-1.6.8-2.1-.1-.2-.4-1 .1-2.1 0 0 .7-.2 2.2.8.6-.2 1.3-.3 2-.3s1.4.1 2 .3c1.5-1 2.2-.8 2.2-.8.4 1.1.2 1.9.1 2.1.5.6.8 1.3.8 2.1 0 3.1-1.9 3.7-3.6 3.9.3.3.6.8.6 1.5v2.2c0 .2.1.5.6.4C13.7 14.5 16 11.5 16 8c0-4.4-3.6-8-8-8z"/></svg>
          Entrar com {{ provider.name }}
        </a>
      </div>
    </template>
  </section>
</template>
