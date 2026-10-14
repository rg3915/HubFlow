<script setup>
import BoardCard from './BoardCard.vue'

defineProps({ column: { type: Object, required: true } })

// Ponto de cor no cabeçalho: a cor é a única informação visual da etapa (docs/design.md).
const dots = {
  backlog: 'bg-stone-400',
  sprint: 'bg-slate-500',
  doing: 'bg-[#8a6a1e]',
  qa: 'bg-[#6b5b95]',
  done: 'bg-[#2e6b4f]',
  archived: 'bg-stone-600',
}
</script>

<template>
  <section class="flex w-72 shrink-0 flex-col rounded-[var(--radius-panel)] bg-surface-2" :aria-label="column.label">
    <header class="flex items-center gap-2 px-3 pb-2 pt-3">
      <span class="h-2 w-2 rounded-full" :class="dots[column.key]" aria-hidden="true"></span>
      <h2 class="font-medium">{{ column.label }}</h2>
      <span class="ml-auto text-muted tabular-nums">{{ column.cards.length }}</span>
    </header>
    <div class="flex min-h-16 flex-1 flex-col gap-2 overflow-y-auto px-2 pb-2">
      <BoardCard v-for="card in column.cards" :key="card.id" :card="card" />
      <p v-if="!column.cards.length" class="px-1 py-2 text-[13px] text-muted">Vazio</p>
    </div>
  </section>
</template>
