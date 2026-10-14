<script setup>
import Sortable from 'sortablejs'
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { useBoardStore } from '../stores/board'

const board = useBoardStore()
const text = ref('')
const list = ref(null)
let sortable

onMounted(() => {
  sortable = Sortable.create(list.value, {
    handle: '.handle',
    animation: 150,
    onEnd(event) {
      if (event.oldIndex === event.newIndex) return
      event.from.insertBefore(event.item, event.from.children[event.oldIndex] || null)
      const ids = board.checklist.map((i) => i.id)
      const [moved] = ids.splice(event.oldIndex, 1)
      ids.splice(event.newIndex, 0, moved)
      board.reorderChecklist(ids)
    },
  })
})
onBeforeUnmount(() => sortable?.destroy())

async function add() {
  if (!text.value.trim()) return
  await board.addChecklistItem(text.value.trim())
  text.value = ''
}
</script>

<template>
  <div>
    <p v-if="board.checklist.length" class="mb-2 text-[13px] text-muted tabular-nums">
      {{ board.checklist.filter((i) => i.done).length }} de {{ board.checklist.length }} feitos
    </p>
    <ul ref="list" class="space-y-1">
      <li v-for="item in board.checklist" :key="item.id" class="group flex items-center gap-2 rounded-[var(--radius-control)] px-1 py-0.5 hover:bg-surface-2">
        <span class="handle cursor-grab text-muted" aria-hidden="true">⋮</span>
        <input :id="`check-${item.id}`" type="checkbox" class="h-4 w-4 accent-[var(--accent)]" :checked="item.done" @change="board.toggleChecklistItem(item)" />
        <label :for="`check-${item.id}`" class="flex-1 text-sm" :class="{ 'text-muted line-through': item.done }">{{ item.text }}</label>
        <button type="button" class="text-[13px] text-muted opacity-0 hover:text-danger group-hover:opacity-100 focus:opacity-100" aria-label="Excluir item" @click="board.deleteChecklistItem(item)">×</button>
      </li>
    </ul>
    <form class="mt-2 flex gap-2" @submit.prevent="add">
      <label class="sr-only" for="checklist-new">Novo item</label>
      <input id="checklist-new" v-model="text" class="field h-8 text-sm" type="text" placeholder="Adicionar item" />
      <button type="submit" class="btn h-8">Adicionar</button>
    </form>
  </div>
</template>
