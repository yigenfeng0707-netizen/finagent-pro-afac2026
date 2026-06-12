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
  </aside>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { getAgentStatus } from '../api'

const navItems = [
  { path: '/', icon: '📊', label: '工作台' },
  { path: '/analyze', icon: '🔍', label: '股票分析' },
  { path: '/chat', icon: '💬', label: '数字员工' },
  { path: '/agents', icon: '🤖', label: '智能体管理' },
  { path: '/reports', icon: '📄', label: '报告中心' },
  { path: '/alerts', icon: '🔔', label: '预警中心' },
]

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
