import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './style.css'

const app = createApp(App).use(createPinia()).use(router)

// v-stack na <table>: cada <td> recebe o título da coluna (data-label); no celular a linha vira cartão (style.css).
function labelCells(table) {
  const titles = [...table.querySelectorAll('thead th')].map((th) => th.textContent.trim())
  table.querySelectorAll('tbody tr').forEach((row) => [...row.cells].forEach((cell, i) => (cell.dataset.label = titles[i] || '')))
}
app.directive('stack', { mounted: labelCells, updated: labelCells })

// Espera a primeira rota resolver para já montar com o layout certo (app ou auth).
router.isReady().then(() => app.mount('#app'))
