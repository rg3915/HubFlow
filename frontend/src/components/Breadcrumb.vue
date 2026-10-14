<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useClientsStore } from '../stores/clients'

const route = useRoute()
const clients = useClientsStore()

// Caminho = hierarquia do domínio: Clientes › Cliente › Projeto › Página.
const crumbs = computed(() => {
  const id = Number(route.params.id)
  const items = []
  const name = route.name
  const project = name?.startsWith('project') && id ? clients.projects.find((p) => p.id === id) : null
  const client = name?.startsWith('client') && id ? clients.clients.find((c) => c.id === id) : null

  if (name === 'home') return [{ label: 'Dashboard' }]
  if (name?.startsWith('client')) {
    items.push({ label: 'Clientes', to: '/clients' })
    if (client) items.push({ label: client.name, to: `/clients/${client.id}/edit` })
    if (name === 'client-new') items.push({ label: 'Novo cliente' })
    if (name === 'client-edit') items.push({ label: 'Editar' })
  } else if (name?.startsWith('project')) {
    if (project) {
      items.push({ label: project.client_name, to: `/projects?client=${project.client_id}` })
      items.push({ label: project.name, to: `/projects/${project.id}` })
    } else {
      items.push({ label: 'Projetos', to: '/projects' })
    }
    if (name === 'project-new') items.push({ label: 'Novo projeto' })
    if (name === 'project-edit') items.push({ label: 'Configurar' })
    if (name === 'project-labels') items.push({ label: 'Etiquetas' })
    if (name === 'project-fields') items.push({ label: 'Campos' })
    if (name === 'project-sprints') items.push({ label: 'Sprints' })
    if (name === 'project-integration') items.push({ label: 'Integração' })
    if (name === 'project') items.push({ label: 'Quadro' })
  } else {
    items.push({ label: route.meta.title })
  }
  return items
})
</script>

<template>
  <nav aria-label="Caminho" class="min-w-0">
    <ol class="flex items-center gap-1 truncate">
      <li v-for="(crumb, index) in crumbs" :key="index" class="flex items-center gap-1 truncate">
        <span v-if="index" class="text-muted" aria-hidden="true">›</span>
        <RouterLink v-if="crumb.to && index < crumbs.length - 1" :to="crumb.to" class="truncate text-muted hover:text-text">{{ crumb.label }}</RouterLink>
        <h1 v-else class="truncate text-xl font-semibold" aria-current="page">{{ crumb.label }}</h1>
      </li>
    </ol>
  </nav>
</template>
