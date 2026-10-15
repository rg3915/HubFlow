<script setup>
import { fieldText, useBoardStore } from '../stores/board'

const board = useBoardStore()

const columns = { backlog: 'Backlog', sprint: 'Sprint', doing: 'Em desenvolvimento', qa: 'QA', done: 'Concluído', archived: 'Arquivadas' }

function describe(item) {
  const d = item.data
  switch (item.kind) {
    case 'created': return 'criou o card'
    case 'moved': return `moveu de ${columns[d.from_column]} para ${columns[d.to_column]}`
    case 'comment': return `comentou: “${d.text.length > 80 ? d.text.slice(0, 80) + '…' : d.text}”`
    case 'attachment': return `anexou ${d.name}`
    case 'assignee': return d.assignee ? `definiu ${d.assignee} como responsável` : 'tirou o responsável'
    case 'due_date': return d.due_date ? `definiu o prazo para ${new Date(d.due_date + 'T00:00').toLocaleDateString('pt-BR')}` : 'tirou o prazo'
    case 'fields': return Object.entries(d.changes).map(([name, [before, after]]) => `${name}: ${fieldText(before)} → ${fieldText(after)}`).join('; ')
    case 'automation': return `automação “${d.name}”: ${d.description.split('→')[1]?.trim() || d.description}`
    case 'sla_breached': return `SLA de ${columns[d.column]} estourado (${d.hours}h)`
    case 'labels': return d.labels.length ? `etiquetas: ${d.labels.join(', ')}` : 'tirou as etiquetas'
    default: return item.kind
  }
}

function when(iso) {
  return new Date(iso).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' })
}
</script>

<template>
  <ol class="space-y-2 text-sm">
    <li v-for="(item, index) in board.activity" :key="index" class="flex gap-2">
      <span class="w-28 shrink-0 text-[0.93rem] text-muted tabular-nums">{{ when(item.created) }}</span>
      <span><span class="font-medium">{{ item.user?.name || item.user?.email || 'Sistema' }}</span> {{ describe(item) }}</span>
    </li>
    <li v-if="!board.activity.length" class="text-muted">Sem atividade registrada.</li>
  </ol>
</template>
