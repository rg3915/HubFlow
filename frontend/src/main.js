import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './style.css'

const app = createApp(App).use(createPinia()).use(router)

// Espera a primeira rota resolver para já montar com o layout certo (app ou auth).
router.isReady().then(() => app.mount('#app'))
