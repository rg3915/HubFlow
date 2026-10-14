<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import BoardColumn from '../components/BoardColumn.vue'
import CardPanel from '../components/CardPanel.vue'
import { useBoardStore } from '../stores/board'

const route = useRoute()
const board = useBoardStore()
const showArchived = ref(false)

const projectId = computed(() => Number(route.params.id))
watch([projectId, showArchived], () => board.load(projectId.value, { archived: showArchived.value }), { immediate: true })

const visibleColumns = computed(() =>
  board.columns.filter((c) => c.key !== 'archived' || showArchived.value),
)
</script>

<template>
  <div v-if="board.project && board.projectId === projectId" class="-m-6 flex h-[calc(100vh-3rem)] flex-col">
    <div class="flex items-center gap-3 border-b border-border bg-surface px-6 py-2">
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
