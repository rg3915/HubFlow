import { createRouter, createWebHistory } from 'vue-router'
import AppShell from '../layouts/AppShell.vue'
import AuthLayout from '../layouts/AuthLayout.vue'
import LoginView from '../views/LoginView.vue'
import HomeView from '../views/HomeView.vue'
import ClientFormView from '../views/ClientFormView.vue'

const routes = [
  {
    path: '/',
    component: AuthLayout,
    children: [{ path: 'login', name: 'login', component: LoginView, meta: { title: 'Entrar' } }],
  },
  {
    path: '/',
    component: AppShell,
    children: [
      { path: '', name: 'home', component: HomeView, meta: { title: 'Início' } },
      { path: 'clients/new', name: 'client-new', component: ClientFormView, meta: { title: 'Novo cliente' } },
    ],
  },
]

const router = createRouter({ history: createWebHistory(), routes })

router.afterEach((to) => {
  document.title = to.meta.title ? `${to.meta.title} · HubFlow` : 'HubFlow'
})

export default router
