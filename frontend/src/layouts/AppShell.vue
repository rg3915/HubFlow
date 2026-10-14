<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Breadcrumb from '../components/Breadcrumb.vue'
import ThemeToggle from '../components/ThemeToggle.vue'
import UserMenu from '../components/UserMenu.vue'
import { useAuthStore } from '../stores/auth'
import { useClientsStore } from '../stores/clients'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const clientsStore = useClientsStore()

onMounted(async () => {
  if (auth.user || !auth.token) return
  try {
    await auth.fetchUser()
    await clientsStore.load()
  } catch (e) {
    // Token revogado ou expirado: volta para o login.
    if (e.status === 401) {
      await auth.logout()
      router.push({ name: 'login', query: { redirect: route.fullPath } })
    }
  }
})
const sidebarOpen = ref(false) // gaveta no celular
const collapsed = ref(localStorage.getItem('sidebar') === 'collapsed') // recolhido no desktop

function toggleSidebar() {
  if (matchMedia('(min-width: 768px)').matches) {
    collapsed.value = !collapsed.value
    localStorage.setItem('sidebar', collapsed.value ? 'collapsed' : 'open')
  } else {
    sidebarOpen.value = !sidebarOpen.value
  }
}
</script>

<template>
  <div class="flex min-h-screen">
    <!-- Barra lateral: Cliente → Projetos -->
    <aside
      class="fixed inset-y-0 left-0 z-20 flex w-60 -translate-x-full flex-col overflow-hidden border-r border-border bg-surface transition-[transform,width] md:static md:translate-x-0"
      :class="[sidebarOpen ? 'translate-x-0' : '', collapsed ? 'md:w-0 md:border-r-0' : 'md:w-60']"
      :aria-hidden="collapsed"
    >
      <RouterLink to="/" class="flex h-12 items-center border-b border-border px-4 text-base font-semibold">
        HubFlow
      </RouterLink>

      <nav class="flex-1 overflow-y-auto px-2 py-3" aria-label="Clientes e projetos">
        <RouterLink to="/clients" class="mb-2 block rounded-[var(--radius-control)] px-2 py-1 text-muted hover:bg-surface-2 hover:text-text" active-class="bg-surface-2 text-text">
          Todos os clientes
        </RouterLink>
        <RouterLink to="/projects" class="mb-2 block rounded-[var(--radius-control)] px-2 py-1 text-muted hover:bg-surface-2 hover:text-text" active-class="bg-surface-2 text-text">
          Todos os projetos
        </RouterLink>
        <template v-if="clientsStore.tree.length">
          <div v-for="client in clientsStore.tree" :key="client.id" class="mb-3">
            <RouterLink
              :to="`/clients/${client.id}/edit`"
              class="block rounded-[var(--radius-control)] px-2 py-1 font-medium hover:bg-surface-2"
            >
              {{ client.name }}
            </RouterLink>
            <RouterLink
              v-for="project in client.projects"
              :key="project.id"
              :to="`/projects/${project.id}`"
              class="block rounded-[var(--radius-control)] py-1 pl-5 pr-2 text-muted hover:bg-surface-2 hover:text-text"
              active-class="bg-surface-2 text-text"
            >
              {{ project.name }}
            </RouterLink>
          </div>
        </template>
        <p v-else class="px-2 py-1 text-muted">Nenhum cliente ainda.</p>
      </nav>

      <div class="border-t border-border p-2">
        <RouterLink to="/clients/new" class="btn w-full justify-start">
          <span class="text-muted">+</span> Novo cliente
        </RouterLink>
      </div>
    </aside>

    <div v-if="sidebarOpen" class="fixed inset-0 z-10 bg-black/40 md:hidden" @click="sidebarOpen = false" />

    <div class="flex min-w-0 flex-1 flex-col">
      <header class="flex h-12 items-center gap-3 border-b border-border bg-surface px-4">
        <button
          type="button"
          class="btn btn-ghost h-8 w-8 justify-center px-0"
          :aria-label="collapsed ? 'Mostrar menu' : 'Recolher menu'"
          :aria-expanded="!collapsed"
          @click="toggleSidebar"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M4 7h16M4 12h16M4 17h16" /></svg>
        </button>
        <Breadcrumb />
        <div class="ml-auto flex items-center gap-2">
          <ThemeToggle />
          <UserMenu />
        </div>
      </header>

      <main class="flex-1 p-6">
        <slot />
      </main>
    </div>
  </div>
</template>
