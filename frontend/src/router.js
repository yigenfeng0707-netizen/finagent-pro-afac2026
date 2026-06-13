import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/login', name: 'Login', component: () => import('./views/Login.vue'), meta: { public: true } },
  { path: '/pricing', name: 'Pricing', component: () => import('./views/Pricing.vue'), meta: { public: false } },
  { path: '/', name: 'Dashboard', component: () => import('./views/Dashboard.vue') },
  { path: '/analyze', name: 'Analyze', component: () => import('./views/Analyze.vue') },
  { path: '/chat', name: 'Chat', component: () => import('./views/Chat.vue') },
  { path: '/agents', name: 'Agents', component: () => import('./views/Agents.vue') },
  { path: '/reports', name: 'Reports', component: () => import('./views/Reports.vue') },
  { path: '/alerts', name: 'Alerts', component: () => import('./views/Alerts.vue') },
  { path: '/admin', name: 'Admin', component: () => import('./views/Admin.vue') },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 路由守卫
router.beforeEach(async (to, from) => {
  const token = localStorage.getItem('finagent_token')

  // 公开页面直接放行
  if (to.meta.public) {
    // 已登录用户访问登录页时跳转到首页
    if (to.path === '/login' && token) {
      return '/'
    }
    return true
  }

  // 未登录跳转登录页
  if (!token) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }

  return true
})

export default router
