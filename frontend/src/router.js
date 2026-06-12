import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'Dashboard', component: () => import('./views/Dashboard.vue') },
  { path: '/analyze', name: 'Analyze', component: () => import('./views/Analyze.vue') },
  { path: '/chat', name: 'Chat', component: () => import('./views/Chat.vue') },
  { path: '/agents', name: 'Agents', component: () => import('./views/Agents.vue') },
  { path: '/reports', name: 'Reports', component: () => import('./views/Reports.vue') },
  { path: '/alerts', name: 'Alerts', component: () => import('./views/Alerts.vue') },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
