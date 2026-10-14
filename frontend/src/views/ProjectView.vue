<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import BoardColumn from '../components/BoardColumn.vue'
import CardPanel from '../components/CardPanel.vue'
import { useBoardStore } from '../stores/board'

const route = useRoute()
const router = useRouter()
const board = useBoardStore()
const showArchived = ref(false)

const projectId = computed(() => Number(route.params.id))
const sprintId = computed(() => (route.query.sprint ? Number(route.query.sprint) : null))
watch(
  [projectId, showArchived, sprintId],
  () => board.load(projectId.value, { archived: showArchived.value, sprintId: sprintId.value }),
  { immediate: true },
)

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
      <RouterLink :to="`/projects/${projectId}/edit`" class="text-muted hover:text-text">Configurar</RouterLink>
      <label class="ml-auto flex items-center gap-2 text-muted">
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
