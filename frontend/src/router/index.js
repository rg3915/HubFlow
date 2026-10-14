import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import AutomationsView from '../views/AutomationsView.vue'
import ChangePasswordView from '../views/ChangePasswordView.vue'
import ClientFormView from '../views/ClientFormView.vue'
import ClientsView from '../views/ClientsView.vue'
import ForgotPasswordView from '../views/ForgotPasswordView.vue'
import DashboardView from '../views/DashboardView.vue'
import IntegrationView from '../views/IntegrationView.vue'
import FieldsView from '../views/FieldsView.vue'
import LabelsView from '../views/LabelsView.vue'
import LoginView from '../views/LoginView.vue'
import PaymentsView from '../views/PaymentsView.vue'
import ProfileView from '../views/ProfileView.vue'
import ReportSchedulesView from '../views/ReportSchedulesView.vue'
import ReportsView from '../views/ReportsView.vue'
import PublicFormView from '../views/PublicFormView.vue'
import UsersView from '../views/UsersView.vue'
import ProjectFormView from '../views/ProjectFormView.vue'
import ProjectView from '../views/ProjectView.vue'
import ProjectsView from '../views/ProjectsView.vue'
import ResetPasswordView from '../views/ResetPasswordView.vue'
import SprintsView from '../views/SprintsView.vue'

const auth = { layout: 'auth', public: true }

const routes = [
  { path: '/', name: 'home', component: DashboardView, meta: { title: 'Dashboard' } },
  { path: '/clients', name: 'clients', component: ClientsView, meta: { title: 'Clientes' } },
  { path: '/clients/new', name: 'client-new', component: ClientFormView, meta: { title: 'Novo cliente', perm: 'clients.add_client' } },
  { path: '/clients/:id/edit', name: 'client-edit', component: ClientFormView, meta: { title: 'Editar cliente', perm: 'clients.change_client' } },
  { path: '/projects', name: 'projects', component: ProjectsView, meta: { title: 'Projetos' } },
  { path: '/projects/new', name: 'project-new', component: ProjectFormView, meta: { title: 'Novo projeto', perm: 'projects.add_project' } },
  { path: '/projects/:id', name: 'project', component: ProjectView, meta: { title: 'Quadro' } },
  { path: '/projects/:id/sprints', name: 'project-sprints', component: SprintsView, meta: { title: 'Sprints' } },
  { path: '/projects/:id/integration', name: 'project-integration', component: IntegrationView, meta: { title: 'Integração', perm: 'projects.change_project' } },
  { path: '/projects/:id/fields', name: 'project-fields', component: FieldsView, meta: { title: 'Campos', perm: 'projects.change_project' } },
  { path: '/projects/:id/automations', name: 'project-automations', component: AutomationsView, meta: { title: 'Automações', perm: 'projects.change_project' } },
  { path: '/projects/:id/labels', name: 'project-labels', component: LabelsView, meta: { title: 'Etiquetas' } },
  { path: '/projects/:id/edit', name: 'project-edit', component: ProjectFormView, meta: { title: 'Editar projeto', perm: 'projects.change_project' } },
  { path: '/reports', name: 'reports', component: ReportsView, meta: { title: 'Relatórios' } },
  { path: '/reports/schedules', name: 'report-schedules', component: ReportSchedulesView, meta: { title: 'Relatórios agendados' } },
  { path: '/payments', name: 'payments', component: PaymentsView, meta: { title: 'Pagamentos', payments: true } },
  { path: '/settings/users', name: 'users', component: UsersView, meta: { title: 'Usuários e permissões', perm: 'accounts.change_user' } },
  { path: '/settings/profile', name: 'profile', component: ProfileView, meta: { title: 'Perfil' } },
  { path: '/settings/password', name: 'change-password', component: ChangePasswordView, meta: { title: 'Trocar senha' } },
  { path: '/form/:token', name: 'public-form', component: PublicFormView, meta: { ...auth, title: 'Formulário' } },
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

// Página nova abre no topo; voltar/avançar restaura a rolagem.
const router = createRouter({ history: createWebHistory(), routes, scrollBehavior: (to, from, saved) => saved || { top: 0 } })

// Rotas privadas exigem token; quem já está logado não volta para o login.
router.beforeEach(async (to) => {
  const auth = useAuthStore()
  if (!to.meta.public && !auth.isLoggedIn) return { name: 'login', query: { redirect: to.fullPath } }
  if (to.name === 'login' && auth.isLoggedIn) return { name: 'home' }
  if (to.meta.public) return
  if (!auth.user) {
    try {
      await auth.fetchUser()
    } catch (e) {
      // Token revogado ou expirado: volta para o login.
      if (e.status === 401) {
        await auth.logout()
        return { name: 'login', query: { redirect: to.fullPath } }
      }
    }
  }
  // Sem a permissão, a rota nem abre (a API devolveria 403 de qualquer jeito).
  if ((to.meta.perm && !auth.can(to.meta.perm)) || (to.meta.payments && !auth.seesPayments)) return { name: 'home' }
})

router.afterEach((to) => {
  document.title = to.meta.title ? `${to.meta.title} · HubFlow` : 'HubFlow'
})

export default router
