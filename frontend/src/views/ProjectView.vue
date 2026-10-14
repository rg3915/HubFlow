<script setup>
// Quadro do projeto entra na #34. Por ora, só os dados do projeto.
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useClientsStore } from '../stores/clients'

const route = useRoute()
const store = useClientsStore()
onMounted(() => store.loaded || store.load())
const project = computed(() => store.projects.find((p) => p.id === Number(route.params.id)))
</script>

<template>
  <section v-if="project" class="panel max-w-lg p-6">
    <h2 class="text-xl font-semibold">{{ project.client_name }} / {{ project.name }}</h2>
    <a :href="project.repository_url" target="_blank" rel="noopener" class="text-accent hover:underline">{{ project.repository_url }}</a>
    <p v-if="project.description" class="mt-2 text-muted">{{ project.description }}</p>
    <p class="mt-4 text-muted">O quadro deste projeto chega em breve.</p>
  </section>
</template>
