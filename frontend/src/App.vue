<script setup>
import { useRoute } from 'vue-router'
import AppShell from './layouts/AppShell.vue'
import AuthLayout from './layouts/AuthLayout.vue'

const route = useRoute()
</script>

<template>
  <component :is="route.meta.layout === 'auth' ? AuthLayout : AppShell">
    <RouterView />
  </component>
</template>
