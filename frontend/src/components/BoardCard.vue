<script setup>
defineProps({ card: { type: Object, required: true } })
</script>

<template>
  <article class="rounded-[var(--radius-control)] border border-border bg-surface px-3 py-2 shadow-[0_1px_2px_rgb(0_0_0/.06)]">
    <p class="leading-snug">{{ card.title }}</p>
    <p class="mt-1 text-[13px] text-muted tabular-nums">#{{ card.number }}</p>
  </article>
</template>
