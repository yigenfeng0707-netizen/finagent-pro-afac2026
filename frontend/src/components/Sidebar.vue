<template>
  <aside class="w-64 bg-dark-900 border-r border-dark-700 flex flex-col h-full">
    <!-- Logo -->
    <div class="p-4 border-b border-dark-700">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 bg-primary-600 rounded-xl flex items-center justify-center text-white font-bold text-lg">F</div>
        <div>
          <h1 class="text-lg font-bold text-white">FinAgent Pro</h1>
          <p class="text-xs text-dark-400">金融自主智能体平台</p>
        </div>
      </div>
    </div>

    <!-- 导航 -->
    <nav class="flex-1 p-3 space-y-1">
      <router-link v-for="item in navItems" :key="item.path" :to="item.path"
        class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-dark-300 hover:bg-dark-800 hover:text-white transition-colors"
        active-class="bg-dark-800 text-white">
        <span class="text-xl">{{ item.icon }}</span>
        <span class="text-sm font-medium">{{ item.label }}</span>
      </router-link>
    </nav>

    <!-- 智能体状态 -->
    <div class="p-3 border-t border-dark-700">
      <div class="text-xs text-dark-500 mb-2">智能体状态</div>
      <div class="space-y-1.5">
        <div v-for="agent in agents" :key="agent.name" class="flex items-center gap-2 text-xs">
          <span class="w-2 h-2 rounded-full" :class="agent.running ? 'bg-success animate-pulse' : 'bg-dark-500'"></span>
          <span class="text-dark-400">{{ agent.name }}</span>
        </div>
      </div>
    </div>

    <!-- 用户信息 -->
    <div class="p-3 border-t border-dark-700">
      <div v-if="userStore.isLoggedIn && userStore.user" class="space-y-2">
        <div class="flex items-center gap-2">
          <div class="w-8 h-8 bg-primary-600/30 rounded-full flex items-center justify-center text-primary-400 text-sm font-bold">
            {{ userStore.user.username?.charAt(0)?.toUpperCase() || 'U' }}
          </div>
          <div class="flex-1 min-w-0">
            <div class="text-sm text-white font-medium truncate">{{ userStore.user.username }}</div>
            <div class="flex items-center gap-1.5">
              <span class="badge text-[10px]" :class="planBadgeClass">{{ planLabel }}</span>
              <span v-if="userStore.isFreeUser" class="text-[10px] text-dark-500">{{ userStore.usage.remaining }}次剩余</span>
            </div>
          </div>
        </div>
        <div class="flex gap-2">
          <router-link to="/pricing" class="flex-1 text-center text-xs text-primary-400 hover:text-primary-300 bg-primary-600/10 hover:bg-primary-600/20 rounded-md py-1.5 transition-colors">
            {{ userStore.isFreeUser ? '升级套餐' : '管理套餐' }}
          </router-link>
          <button @click="handleLogout" class="flex-1 text-center text-xs text-dark-400 hover:text-white bg-dark-800 hover:bg-dark-700 rounded-md py-1.5 transition-colors">
            退出登录
          </button>
        </div>
      </div>
      <div v-else>
        <router-link to="/login" class="block text-center text-sm text-primary-400 hover:text-primary-300 py-2">
          登录 / 注册
        </router-link>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { getAgentStatus } from '../api'
import { useUserStore } from '../stores/user'

const router = useRouter()
const userStore = useUserStore()

const navItems = computed(() => {
  const items = [
    { path: '/', icon: '📊', label: '工作台' },
    { path: '/analyze', icon: '🔍', label: '股票分析' },
    { path: '/chat', icon: '💬', label: '数字员工' },
    { path: '/agents', icon: '🤖', label: '智能体管理' },
    { path: '/reports', icon: '📄', label: '报告中心' },
    { path: '/alerts', icon: '🔔', label: '预警中心' },
    { path: '/cases', icon: '🏆', label: '试点案例' },
    { path: '/audit', icon: '📋', label: '审计日志' },
  ]
  // 管理员显示管理后台入口
  if (userStore.user?.role === 'admin' || userStore.user?.role === 'superadmin') {
    items.push({ path: '/admin', icon: '⚙️', label: '管理后台' })
  }
  return items
})

const agentNameMap = {
  market: '市场分析',
  news: '新闻舆情',
  risk: '风控合规',
  strategy: '投资策略',
  report: '报告生成',
  execution: '执行监控',
}

const agents = ref([
  { name: '市场分析', running: false },
  { name: '新闻舆情', running: false },
  { name: '风控合规', running: false },
  { name: '投资策略', running: false },
  { name: '报告生成', running: false },
  { name: '执行监控', running: false },
])

const planLabel = computed(() => {
  const planMap = { free: '免费版', pro: '专业版', enterprise: '企业版' }
  return planMap[userStore.user?.plan] || '免费版'
})

const planBadgeClass = computed(() => {
  const classMap = {
    free: 'bg-dark-600 text-dark-300',
    pro: 'bg-primary-600/20 text-primary-400',
    enterprise: 'bg-warning/20 text-warning',
  }
  return classMap[userStore.user?.plan] || 'bg-dark-600 text-dark-300'
})

function handleLogout() {
  userStore.logout()
  router.push('/login')
}

let statusTimer = null

async function fetchStatus() {
  try {
    const { data } = await getAgentStatus()
    if (data && typeof data === 'object') {
      agents.value = Object.entries(data).map(([key, status]) => ({
        name: status.name || agentNameMap[key] || key,
        running: status.execution_count > 0,
      }))
    }
  } catch {}
}

onMounted(() => {
  fetchStatus()
  statusTimer = setInterval(fetchStatus, 30000)
})

onUnmounted(() => {
  if (statusTimer) clearInterval(statusTimer)
})
</script>
