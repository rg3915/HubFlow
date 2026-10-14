<script setup>
import { onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useClientsStore } from '../stores/clients'

const auth = useAuthStore()

const store = useClientsStore()
onMounted(() => store.load())
</script>

<template>
  <div class="mx-auto max-w-5xl">
    <div class="mb-4 flex items-center justify-between">
      <p class="text-muted">{{ store.clients.length }} cliente{{ store.clients.length === 1 ? '' : 's' }}</p>
      <RouterLink v-if="auth.can('clients.add_client')" to="/clients/new" class="btn btn-primary">Novo cliente</RouterLink>
    </div>

    <section v-if="store.loaded && !store.clients.length" class="panel p-8 text-center">
      <h2 class="text-xl font-semibold">Nenhum cliente ainda</h2>
      <p class="mt-2 text-muted">O cliente é o dono dos projetos. Cadastre o primeiro para começar.</p>
    </section>

    <table v-else-if="store.clients.length" v-stack class="stack-table panel w-full border-separate border-spacing-0 overflow-hidden">
      <thead>
        <tr class="text-left text-muted">
          <th class="border-b border-border px-4 py-2 font-medium">Cliente</th>
          <th class="border-b border-border px-4 py-2 font-medium">Projetos</th>
          <th class="border-b border-border px-4 py-2 font-medium">E-mails de notificação</th>
          <th class="border-b border-border px-4 py-2"></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="client in store.tree" :key="client.id" class="hover:bg-surface-2/60">
          <td class="border-b border-border px-4 py-2.5">
            <span class="font-medium">{{ client.name }}</span>
            <span v-if="!client.is_active" class="ml-2 text-muted">(arquivado)</span>
          </td>
          <td class="border-b border-border px-4 py-2.5 tabular-nums">{{ client.projects.length }}</td>
          <td class="border-b border-border px-4 py-2.5 text-muted">{{ client.emails.join(', ') || '—' }}</td>
          <td class="border-b border-border px-4 py-2.5 text-right">
            <RouterLink v-if="auth.can('clients.change_client')" :to="`/clients/${client.id}/edit`" class="text-accent hover:underline">Editar</RouterLink>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
