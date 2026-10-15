<script setup>
import { useRoute } from 'vue-router'
import { DEMO } from './api'
import AppShell from './layouts/AppShell.vue'
import AuthLayout from './layouts/AuthLayout.vue'

const route = useRoute()

async function restaurar() {
  if (import.meta.env.VITE_DEMO === '1') (await import('./demo/api.js')).restaurarDemo()
  location.reload()
}
</script>

<template>
  <p v-if="DEMO" class="bg-accent px-4 py-1.5 text-center text-[0.93rem] text-white">
    Demonstração com dados de exemplo: nada vai para um servidor.
    <button type="button" class="ml-2 underline" @click="restaurar">Restaurar os dados</button>
    <a href="https://github.com/rg3915/HubFlow" class="ml-2 underline">Código no GitHub</a>
  </p>
  <component :is="route.meta.layout === 'auth' ? AuthLayout : AppShell">
    <RouterView />
  </component>
</template>
