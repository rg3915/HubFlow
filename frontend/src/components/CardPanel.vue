<script setup>
import { ref, watch } from 'vue'
import { useBoardStore } from '../stores/board'
import ActivityList from './ActivityList.vue'
import AttachmentsBox from './AttachmentsBox.vue'
import ChecklistBox from './ChecklistBox.vue'
import CommentBox from './CommentBox.vue'
import LabelPicker from './LabelPicker.vue'
import TimeBox from './TimeBox.vue'

const board = useBoardStore()
const title = ref('')
const description = ref('')
const dueDate = ref('')
const assigneeId = ref('')
const estimate = ref('')
const error = ref('')
const saved = ref(false)

const labels = {
  backlog: 'Backlog',
  sprint: 'Sprint',
  doing: 'Em desenvolvimento',
  qa: 'QA',
  done: 'Concluído',
  archived: 'Arquivadas',
}

watch(
  () => board.selected,
  (card) => {
    title.value = card?.title || ''
    description.value = card?.description || ''
    dueDate.value = card?.due_date || ''
    assigneeId.value = card?.assignee?.id || ''
    estimate.value = card?.estimate_hours ?? ''
    error.value = ''
    saved.value = false
  },
  { immediate: true },
)

async function save() {
  error.value = ''
  try {
    await board.updateCard(board.selected, {
      title: title.value,
      description: description.value,
      due_date: dueDate.value || null,
      assignee_id: assigneeId.value || null,
      estimate_hours: estimate.value === '' ? null : Number(estimate.value),
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
  <aside v-if="board.selected" class="flex w-[26rem] shrink-0 flex-col border-l border-border bg-surface" aria-label="Detalhes do card">
    <header class="flex items-center gap-2 border-b border-border px-4 py-2">
      <span class="text-muted tabular-nums">#{{ board.selected.number }}</span>
      <span class="text-muted">· {{ labels[board.selected.column] }}</span>
      <span v-if="board.selected.is_overdue" class="rounded-full bg-danger/10 px-2 text-[13px] text-danger">Atrasado</span>
      <button type="button" class="btn btn-ghost ml-auto h-8 w-8 justify-center px-0" aria-label="Fechar" @click="board.select(null)">×</button>
    </header>

    <div class="flex-1 overflow-y-auto">
      <form class="space-y-4 border-b border-border p-4" @submit.prevent="save">
        <div>
          <label class="label" for="card-title">Título</label>
          <input id="card-title" v-model="title" class="field" type="text" required />
        </div>
        <div>
          <label class="label" for="card-description">Descrição</label>
          <textarea id="card-description" v-model="description" class="field h-28 resize-none py-2" placeholder="O que precisa ser feito?"></textarea>
        </div>
        <div class="grid grid-cols-3 gap-3">
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
        <p v-if="board.selected.progress?.estimate_hours" class="-mt-2 text-[13px] text-muted">
          {{ board.selected.progress.spent_hours }}h de {{ board.selected.progress.estimate_hours }}h
          ({{ board.selected.progress.percent }}%<span v-if="board.selected.progress.source === 'median'">, estimativa pela mediana do projeto</span>)
        </p>

        <p v-if="error" class="rounded-[var(--radius-control)] border border-danger/40 px-3 py-2 text-danger" role="alert">{{ error }}</p>
        <p v-else-if="saved" class="text-muted" role="status">Salvo.</p>

        <div class="flex flex-wrap gap-2">
          <button type="submit" class="btn btn-primary">Salvar</button>
          <button v-if="board.selected.column !== 'archived'" type="button" class="btn" @click="board.archiveCard(board.selected)">Arquivar</button>
          <button type="button" class="btn btn-ghost ml-auto text-danger" @click="remove">Excluir</button>
        </div>
      </form>

      <section class="border-b border-border p-4">
        <h3 class="label">Tempo</h3>
        <TimeBox />
      </section>

      <section class="border-b border-border p-4">
        <h3 class="label">Etiquetas</h3>
        <LabelPicker :card="board.selected" />
      </section>

      <section class="border-b border-border p-4">
        <h3 class="label">Checklist</h3>
        <ChecklistBox />
      </section>

      <section class="border-b border-border p-4">
        <h3 class="label">Anexos</h3>
        <AttachmentsBox />
      </section>

      <section class="border-b border-border p-4">
        <h3 class="label">Comentários</h3>
        <CommentBox :card="board.selected" />
      </section>

      <section class="p-4">
        <h3 class="label">Atividade</h3>
        <ActivityList />
      </section>
    </div>
  </aside>
</template>
