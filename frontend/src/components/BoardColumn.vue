<script setup>
import Sortable from 'sortablejs'
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { useBoardStore } from '../stores/board'
import BoardCard from './BoardCard.vue'

const props = defineProps({ column: { type: Object, required: true } })
const board = useBoardStore()
const list = ref(null)
let sortable

// Ponto de cor no cabeçalho: a cor é a única informação visual da etapa (docs/design.md).
const dots = {
  backlog: 'bg-stone-400',
  sprint: 'bg-slate-500',
  doing: 'bg-[#8a6a1e]',
  qa: 'bg-[#6b5b95]',
  done: 'bg-[#2e6b4f]',
  archived: 'bg-stone-600',
}

onMounted(() => {
  sortable = Sortable.create(list.value, {
    group: 'cards',
    animation: 150,
    ghostClass: 'opacity-40',
    dragClass: 'shadow-lg',
    delayOnTouchOnly: true,
    delay: 120,
    onEnd(event) {
      const cardId = Number(event.item.dataset.id)
      const from = event.from.dataset.column
      const to = event.to.dataset.column
      if (from === to && event.oldIndex === event.newIndex) return
      // O Sortable já mexeu no DOM; devolvemos o nó e deixamos o Vue renderizar a partir do estado.
      event.from.insertBefore(event.item, event.from.children[event.oldIndex] || null)
      board.move(cardId, from, to, event.newIndex).catch(() => {})
    },
  })
})

onBeforeUnmount(() => sortable?.destroy())
</script>

<template>
  <section class="flex w-72 shrink-0 flex-col rounded-[var(--radius-panel)] bg-surface-2" :aria-label="column.label">
    <header class="flex items-center gap-2 px-3 pb-2 pt-3">
      <span class="h-2 w-2 rounded-full" :class="dots[column.key]" aria-hidden="true"></span>
      <h2 class="font-medium">{{ column.label }}</h2>
      <span class="ml-auto text-muted tabular-nums">{{ column.cards.length }}</span>
    </header>
    <div ref="list" :data-column="column.key" class="flex min-h-16 flex-1 flex-col gap-2 overflow-y-auto px-2 pb-2">
      <BoardCard v-for="card in column.cards" :key="card.id" :card="card" :data-id="card.id" />
    </div>
  </section>
</template>
