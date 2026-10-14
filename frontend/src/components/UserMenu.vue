<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()
const open = ref(false)
const root = ref(null)

function close(event) {
  if (!root.value?.contains(event.target)) open.value = false
}

onMounted(() => document.addEventListener('click', close))
onBeforeUnmount(() => document.removeEventListener('click', close))

async function logout() {
  await auth.logout()
  router.push('/login')
}
</script>

<template>
  <div ref="root" class="relative">
    <button
      type="button"
      class="btn btn-ghost h-8 max-w-56 px-2"
      aria-haspopup="menu"
      :aria-expanded="open"
      @click="open = !open"
    >
      <span class="hidden truncate sm:inline">{{ auth.user?.name || auth.user?.email || '…' }}</span>
      <span class="flex h-7 w-7 items-center justify-center rounded-full bg-surface-2 text-[12px] font-medium uppercase sm:hidden" :aria-label="auth.user?.email">{{ (auth.user?.first_name || '?').slice(0, 2) }}</span>
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="text-muted"><path d="m6 9 6 6 6-6" /></svg>
    </button>

    <div v-if="open" role="menu" class="panel absolute right-0 z-30 mt-1 w-56 p-1 shadow-sm">
      <p v-if="auth.user?.name" class="truncate px-2 pb-1 pt-1.5 text-muted">{{ auth.user.email }}</p>
      <RouterLink to="/settings/profile" role="menuitem" class="block rounded-[var(--radius-control)] px-2 py-1.5 hover:bg-surface-2" @click="open = false">
        Perfil
      </RouterLink>
      <RouterLink to="/settings/password" role="menuitem" class="block rounded-[var(--radius-control)] px-2 py-1.5 hover:bg-surface-2" @click="open = false">
        Trocar senha
      </RouterLink>
      <button type="button" role="menuitem" class="block w-full rounded-[var(--radius-control)] px-2 py-1.5 text-left hover:bg-surface-2" @click="logout">
        Sair
      </button>
    </div>
  </div>
</template>
