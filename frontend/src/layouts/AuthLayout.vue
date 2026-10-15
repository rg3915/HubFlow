<script setup>
import ThemeToggle from '../components/ThemeToggle.vue'
</script>

<template>
  <div class="flex min-h-screen flex-col">
    <div class="flex justify-end p-3">
      <ThemeToggle />
    </div>
    <div class="flex flex-1 items-start justify-center px-4 pb-16 pt-6 sm:pt-16">
      <div class="w-full max-w-[28.6rem]">
        <p class="mb-6 text-center text-base font-semibold">HubFlow</p>
        <slot />
      </div>
    </div>
  </div>
</template>
