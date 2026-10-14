<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

// Volta do Google/GitHub: troca o código de uso único pelo token e entra.
const MESSAGES = {
  not_registered: 'Não há conta no HubFlow com esse e-mail. Peça um convite a quem administra o sistema.',
  email_not_verified: 'O provedor não confirmou um e-mail verificado. Verifique o e-mail na sua conta e tente de novo.',
  access_denied: 'Você cancelou o login.',
  invalid_state: 'O login expirou ou veio de outra aba. Tente de novo.',
  provider_error: 'Não foi possível falar com o provedor. Tente de novo em instantes.',
}
const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const error = ref('')

onMounted(async () => {
  if (route.query.error) {
    error.value = MESSAGES[route.query.error] || 'Não foi possível entrar.'
    return
  }
  try {
    await auth.loginWithCode(route.query.code)
    router.replace('/')
  } catch (e) {
    error.value = e.message
  }
})
</script>

<template>
  <section class="panel p-6 text-center sm:p-8">
    <template v-if="error">
      <h1 class="text-xl font-semibold">Não foi possível entrar</h1>
      <p class="mt-2 text-muted" role="alert">{{ error }}</p>
      <RouterLink to="/login" class="btn btn-primary mt-5">Voltar para o login</RouterLink>
    </template>
    <p v-else class="text-muted" role="status">Entrando…</p>
  </section>
</template>
