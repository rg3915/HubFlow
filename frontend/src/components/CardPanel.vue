<script setup>
import { ref, watch } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useBoardStore } from '../stores/board'
import ActivityList from './ActivityList.vue'
import AttachmentsBox from './AttachmentsBox.vue'
import ChecklistBox from './ChecklistBox.vue'
import CommentBox from './CommentBox.vue'
import FieldInput from './FieldInput.vue'
import LabelPicker from './LabelPicker.vue'
import TimeBox from './TimeBox.vue'

const auth = useAuthStore()
const board = useBoardStore()
const title = ref('')
const description = ref('')
const dueDate = ref('')
const assigneeId = ref('')
const estimate = ref('')
const values = ref({}) // campos personalizados {id: valor}
const error = ref('')
const saved = ref(false)
// No celular as seções começam fechadas (menos comentários) para o formulário caber na tela.
const wide = matchMedia('(min-width: 768px)').matches

const labels = {
  backlog: 'Backlog',
  sprint: 'Sprint',
  doing: 'Em desenvolvimento',
  qa: 'QA',
  done: 'Concluído',
  archived: 'Arquivadas',
}

watch(
  () => [board.selected, board.fields], // os campos podem chegar depois do card aberto pela URL
  ([card]) => {
    title.value = card?.title || ''
    description.value = card?.description || ''
    dueDate.value = card?.due_date || ''
    assigneeId.value = card?.assignee?.id || ''
    estimate.value = card?.estimate_hours ?? ''
    values.value = Object.fromEntries(board.fields.map((f) => [f.id, card?.custom_values?.[f.id] ?? '']))
    error.value = ''
    saved.value = false
  },
  { immediate: true },
)

// Só o que mudou: card antigo não precisa preencher obrigatório criado depois para editar o título.
function changedFields() {
  const current = board.selected.custom_values || {}
  return Object.fromEntries(Object.entries(values.value).filter(([id, value]) => value !== (current[id] ?? '')))
}

function moveTo(column) {
  const card = board.selected
  if (column !== card.column) board.move(card.id, card.column, column, board.column(column).cards.length).catch(() => {})
}

async function save() {
  error.value = ''
  try {
    await board.updateCard(board.selected, {
      title: title.value,
      description: description.value,
      due_date: dueDate.value || null,
      assignee_id: assigneeId.value || null,
      estimate_hours: estimate.value === '' ? null : Number(estimate.value),
      fields: changedFields(),
    })
    saved.value = true
  } catch (e) {
    error.value = e.status === 422 ? 'O título é obrigatório.' : e.message
  }
}

async function remove() {
  if (!confirm(`Excluir o card #${board.selected.number}? Isso não pode ser desfeito.`)) return
  await board.deleteCard(board.selected)
}
</script>

