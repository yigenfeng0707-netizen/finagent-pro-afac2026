<template>
  <div class="p-6 space-y-6">
    <h1 class="text-2xl font-bold text-white">智能体管理</h1>
    <div class="grid grid-cols-3 gap-4">
      <div v-for="(status, name) in agents" :key="name" class="card-glow">
        <div class="flex items-center gap-3 mb-3">
          <div class="w-10 h-10 rounded-xl flex items-center justify-center text-lg" :class="agentIcon(name).bg">{{ agentIcon(name).icon }}</div>
          <div>
            <h3 class="font-bold text-white">{{ status.name }}</h3>
            <p class="text-xs text-dark-400">{{ status.type }}</p>
          </div>
        </div>
        <div class="grid grid-cols-2 gap-2 text-xs">
          <div class="text-dark-400">执行次数</div><div class="text-dark-200">{{ status.execution_count }}</div>
          <div class="text-dark-400">成功率</div><div class="text-dark-200">{{ (status.success_rate * 100).toFixed(0) }}%</div>
          <div class="text-dark-400">工具数</div><div class="text-dark-200">{{ status.tools?.length || 0 }}</div>
          <div class="text-dark-400">状态</div><div :class="status.is_running ? 'text-success' : 'text-dark-400'">{{ status.is_running ? '运行中' : '空闲' }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getAgentStatus } from '../api'

const agents = ref({})

onMounted(async () => {
  try { const { data } = await getAgentStatus(); agents.value = data } catch {}
})

function agentIcon(name) {
  const icons = { market: { icon: '📈', bg: 'bg-success/20' }, news: { icon: '📰', bg: 'bg-info/20' }, risk: { icon: '🛡️', bg: 'bg-warning/20' }, strategy: { icon: '🎯', bg: 'bg-primary-500/20' }, report: { icon: '📄', bg: 'bg-dark-600' }, execution: { icon: '⚡', bg: 'bg-danger/20' } }
  return icons[name] || { icon: '🤖', bg: 'bg-dark-600' }
}
</script>
