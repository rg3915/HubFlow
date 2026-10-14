import { ref, watchEffect } from 'vue'

const stored = localStorage.getItem('theme')
const isDark = ref(stored ? stored === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches)

watchEffect(() => {
  document.documentElement.classList.toggle('dark', isDark.value)
  localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
})

export function useTheme() {
  return { isDark, toggle: () => (isDark.value = !isDark.value) }
}
