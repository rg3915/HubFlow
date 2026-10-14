<script setup>
import { useBoardStore } from '../stores/board'

defineProps({ card: { type: Object, required: true } })
const board = useBoardStore()
</script>

<template>
  <article
    class="cursor-grab rounded-[var(--radius-control)] border bg-surface px-3 py-2 shadow-[0_1px_2px_rgb(0_0_0/.06)] active:cursor-grabbing"
    :class="board.selected?.id === card.id ? 'border-accent' : 'border-border'"
    tabindex="0"
    role="button"
    @click="board.select(card)"
    @keydown.enter="board.select(card)"
  >
    <p class="leading-snug">{{ card.title }}</p>
    <p class="mt-1 text-[13px] text-muted tabular-nums">#{{ card.number }}</p>
  </article>
</template>
