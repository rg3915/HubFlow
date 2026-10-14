<script setup>
import { ref } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useBoardStore } from '../stores/board'

const auth = useAuthStore()
const props = defineProps({ card: { type: Object, required: true } })
const board = useBoardStore()
const creating = ref(false)
const name = ref('')
const color = ref('#245e7d')
const error = ref('')

function has(label) {
  return props.card.labels.some((l) => l.id === label.id)
}

async function toggle(label) {
  const ids = props.card.labels.map((l) => l.id)
  const next = has(label) ? ids.filter((id) => id !== label.id) : [...ids, label.id]
  await board.setLabels(props.card, next)
}

async function create() {
  error.value = ''
  try {
    const label = await board.createLabel(name.value.trim(), color.value)
    await toggle(label)
    name.value = ''
    creating.value = false
  } catch (e) {
    error.value = e.message
  }
}
</script>

<template>
  <div>
    <div class="flex flex-wrap gap-1.5">
      <button
        v-for="label in board.labels"
        :key="label.id"
        type="button"
        class="rounded-full border px-2 py-0.5 text-[13px] leading-5"
        :class="has(label) ? 'text-white' : 'border-border text-muted hover:text-text'"
        :style="has(label) ? { background: label.color, borderColor: label.color } : {}"
        :aria-pressed="has(label)"
        @click="toggle(label)"
      >
        {{ label.name }}
      </button>
      <button v-if="auth.can('boards.add_label')" type="button" class="rounded-full border border-dashed border-border px-2 py-0.5 text-[13px] text-muted hover:text-text" @click="creating = !creating">
        + nova
      </button>
    </div>
    <form v-if="creating" class="mt-2 flex items-center gap-2" @submit.prevent="create">
      <input v-model="name" class="field h-8 flex-1 text-sm" type="text" placeholder="Nome da etiqueta" required />
      <input v-model="color" type="color" class="h-8 w-10 cursor-pointer rounded-[var(--radius-control)] border border-border bg-surface p-0.5" aria-label="Cor" />
      <button type="submit" class="btn btn-primary h-8">Criar</button>
    </form>
    <p v-if="error" class="mt-1 text-[13px] text-danger" role="alert">{{ error }}</p>
  </div>
</template>
