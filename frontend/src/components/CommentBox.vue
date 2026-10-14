<script setup>
import { computed, ref } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useBoardStore } from '../stores/board'

const props = defineProps({ card: { type: Object, required: true } })
const board = useBoardStore()
const auth = useAuthStore()
const text = ref('')
const error = ref('')
const input = ref(null)

// Autocompletar de @menção: mostra usuários enquanto a última palavra começa com "@".
const mentionQuery = computed(() => {
  const match = /(?:^|\s)@([\w.@+-]*)$/.exec(text.value)
  return match ? match[1].toLowerCase() : null
})
const suggestions = computed(() => {
  if (mentionQuery.value === null) return []
  return board.users
    .filter((u) => u.id !== auth.user?.id)
    .filter((u) => u.email.toLowerCase().includes(mentionQuery.value) || u.name.toLowerCase().includes(mentionQuery.value))
    .slice(0, 5)
})

function pick(user) {
  text.value = text.value.replace(/@([\w.@+-]*)$/, `@${user.email} `)
  input.value?.focus()
}

async function submit() {
  if (!text.value.trim()) return
  error.value = ''
  try {
    await board.addComment(props.card, text.value.trim())
    text.value = ''
  } catch (e) {
    error.value = e.message
  }
}

function when(iso) {
  return new Date(iso).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' })
}
</script>

<template>
  <div>
    <ol class="space-y-3">
      <li v-for="comment in board.comments" :key="comment.id" class="text-sm">
        <p class="flex items-baseline gap-2">
          <span class="font-medium">{{ comment.author.name || comment.author.email }}</span>
          <span class="text-[13px] text-muted">{{ when(comment.created) }}</span>
          <button
            v-if="comment.author.id === auth.user?.id || auth.can('boards.delete_comment')"
            type="button"
            class="ml-auto text-[13px] text-muted hover:text-danger"
            @click="board.deleteComment(comment)"
          >
            Excluir
          </button>
        </p>
        <p class="whitespace-pre-wrap">{{ comment.text }}</p>
      </li>
      <li v-if="!board.comments.length" class="text-sm text-muted">Nenhum comentário ainda.</li>
    </ol>

    <form class="relative mt-3" @submit.prevent="submit">
      <label class="sr-only" for="comment-text">Novo comentário</label>
      <textarea
        id="comment-text"
        ref="input"
        v-model="text"
        class="field h-20 resize-none py-2 text-sm"
        placeholder="Escreva um comentário. Use @ para mencionar alguém."
        @keydown.meta.enter.prevent="submit"
        @keydown.ctrl.enter.prevent="submit"
      ></textarea>
      <ul v-if="suggestions.length" class="panel absolute left-0 right-0 z-10 mt-1 p-1 shadow-sm" role="listbox">
        <li v-for="user in suggestions" :key="user.id">
          <button type="button" class="block w-full rounded-[var(--radius-control)] px-2 py-1 text-left text-sm hover:bg-surface-2" @click="pick(user)">
            {{ user.name || user.email }} <span class="text-muted">{{ user.email }}</span>
          </button>
        </li>
      </ul>
      <p v-if="error" class="mt-1 text-[13px] text-danger" role="alert">{{ error }}</p>
      <div class="mt-2 flex items-center gap-3">
        <button type="submit" class="btn h-8">Comentar</button>
        <span class="text-[13px] text-muted">Ctrl+Enter envia</span>
      </div>
    </form>
  </div>
</template>
