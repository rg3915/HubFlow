<script setup>
// Heatmap estilo GitHub: 26 colunas (semanas) × 7 linhas (dias), um só matiz em 5 passos.
import { computed, ref } from 'vue'

const props = defineProps({ days: { type: Array, required: true }, weeks: { type: Number, required: true } })
const hover = ref(null)
const size = 11
const gap = 2

const cells = computed(() =>
  props.days.map((day, index) => {
    const date = new Date(day.date + 'T00:00')
    const firstOffset = (new Date(props.days[0].date + 'T00:00').getDay() + 6) % 7 // segunda = 0
    const slot = index + firstOffset
    return { ...day, x: Math.floor(slot / 7) * (size + gap), y: (slot % 7) * (size + gap), label: date.toLocaleDateString('pt-BR') }
  }),
)
const width = computed(() => (props.weeks + 1) * (size + gap))
const height = 7 * (size + gap)
const fills = ['var(--surface-2)', 'color-mix(in oklab, var(--accent) 30%, var(--surface-2))', 'color-mix(in oklab, var(--accent) 55%, var(--surface-2))', 'color-mix(in oklab, var(--accent) 80%, var(--surface-2))', 'var(--accent)']
</script>

<template>
  <div class="relative">
    <svg :viewBox="`0 0 ${width} ${height}`" class="w-full" role="img" aria-label="Horas por dia nas últimas 26 semanas">
      <rect
        v-for="cell in cells"
        :key="cell.date"
        :x="cell.x"
        :y="cell.y"
        :width="size"
        :height="size"
        rx="2"
        :fill="fills[cell.level]"
        @mouseenter="hover = cell"
        @mouseleave="hover = null"
      />
    </svg>
    <p class="mt-1 text-[0.93rem] text-muted">
      <template v-if="hover">{{ hover.label }}: {{ hover.hours }}h</template>
      <template v-else>Menos <span v-for="(fill, i) in fills" :key="i" class="mx-0.5 inline-block h-2.5 w-2.5 rounded-sm align-middle" :style="{ background: fill }"></span> mais</template>
    </p>
  </div>
</template>
