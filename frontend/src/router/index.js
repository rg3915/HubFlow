import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import ChangePasswordView from '../views/ChangePasswordView.vue'
import ClientFormView from '../views/ClientFormView.vue'
import ClientsView from '../views/ClientsView.vue'
import ForgotPasswordView from '../views/ForgotPasswordView.vue'
import DashboardView from '../views/DashboardView.vue'
import IntegrationView from '../views/IntegrationView.vue'
import LabelsView from '../views/LabelsView.vue'
import LoginView from '../views/LoginView.vue'
import PaymentsView from '../views/PaymentsView.vue'
import ProjectFormView from '../views/ProjectFormView.vue'
import ProjectView from '../views/ProjectView.vue'
import ProjectsView from '../views/ProjectsView.vue'
import ResetPasswordView from '../views/ResetPasswordView.vue'
import SprintsView from '../views/SprintsView.vue'

const auth = { layout: 'auth', public: true }

const routes = [
  { path: '/', name: 'home', component: DashboardView, meta: { title: 'Dashboard' } },
  { path: '/clients', name: 'clients', component: ClientsView, meta: { title: 'Clientes' } },
  { path: '/clients/new', name: 'client-new', component: ClientFormView, meta: { title: 'Novo cliente' } },
  { path: '/clients/:id/edit', name: 'client-edit', component: ClientFormView, meta: { title: 'Editar cliente' } },
  { path: '/projects', name: 'projects', component: ProjectsView, meta: { title: 'Projetos' } },
  { path: '/projects/new', name: 'project-new', component: ProjectFormView, meta: { title: 'Novo projeto' } },
  { path: '/projects/:id', name: 'project', component: ProjectView, meta: { title: 'Quadro' } },
  { path: '/projects/:id/sprints', name: 'project-sprints', component: SprintsView, meta: { title: 'Sprints' } },
  { path: '/projects/:id/integration', name: 'project-integration', component: IntegrationView, meta: { title: 'Integração' } },
  { path: '/projects/:id/labels', name: 'project-labels', component: LabelsView, meta: { title: 'Etiquetas' } },
  { path: '/projects/:id/edit', name: 'project-edit', component: ProjectFormView, meta: { title: 'Editar projeto' } },
  { path: '/payments', name: 'payments', component: PaymentsView, meta: { title: 'Pagamentos' } },
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
