<script setup>
// Entrada de um campo personalizado conforme o tipo; '' significa vazio (a API apaga o valor).
const props = defineProps({ field: { type: Object, required: true }, id: { type: String, required: true } })
const model = defineModel({ default: '' })

function setNumber(event) {
  const raw = event.target.value
  model.value = raw === '' ? '' : Number(raw)
}

function setBool(event) {
  const raw = event.target.value
  model.value = raw === '' ? '' : raw === 'true'
}
</script>

<template>
  <select v-if="props.field.kind === 'select'" :id="id" v-model="model" class="field" :required="field.required">
    <option value="">—</option>
    <option v-for="option in field.options" :key="option" :value="option">{{ option }}</option>
  </select>
  <select v-else-if="field.kind === 'bool'" :id="id" class="field" :value="model === '' ? '' : String(model)" :required="field.required" @change="setBool">
    <option value="">—</option>
    <option value="true">Sim</option>
    <option value="false">Não</option>
  </select>
  <input v-else-if="field.kind === 'number'" :id="id" class="field" type="number" step="any" :value="model" :required="field.required" @input="setNumber" />
  <input v-else-if="field.kind === 'date'" :id="id" v-model="model" class="field" type="date" :required="field.required" />
  <input v-else :id="id" v-model="model" class="field" type="text" :required="field.required" />
</template>
