<script setup>
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useClientsStore } from '../stores/clients'

const auth = useAuthStore()
const store = useClientsStore()
const route = useRoute()
const router = useRouter()

onMounted(() => store.load())

const clientId = computed(() => (route.query.client ? Number(route.query.client) : null))
const projects = computed(() =>
  clientId.value ? store.projects.filter((p) => p.client_id === clientId.value) : store.projects,
)

function filter(event) {
  const value = event.target.value
  router.replace({ query: value ? { client: value } : {} })
}
</script>

<template>
  <div class="mx-auto max-w-5xl">
    <div class="mb-4 flex flex-wrap items-center gap-3">
      <label class="sr-only" for="client-filter">Filtrar por cliente</label>
      <select id="client-filter" class="field h-9 w-auto text-sm" :value="clientId || ''" @change="filter">
        <option value="">Todos os clientes</option>
        <option v-for="client in store.clients" :key="client.id" :value="client.id">{{ client.name }}</option>
      </select>
      <p class="text-muted">{{ projects.length }} projeto{{ projects.length === 1 ? '' : 's' }}</p>
      <RouterLink v-if="auth.can('projects.add_project')" :to="{ path: '/projects/new', query: clientId ? { client: clientId } : {} }" class="btn btn-primary ml-auto">
        Novo projeto
      </RouterLink>
    </div>

    <section v-if="store.loaded && !projects.length" class="panel p-8 text-center">
      <h2 class="text-xl font-semibold">Nenhum projeto {{ clientId ? 'neste cliente' : 'ainda' }}</h2>
      <p class="mt-2 text-muted">Um projeto corresponde a um repositório no GitHub ou no GitLab.</p>
    </section>

    <table v-else-if="projects.length" class="panel w-full border-separate border-spacing-0 overflow-hidden">
      <thead>
        <tr class="text-left text-muted">
          <th class="border-b border-border px-4 py-2 font-medium">Projeto</th>
          <th class="border-b border-border px-4 py-2 font-medium">Cliente</th>
          <th class="border-b border-border px-4 py-2 font-medium">Repositório</th>
          <th class="border-b border-border px-4 py-2"></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="project in projects" :key="project.id" class="hover:bg-surface-2/60">
          <td class="border-b border-border px-4 py-2.5">
            <RouterLink :to="`/projects/${project.id}`" class="font-medium hover:underline">{{ project.name }}</RouterLink>
            <span v-if="!project.is_active" class="ml-2 text-muted">(arquivado)</span>
          </td>
          <td class="border-b border-border px-4 py-2.5 text-muted">{{ project.client_name }}</td>
          <td class="border-b border-border px-4 py-2.5">
            <a :href="project.repository_url" target="_blank" rel="noopener" class="text-accent hover:underline">
              {{ project.provider === 'github' ? 'GitHub' : 'GitLab' }} · {{ project.owner }}/{{ project.repo }}
            </a>
          </td>
          <td class="border-b border-border px-4 py-2.5 text-right">
            <RouterLink v-if="auth.can('projects.change_project')" :to="`/projects/${project.id}/edit`" class="text-accent hover:underline">Editar</RouterLink>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
