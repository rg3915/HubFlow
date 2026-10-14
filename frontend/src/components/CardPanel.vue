<script setup>
import { ref, watch } from 'vue'
import { useBoardStore } from '../stores/board'

const board = useBoardStore()
const title = ref('')
const description = ref('')
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
    error.value = ''
    saved.value = false
  },
  { immediate: true },
)

async function save() {
  error.value = ''
  try {
    await board.updateCard(board.selected, { title: title.value, description: description.value })
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
  <aside
    v-if="board.selected"
    class="flex w-96 shrink-0 flex-col border-l border-border bg-surface"
    aria-label="Detalhes do card"
  >
    <header class="flex items-center gap-2 border-b border-border px-4 py-2">
      <span class="text-muted tabular-nums">#{{ board.selected.number }}</span>
      <span class="text-muted">· {{ labels[board.selected.column] }}</span>
      <button type="button" class="btn btn-ghost ml-auto h-8 w-8 justify-center px-0" aria-label="Fechar" @click="board.selected = null">
        ×
      </button>
    </header>

    <form class="flex flex-1 flex-col gap-4 overflow-y-auto p-4" @submit.prevent="save">
      <div>
        <label class="label" for="card-title">Título</label>
        <input id="card-title" v-model="title" class="field" type="text" required />
      </div>
      <div class="flex flex-1 flex-col">
        <label class="label" for="card-description">Descrição</label>
        <textarea id="card-description" v-model="description" class="field h-48 resize-none py-2" placeholder="O que precisa ser feito?"></textarea>
      </div>

      <p v-if="error" class="rounded-[var(--radius-control)] border border-danger/40 px-3 py-2 text-danger" role="alert">{{ error }}</p>
      <p v-else-if="saved" class="text-muted" role="status">Salvo.</p>

      <div class="flex flex-wrap gap-2">
        <button type="submit" class="btn btn-primary">Salvar</button>
        <button v-if="board.selected.column !== 'archived'" type="button" class="btn" @click="board.archiveCard(board.selected)">Arquivar</button>
        <button type="button" class="btn btn-ghost ml-auto text-danger" @click="remove">Excluir</button>
      </div>
    </form>
  </aside>
</template>
