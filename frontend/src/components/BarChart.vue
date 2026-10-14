<script setup>
// Barras agrupadas (2 séries), um eixo só, SVG puro. Dados: [{ label, received, pending }].
import { computed, ref } from 'vue'

const props = defineProps({
  rows: { type: Array, required: true },
  money: { type: Function, required: true },
})

const hover = ref(null)
const W = 640
const H = 220
const pad = { top: 12, right: 8, bottom: 28, left: 56 }

const max = computed(() => Math.max(1, ...props.rows.flatMap((r) => [Number(r.received), Number(r.pending)])))
const inner = computed(() => ({ w: W - pad.left - pad.right, h: H - pad.top - pad.bottom }))
const groupW = computed(() => inner.value.w / Math.max(1, props.rows.length))
const barW = computed(() => Math.max(4, Math.min(28, groupW.value * 0.35)))

function y(value) {
  return pad.top + inner.value.h - (Number(value) / max.value) * inner.value.h
}
function x(index, series) {
  const center = pad.left + groupW.value * index + groupW.value / 2
  return series === 0 ? center - barW.value - 1 : center + 1
}
const ticks = computed(() => [0, 0.5, 1].map((t) => ({ y: y(max.value * t), value: max.value * t })))
</script>

<template>
  <div class="relative">
    <svg :viewBox="`0 0 ${W} ${H}`" class="w-full" role="img" aria-label="Recebido e pendente por período">
      <g v-for="tick in ticks" :key="tick.y">
        <line :x1="pad.left" :x2="W - pad.right" :y1="tick.y" :y2="tick.y" stroke="var(--border)" stroke-width="1" />
        <text :x="pad.left - 6" :y="tick.y + 4" text-anchor="end" class="fill-[var(--muted)] text-[10px]">{{ money(tick.value, true) }}</text>
      </g>
      <g v-for="(row, i) in rows" :key="row.label" @mouseenter="hover = i" @mouseleave="hover = null">
        <rect :x="pad.left + groupW * i" :y="pad.top" :width="groupW" :height="inner.h" fill="transparent" />
        <rect :x="x(i, 0)" :y="y(row.received)" :width="barW" :height="pad.top + inner.h - y(row.received)" rx="3" fill="var(--chart-1)" />
        <rect :x="x(i, 1)" :y="y(row.pending)" :width="barW" :height="pad.top + inner.h - y(row.pending)" rx="3" fill="var(--chart-2)" />
        <text :x="pad.left + groupW * i + groupW / 2" :y="H - 8" text-anchor="middle" class="fill-[var(--muted)] text-[11px]">{{ row.label }}</text>
      </g>
    </svg>
    <div v-if="hover !== null" class="panel pointer-events-none absolute left-1/2 top-2 -translate-x-1/2 px-3 py-2 text-[13px] shadow-sm">
      <p class="font-medium">{{ rows[hover].label }}</p>
      <p><span class="mr-1 inline-block h-2 w-2 rounded-sm" style="background: var(--chart-1)"></span>Recebido {{ money(rows[hover].received) }}</p>
      <p><span class="mr-1 inline-block h-2 w-2 rounded-sm" style="background: var(--chart-2)"></span>Pendente {{ money(rows[hover].pending) }}</p>
    </div>
    <p class="mt-1 flex gap-4 text-[13px] text-muted">
      <span><span class="mr-1 inline-block h-2 w-2 rounded-sm" style="background: var(--chart-1)"></span>Recebido</span>
      <span><span class="mr-1 inline-block h-2 w-2 rounded-sm" style="background: var(--chart-2)"></span>Pendente</span>
    </p>
  </div>
</template>
