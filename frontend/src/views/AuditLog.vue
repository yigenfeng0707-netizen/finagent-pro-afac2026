<template>
  <div class="p-6 space-y-6">
    <h1 class="text-2xl font-bold text-white">合规审计日志</h1>
    <p class="text-dark-400 text-sm">所有投资建议 API 调用均可追溯</p>

    <div v-if="loading" class="text-dark-400 text-center py-8">加载中...</div>
    <div v-else class="space-y-2">
      <div v-for="(log, idx) in logs" :key="idx" class="card flex items-center gap-4 py-3">
        <div class="w-2 h-2 rounded-full bg-success flex-shrink-0"></div>
        <div class="flex-1 min-w-0">
          <div class="text-sm text-white font-mono">{{ log.method }} {{ log.path }}</div>
          <div class="text-xs text-dark-500">{{ log.timestamp }} · IP {{ log.client_ip }}</div>
        </div>
        <span class="badge bg-success/20 text-success text-xs">{{ log.status_code }}</span>
        <span class="text-xs text-dark-400">{{ log.processing_time }}s</span>
      </div>
      <div v-if="!logs.length" class="text-dark-500 text-center py-8">暂无审计记录，请先执行分析操作</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getAuditLog } from '../api'

const logs = ref([])
const loading = ref(true)

onMounted(async () => {
  try {
    const { data } = await getAuditLog(30)
    logs.value = Array.isArray(data) ? data : []
  } catch (e) {
    console.error(e)
  }
  loading.value = false
})
</script>
