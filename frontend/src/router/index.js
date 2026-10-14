import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import ChangePasswordView from '../views/ChangePasswordView.vue'
import ClientFormView from '../views/ClientFormView.vue'
import ClientsView from '../views/ClientsView.vue'
import ForgotPasswordView from '../views/ForgotPasswordView.vue'
import HomeView from '../views/HomeView.vue'
import LoginView from '../views/LoginView.vue'
import ResetPasswordView from '../views/ResetPasswordView.vue'

const auth = { layout: 'auth', public: true }

const routes = [
  { path: '/', name: 'home', component: HomeView, meta: { title: 'Início' } },
  { path: '/clients', name: 'clients', component: ClientsView, meta: { title: 'Clientes' } },
  { path: '/clients/new', name: 'client-new', component: ClientFormView, meta: { title: 'Novo cliente' } },
  { path: '/clients/:id/edit', name: 'client-edit', component: ClientFormView, meta: { title: 'Editar cliente' } },
  { path: '/settings/password', name: 'change-password', component: ChangePasswordView, meta: { title: 'Trocar senha' } },
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

// Rotas privadas exigem token; quem já está logado não volta para o login.
router.beforeEach((to) => {
  const auth = useAuthStore()
  if (!to.meta.public && !auth.isLoggedIn) return { name: 'login', query: { redirect: to.fullPath } }
  if (to.name === 'login' && auth.isLoggedIn) return { name: 'home' }
})

router.afterEach((to) => {
  document.title = to.meta.title ? `${to.meta.title} · HubFlow` : 'HubFlow'
})

export default router
