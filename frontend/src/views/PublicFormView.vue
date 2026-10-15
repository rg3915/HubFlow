<script setup>
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../api'
import FieldInput from '../components/FieldInput.vue'

// Página sem login: quem tem o link abre um card no Backlog do projeto.
const route = useRoute()
const form = ref(null)
const missing = ref(false)
const data = ref({ title: '', description: '', email: '' })
const values = ref({})
const sent = ref(null)
const error = ref('')
const sending = ref(false)

onMounted(async () => {
  try {
    form.value = await api(`/forms/${route.params.token}`)
    document.title = `${form.value.project_name} · HubFlow`
  } catch {
    missing.value = true
  }
})

async function submit() {
  error.value = ''
  sending.value = true
  try {
    sent.value = await api(`/forms/${route.params.token}`, { method: 'POST', body: { ...data.value, fields: values.value } })
  } catch (e) {
    error.value = e.message
  } finally {
    sending.value = false
  }
}

function again() {
  data.value = { title: '', description: '', email: data.value.email }
  values.value = {}
  sent.value = null
}
</script>

<template>
  <section v-if="missing" class="panel p-6 text-center">
    <h1 class="text-xl font-semibold">Formulário indisponível</h1>
    <p class="mt-2 text-muted">O link não existe mais ou o formulário foi desligado. Peça um novo link a quem enviou.</p>
  </section>

  <section v-else-if="sent" class="panel p-6 text-center" role="status">
    <h1 class="text-xl font-semibold">Recebido</h1>
    <p class="mt-2 text-muted">Seu pedido virou o card #{{ sent.number }} em {{ form.project_name }}.</p>
    <button type="button" class="btn mt-4" @click="again">Enviar outro</button>
  </section>

  <form v-else-if="form" class="panel space-y-4 p-6" @submit.prevent="submit">
    <div>
      <p class="text-[0.93rem] text-muted">{{ form.client_name }}</p>
      <h1 class="text-xl font-semibold">{{ form.project_name }}</h1>
    </div>
    <div>
      <label class="label" for="pf-title">Título<span class="text-danger"> *</span></label>
      <input id="pf-title" v-model="data.title" class="field" type="text" maxlength="200" required />
    </div>
    <div>
      <label class="label" for="pf-description">Descrição</label>
      <textarea id="pf-description" v-model="data.description" class="field h-28 resize-none py-2" maxlength="5000" placeholder="O que aconteceu ou o que você precisa?"></textarea>
    </div>
    <div v-for="field in form.fields" :key="field.id">
      <label class="label" :for="`pf-field-${field.id}`">{{ field.name }}<span v-if="field.required" class="text-danger"> *</span></label>
      <FieldInput v-model="values[field.id]" :field="field" :id="`pf-field-${field.id}`" />
    </div>
    <div>
      <label class="label" for="pf-email">Seu e-mail (opcional)</label>
      <input id="pf-email" v-model="data.email" class="field" type="email" placeholder="voce@hubflow.com" />
    </div>
    <p v-if="error" class="text-danger" role="alert">{{ error }}</p>
    <button type="submit" class="btn btn-primary w-full justify-center" :disabled="sending">{{ sending ? 'Enviando…' : 'Enviar' }}</button>
  </form>

  <p v-else class="text-center text-muted">Carregando…</p>
</template>
