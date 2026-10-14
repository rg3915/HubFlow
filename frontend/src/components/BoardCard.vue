<script setup>
import { computed } from 'vue'
import { BASE_URL } from '../api'
import { useAuthStore } from '../stores/auth'
import { useBoardStore } from '../stores/board'

const props = defineProps({ card: { type: Object, required: true } })
const auth = useAuthStore()
const board = useBoardStore()

const due = computed(() => {
  if (!props.card.due_date) return null
  const date = new Date(props.card.due_date + 'T00:00')
  return date.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' })
})

const progress = computed(() => props.card.progress)
const barWidth = computed(() => `${Math.min(100, progress.value?.percent ?? 0)}%`)

// Dono do card: o responsável ou, sem ele, quem criou.
const owner = computed(() => props.card.assignee || props.card.created_by || null)
const ownerAvatar = computed(() => (owner.value?.avatar_url ? BASE_URL + owner.value.avatar_url : null))
</script>

<template>
  <article
    class="cursor-grab rounded-[var(--radius-control)] border bg-surface px-3 py-2 shadow-[0_1px_2px_rgb(0_0_0/.06)] active:cursor-grabbing"
    :class="[board.selected?.id === card.id ? 'border-accent' : 'border-border', auth.canEditCard(card) ? '' : 'locked !cursor-pointer']"
    tabindex="0"
    role="button"
    @click="board.select(card)"
    @keydown.enter="board.select(card)"
  >
    <div v-if="card.labels?.length" class="mb-1.5 flex flex-wrap gap-1">
      <span
        v-for="label in card.labels"
        :key="label.id"
        class="rounded-full px-1.5 text-[11px] font-medium leading-4 text-white"
        :style="{ background: label.color }"
      >
        {{ label.name }}
      </span>
    </div>
    <p class="leading-snug">{{ card.title }}</p>
    <p v-if="card.description" class="mt-0.5 line-clamp-2 text-[13px] text-muted">{{ card.description }}</p>
    <div
      v-if="progress?.percent !== null && progress?.percent !== undefined"
      class="mt-1.5 h-1 w-full overflow-hidden rounded-full bg-surface-2"
      role="progressbar"
      :aria-valuenow="progress.percent"
      aria-valuemin="0"
      aria-valuemax="100"
      :title="`${progress.spent_hours}h de ${progress.estimate_hours}h (${progress.percent}%)`"
    >
      <div class="h-full rounded-full" :class="progress.percent > 100 ? 'bg-danger' : 'bg-accent'" :style="{ width: barWidth }"></div>
    </div>
    <div class="mt-1.5 flex flex-wrap items-center gap-x-2 gap-y-1 text-[13px] text-muted tabular-nums">
      <span>#{{ card.number }}</span>
      <a v-if="card.issue_number" :href="card.issue_url" target="_blank" rel="noopener" class="hover:underline" :title="`Issue #${card.issue_number} no repositório`" @click.stop>⎇ {{ card.issue_number }}</a>
      <span v-if="due" :class="card.is_overdue ? 'rounded px-1 font-medium text-danger' : ''" :title="card.is_overdue ? 'Atrasado' : 'Prazo'">
        {{ card.is_overdue ? '! ' : '' }}{{ due }}
      </span>
      <span v-if="card.checklist?.total" :title="`Checklist: ${card.checklist.done} de ${card.checklist.total}`">
        ☑ {{ card.checklist.done }}/{{ card.checklist.total }}
      </span>
      <span v-if="card.attachments_count" :title="`${card.attachments_count} anexo(s)`">📎 {{ card.attachments_count }}</span>
      <span v-if="card.time?.hours || card.time?.running" :class="card.time.running ? 'text-accent' : ''" :title="card.time.running ? 'Cronômetro rodando' : 'Horas registradas'">
        ⏱ {{ card.time.running ? 'rodando' : `${card.time.hours}h` }}
      </span>
      <img
        v-if="ownerAvatar"
        :src="ownerAvatar"
        alt=""
        class="ml-auto h-[22px] w-[22px] rounded-full object-cover"
        :title="owner.name || owner.email"
      />
      <span
        v-else-if="owner"
        class="ml-auto inline-flex h-[22px] max-w-24 items-center rounded-full bg-surface-2 px-2 text-[11px] font-medium leading-none text-text"
        :title="owner.name || owner.email"
      >
        <span class="truncate">{{ owner.first_name }}</span>
      </span>
    </div>
  </article>
</template>
