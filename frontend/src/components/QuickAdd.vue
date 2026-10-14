<script setup>
import { nextTick, ref } from 'vue'
import { useBoardStore } from '../stores/board'

const board = useBoardStore()
const open = ref(false)
const title = ref('')
const input = ref(null)
const error = ref('')

async function show() {
  open.value = true
  await nextTick()
  input.value?.focus()
}

async function submit() {
  if (!title.value.trim()) return
  error.value = ''
  try {
    await board.createCard(title.value.trim())
    title.value = ''
    input.value?.focus()
  } catch (e) {
    error.value = e.message
  }
}

function cancel() {
  open.value = false
  title.value = ''
}
</script>

<template>
  <form v-if="open" class="px-2 pb-2" @submit.prevent="submit">
    <label class="sr-only" for="quick-add">Título do card</label>
    <textarea
      id="quick-add"
      ref="input"
      v-model="title"
      class="field h-auto resize-none py-2 text-sm"
      rows="2"
      placeholder="Título do card"
      @keydown.enter.exact.prevent="submit"
      @keydown.esc="cancel"
    ></textarea>
    <p v-if="error" class="mt-1 text-[13px] text-danger" role="alert">{{ error }}</p>
    <div class="mt-2 flex gap-2">
      <button type="submit" class="btn btn-primary h-8">Adicionar</button>
      <button type="button" class="btn btn-ghost h-8" @click="cancel">Cancelar</button>
    </div>
  </form>
  <button v-else type="button" class="btn btn-ghost mx-2 mb-2 h-8 justify-start text-muted" @click="show">
    <span>+</span> Novo card
  </button>
</template>
