import { createRouter, createWebHistory } from 'vue-router'
import ClientFormView from '../views/ClientFormView.vue'
import ForgotPasswordView from '../views/ForgotPasswordView.vue'
import HomeView from '../views/HomeView.vue'
import LoginView from '../views/LoginView.vue'
import ResetPasswordView from '../views/ResetPasswordView.vue'

const auth = { layout: 'auth' }

const routes = [
  { path: '/', name: 'home', component: HomeView, meta: { title: 'Início' } },
  { path: '/clients/new', name: 'client-new', component: ClientFormView, meta: { title: 'Novo cliente' } },
  { path: '/login', name: 'login', component: LoginView, meta: { ...auth, title: 'Entrar' } },
  {
    path: '/forgot-password',
    name: 'forgot-password',
    component: ForgotPasswordView,
    meta: { ...auth, title: 'Esqueci minha senha' },
  },
  {
    path: '/reset-password/:uid/:token',
    name: 'reset-password',
    component: ResetPasswordView,
    meta: { ...auth, title: 'Nova senha' },
  },
]

const router = createRouter({ history: createWebHistory(), routes })

router.afterEach((to) => {
  document.title = to.meta.title ? `${to.meta.title} · HubFlow` : 'HubFlow'
})

export default router