<template>
  <!-- Celular: folha de tela cheia; desktop: painel lateral. -->
  <aside
    v-if="board.selected"
    class="fixed inset-0 z-40 flex flex-col bg-surface pb-[env(safe-area-inset-bottom)] md:static md:z-auto md:w-[26rem] md:shrink-0 md:border-l md:border-border md:pb-0"
    aria-label="Detalhes do card"
  >
    <header class="flex items-center gap-2 border-b border-border px-4 py-2 pt-[max(0.5rem,env(safe-area-inset-top))] md:pt-2">
      <button type="button" class="btn btn-ghost h-8 px-2 md:hidden" @click="board.select(null)">← Quadro</button>
      <span class="text-muted tabular-nums">#{{ board.selected.number }}</span>
      <!-- Mover sem arrastar (útil no celular). -->
      <label class="sr-only" for="card-move">Mover para</label>
      <select
        v-if="auth.canEditCard(board.selected)"
        id="card-move"
        class="field h-8 w-auto py-0 text-sm"
        :value="board.selected.column"
        @change="moveTo($event.target.value)"
      >
        <option v-for="(text, key) in labels" :key="key" :value="key">{{ text }}</option>
      </select>
      <span v-else class="text-muted">· {{ labels[board.selected.column] }}</span>
      <span v-if="board.selected.is_overdue" class="rounded-full bg-danger/10 px-2 text-[0.93rem] text-danger">Atrasado</span>
      <button type="button" class="btn btn-ghost ml-auto hidden h-8 w-8 justify-center px-0 md:inline-flex" aria-label="Fechar" @click="board.select(null)">×</button>
    </header>

    <div class="flex-1 overflow-y-auto">
      <form class="space-y-4 border-b border-border p-4" @submit.prevent="save">
        <fieldset :disabled="!auth.canEditCard(board.selected)" class="space-y-4">
        <div>
          <label class="label" for="card-title">Título</label>
          <input id="card-title" v-model="title" class="field" type="text" required />
        </div>
        <div>
          <label class="label" for="card-description">Descrição</label>
          <textarea id="card-description" v-model="description" class="field h-28 resize-none py-2" placeholder="O que precisa ser feito?"></textarea>
        </div>
        <div class="grid grid-cols-2 gap-3 sm:grid-cols-3">
          <div>
            <label class="label" for="card-assignee">Responsável</label>
            <select id="card-assignee" v-model="assigneeId" class="field">
              <option value="">Ninguém</option>
              <option v-for="user in board.users" :key="user.id" :value="user.id">{{ user.name || user.email }}</option>
            </select>
          </div>
          <div>
            <label class="label" for="card-due">Prazo</label>
            <input id="card-due" v-model="dueDate" class="field" type="date" />
          </div>
          <div>
            <label class="label" for="card-estimate">Estimativa (h)</label>
            <input id="card-estimate" v-model="estimate" class="field" type="number" min="0" step="0.5" placeholder="auto" />
          </div>
        </div>
        <div v-if="board.fields.length" class="grid grid-cols-2 gap-3">
          <div v-for="field in board.fields" :key="field.id">
            <label class="label" :for="`card-field-${field.id}`">{{ field.name }}<span v-if="field.required" class="text-danger"> *</span></label>
            <FieldInput v-model="values[field.id]" :field="field" :id="`card-field-${field.id}`" />
          </div>
        </div>
        <p v-if="board.selected.progress?.estimate_hours" class="-mt-2 text-[0.93rem] text-muted">
          {{ board.selected.progress.spent_hours }}h de {{ board.selected.progress.estimate_hours }}h
          ({{ board.selected.progress.percent }}%<span v-if="board.selected.progress.source === 'median'">, estimativa pela mediana do projeto</span>)
        </p>

        </fieldset>
        <p v-if="!auth.canEditCard(board.selected)" class="text-[0.93rem] text-muted">Só quem criou, o responsável ou quem pode editar qualquer card altera este card.</p>
        <p v-if="error" class="rounded-[var(--radius-control)] border border-danger/40 px-3 py-2 text-danger" role="alert">{{ error }}</p>
        <p v-else-if="saved" class="text-muted" role="status">Salvo.</p>

        <div class="flex flex-wrap gap-2">
          <button v-if="auth.canEditCard(board.selected)" type="submit" class="btn btn-primary">Salvar</button>
          <template v-if="auth.canDeleteCard(board.selected)">
            <button v-if="board.selected.column !== 'archived'" type="button" class="btn" @click="board.archiveCard(board.selected)">Arquivar</button>
            <button type="button" class="btn btn-ghost ml-auto text-danger" @click="remove">Excluir</button>
          </template>
        </div>
      </form>

      <details class="group border-b border-border p-4" :open="wide">
        <summary class="label flex cursor-pointer select-none list-none items-center justify-between">Tempo<span class="text-muted transition-transform group-open:rotate-180" aria-hidden="true">▾</span></summary>
        <TimeBox />
      </details>

      <details class="group border-b border-border p-4" :open="wide">
        <summary class="label flex cursor-pointer select-none list-none items-center justify-between">Etiquetas<span class="text-muted transition-transform group-open:rotate-180" aria-hidden="true">▾</span></summary>
        <fieldset :disabled="!auth.canEditCard(board.selected)"><LabelPicker :card="board.selected" /></fieldset>
      </details>

      <details class="group border-b border-border p-4" :open="wide">
        <summary class="label flex cursor-pointer select-none list-none items-center justify-between">Checklist<span class="text-muted transition-transform group-open:rotate-180" aria-hidden="true">▾</span></summary>
        <ChecklistBox />
      </details>

      <details class="group border-b border-border p-4" :open="wide">
        <summary class="label flex cursor-pointer select-none list-none items-center justify-between">Anexos<span class="text-muted transition-transform group-open:rotate-180" aria-hidden="true">▾</span></summary>
        <AttachmentsBox :can-upload="auth.canEditCard(board.selected)" />
      </details>

      <details class="group border-b border-border p-4" :open="true">
        <summary class="label flex cursor-pointer select-none list-none items-center justify-between">Comentários<span class="text-muted transition-transform group-open:rotate-180" aria-hidden="true">▾</span></summary>
        <CommentBox :card="board.selected" />
      </details>

      <details class="group p-4" :open="wide">
        <summary class="label flex cursor-pointer select-none list-none items-center justify-between">Atividade<span class="text-muted transition-transform group-open:rotate-180" aria-hidden="true">▾</span></summary>
        <ActivityList />
      </details>
    </div>
  </aside>
</template>
