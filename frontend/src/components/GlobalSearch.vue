<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()
const query = ref('')
const open = ref(false)
const results = ref(null)
const active = ref(0)
const input = ref(null)
const root = ref(null)
let timer

const columns = { backlog: 'Backlog', sprint: 'Sprint', doing: 'Em desenvolvimento', qa: 'QA', done: 'Concluído', archived: 'Arquivadas' }

// Resultados achatados em ordem, para navegar com as setas.
const items = computed(() => {
  if (!results.value) return []
  const r = results.value
  return [
    ...r.cards.map((c) => ({ group: 'Cards', key: `c${c.id}`, label: `#${c.number} ${c.title}`, hint: `${c.client_name} / ${c.project_name} · ${columns[c.column]}`, to: `/projects/${c.project_id}?card=${c.number}` })),
    ...r.projects.map((p) => ({ group: 'Projetos', key: `p${p.id}`, label: p.name, hint: p.client_name, to: `/projects/${p.id}` })),
    ...r.clients.map((c) => ({ group: 'Clientes', key: `k${c.id}`, label: c.name, hint: 'cliente', to: `/projects?client=${c.id}` })),
    ...r.users.map((u) => ({ group: 'Usuários', key: `u${u.id}`, label: u.name || u.email, hint: u.email, to: `/projects` })),
    ...r.labels.map((l) => ({ group: 'Etiquetas', key: `l${l.id}`, label: l.name, hint: 'etiqueta', to: `/projects/${l.project_id}/labels`, color: l.color })),
  ]
})

watch(query, (value) => {
  clearTimeout(timer)
  if (value.trim().length < 2) {
    results.value = null
    return
  }
  timer = setTimeout(async () => {
    try {
      results.value = await api(`/search?q=${encodeURIComponent(value.trim())}`, { token: auth.token })
      active.value = 0
      open.value = true
    } catch {
      results.value = null
    }
  }, 200)
})

function go(item) {
  if (!item) return
  open.value = false
  query.value = ''
  router.push(item.to)
}

function onKey(event) {
  if (!open.value || !items.value.length) return
  if (event.key === 'ArrowDown') (event.preventDefault(), (active.value = (active.value + 1) % items.value.length))
  if (event.key === 'ArrowUp') (event.preventDefault(), (active.value = (active.value - 1 + items.value.length) % items.value.length))
  if (event.key === 'Enter') (event.preventDefault(), go(items.value[active.value]))
  if (event.key === 'Escape') open.value = false
}

function shortcut(event) {
  const typing = ['INPUT', 'TEXTAREA', 'SELECT'].includes(event.target.tagName) || event.target.isContentEditable
  if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
    event.preventDefault()
    input.value?.focus()
  } else if (event.key === '/' && !typing) {
    event.preventDefault()
    input.value?.focus()
  }
}

function clickOutside(event) {
  if (!root.value?.contains(event.target)) open.value = false
}

onMounted(() => {
  document.addEventListener('keydown', shortcut)
  document.addEventListener('click', clickOutside)
})
onBeforeUnmount(() => {
  document.removeEventListener('keydown', shortcut)
  document.removeEventListener('click', clickOutside)
})
</script>

<template>
  <div ref="root" class="relative w-full max-w-md">
    <label class="sr-only" for="global-search">Buscar</label>
    <input
      id="global-search"
      ref="input"
      v-model="query"
      class="field h-8 pl-8 text-sm"
      type="search"
      placeholder="Buscar cards, projetos, clientes…  (Ctrl+K)"
      autocomplete="off"
      @focus="open = Boolean(results)"
      @keydown="onKey"
    />
    <svg class="pointer-events-none absolute left-2.5 top-2 text-muted" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" /></svg>

    <div v-if="open && results" class="panel absolute left-0 right-0 z-40 mt-1 max-h-96 overflow-y-auto p-1 shadow-sm" role="listbox">
      <template v-for="(item, index) in items" :key="item.key">
        <p v-if="index === 0 || items[index - 1].group !== item.group" class="px-2 pb-0.5 pt-2 text-[0.79rem] font-medium text-muted">{{ item.group }}</p>
        <button
          type="button"
          role="option"
          :aria-selected="index === active"
          class="flex w-full items-center gap-2 rounded-[var(--radius-control)] px-2 py-1.5 text-left text-sm"
          :class="index === active ? 'bg-surface-2' : 'hover:bg-surface-2'"
          @mouseenter="active = index"
          @click="go(item)"
        >
          <span v-if="item.color" class="h-2.5 w-2.5 shrink-0 rounded-full" :style="{ background: item.color }"></span>
          <span class="truncate">{{ item.label }}</span>
          <span class="ml-auto shrink-0 text-[0.93rem] text-muted">{{ item.hint }}</span>
        </button>
      </template>
      <p v-if="!items.length" class="px-2 py-2 text-sm text-muted">Nada encontrado para “{{ query }}”.</p>
    </div>
  </div>
</template>
