<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useClientsStore } from '../stores/clients'

const router = useRouter()
const store = useClientsStore()

onMounted(async () => {
  if (!store.loaded) await store.load()
  if (store.clients.length) router.replace('/clients')
})
</script>

<template>
  <section v-if="store.loaded && !store.clients.length" class="panel mx-auto max-w-xl p-8 text-center">
    <h2 class="text-xl font-semibold">Comece por um cliente</h2>
    <p class="mt-2 text-muted">
      Cada cliente é dono dos seus projetos, e cada projeto tem um quadro com o trabalho em andamento.
    </p>
    <RouterLink to="/clients/new" class="btn btn-primary mt-6">Criar o primeiro cliente</RouterLink>
  </section>
</template>
