<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { mediaUrl } from '../api'
import BoardColumn from '../components/BoardColumn.vue'
import CardPanel from '../components/CardPanel.vue'
import { useAuthStore } from '../stores/auth'
import { useBoardStore } from '../stores/board'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const board = useBoardStore()
const showArchived = ref(false)

const projectId = computed(() => Number(route.params.id))
const sprintId = computed(() => (route.query.sprint ? Number(route.query.sprint) : null))
watch(
  [projectId, showArchived, sprintId],
  () => board.load(projectId.value, { archived: showArchived.value, sprintId: sprintId.value }),
  { immediate: true },
)
watch(projectId, (id) => board.connect(id), { immediate: true })
// Chegou pela busca (?card=N): abre o painel do card assim que o quadro carregar.
watch(
  () => [board.columns.length, route.query.card],
  () => {
    const number = Number(route.query.card)
    if (!number || !board.columns.length) return
    const found = board.columns.flatMap((c) => c.cards).find((c) => c.number === number)
    if (found) board.select(found)
  },
)
onBeforeUnmount(() => board.disconnect())

function filterSprint(event) {
  const value = event.target.value
  router.replace({ query: value ? { sprint: value } : {} })
}

const visibleColumns = computed(() =>
  board.columns.filter((c) => c.key !== 'archived' || showArchived.value),
)
</script>

<template>
  <div v-if="board.project && board.projectId === projectId" class="-m-6 flex h-[calc(100vh-3rem)] flex-col">
    <div class="flex items-center gap-3 border-b border-border bg-surface px-6 py-2">
      <label class="sr-only" for="sprint-filter">Sprint</label>
      <select id="sprint-filter" class="field h-8 w-auto text-sm" :value="sprintId || ''" @change="filterSprint">
        <option value="">Todas as sprints</option>
        <option v-for="sprint in board.sprints" :key="sprint.id" :value="sprint.id">
          Sprint {{ sprint.number }}{{ sprint.name ? ` · ${sprint.name}` : '' }}{{ sprint.is_open ? '' : ' (fechada)' }}
        </option>
      </select>
      <RouterLink :to="`/projects/${projectId}/sprints`" class="text-muted hover:text-text">Sprints</RouterLink>
      <RouterLink :to="`/projects/${projectId}/labels`" class="text-muted hover:text-text">Etiquetas</RouterLink>
      <RouterLink v-if="auth.can('projects.change_project')" :to="`/projects/${projectId}/integration`" class="text-muted hover:text-text">Integração</RouterLink>
      <RouterLink v-if="auth.can('projects.change_project')" :to="`/projects/${projectId}/edit`" class="text-muted hover:text-text">Configurar</RouterLink>
      <span v-if="board.viewers.length" class="ml-auto flex items-center -space-x-1" :title="`Vendo agora: ${board.viewers.map((v) => v.first_name).join(', ')}`">
        <template v-for="viewer in board.viewers.slice(0, 5)" :key="viewer.id">
          <img v-if="viewer.avatar_url" :src="mediaUrl(viewer.avatar_url)" :alt="viewer.first_name" class="h-6 w-6 rounded-full border-2 border-surface object-cover" />
          <span v-else class="flex h-6 w-6 items-center justify-center rounded-full border-2 border-surface bg-surface-2 text-[10px] font-medium">{{ viewer.first_name.slice(0, 2) }}</span>
        </template>
        <span v-if="board.viewers.length > 5" class="pl-2 text-[13px] text-muted">+{{ board.viewers.length - 5 }}</span>
      </span>
      <span class="flex items-center gap-1 text-[13px] text-muted" :class="{ 'ml-auto': !board.viewers.length }" :title="board.live ? 'Atualiza sozinho quando alguém mexer no quadro' : 'Reconectando…'">
        <span class="inline-block h-2 w-2 rounded-full" :class="board.live ? 'bg-[#2e6b4f]' : 'bg-stone-400'"></span>
        {{ board.live ? 'ao vivo' : 'offline' }}
      </span>
      <label class="flex items-center gap-2 text-muted">
        <input v-model="showArchived" type="checkbox" class="h-4 w-4 accent-[var(--accent)]" />
        Mostrar arquivadas
      </label>
    </div>
    <div class="flex min-h-0 flex-1">
      <div class="flex flex-1 gap-3 overflow-x-auto p-4">
        <BoardColumn v-for="column in visibleColumns" :key="column.key" :column="column" />
      </div>
      <CardPanel />
    </div>
  </div>
</template>
