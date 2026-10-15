<script setup>
import { ref } from 'vue'
import { mediaUrl } from '../api'
import { useAuthStore } from '../stores/auth'
import { useBoardStore } from '../stores/board'

const board = useBoardStore()
defineProps({ canUpload: { type: Boolean, default: true } })
const auth = useAuthStore()
const error = ref('')
const input = ref(null)

async function upload(event) {
  error.value = ''
  for (const file of event.target.files) {
    try {
      await board.uploadAttachment(file)
    } catch (e) {
      error.value = e.message
    }
  }
  event.target.value = ''
}

function size(bytes) {
  return bytes < 1024 * 1024 ? `${Math.max(1, Math.round(bytes / 1024))} KB` : `${(bytes / 1024 / 1024).toFixed(1)} MB`
}
</script>

<template>
  <div>
    <ul class="space-y-1">
      <li v-for="attachment in board.attachments" :key="attachment.id" class="flex items-center gap-2 text-sm">
        <a :href="mediaUrl(attachment.url)" target="_blank" rel="noopener" class="truncate text-accent hover:underline">{{ attachment.name }}</a>
        <span class="text-[0.93rem] text-muted tabular-nums">{{ size(attachment.size) }}</span>
        <button v-if="canUpload || attachment.uploaded_by.id === auth.user?.id" type="button" class="ml-auto text-[0.93rem] text-muted hover:text-danger" @click="board.deleteAttachment(attachment)">Excluir</button>
      </li>
      <li v-if="!board.attachments.length" class="text-sm text-muted">Nenhum anexo.</li>
    </ul>
    <input ref="input" type="file" class="sr-only" multiple @change="upload" />
    <button v-if="canUpload" type="button" class="btn mt-2 h-8" @click="input.click()">Enviar arquivo</button>
    <p v-if="error" class="mt-1 text-[0.93rem] text-danger" role="alert">{{ error }}</p>
  </div>
</template>
