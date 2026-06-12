<template>
  <aside class="w-80 bg-dark-900 border-l border-dark-700 flex flex-col h-full">
    <div class="p-4 border-b border-dark-700 flex items-center justify-between">
      <h2 class="font-bold text-white">预警通知</h2>
      <button @click="$emit('close')" class="text-dark-400 hover:text-white">✕</button>
    </div>
    <div class="flex-1 overflow-y-auto p-3 space-y-2">
      <div v-for="alert in alerts" :key="alert.alert_id"
        class="p-3 rounded-lg border" :class="severityClass(alert.severity)">
        <div class="flex items-center gap-2 mb-1">
          <span class="text-sm font-medium">{{ alert.title }}</span>
        </div>
        <p class="text-xs text-dark-400">{{ alert.message || '暂无详情' }}</p>
        <div class="text-xs text-dark-500 mt-1">{{ formatTime(alert.timestamp) }}</div>
      </div>
      <div v-if="!alerts.length" class="text-center text-dark-500 py-8">暂无预警</div>
    </div>
  </aside>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getAlerts } from '../api'

defineEmits(['close'])

const alerts = ref([])

onMounted(async () => {
  try {
    const { data } = await getAlerts()
    alerts.value = data
  } catch {}
})

function severityClass(severity) {
  return { low: 'border-info/30 bg-info/5', medium: 'border-warning/30 bg-warning/5', high: 'border-danger/30 bg-danger/5', critical: 'border-danger/50 bg-danger/10' }[severity] || 'border-dark-600 bg-dark-800'
}

function formatTime(ts) {
  if (!ts) return ''
  return new Date(ts).toLocaleString('zh-CN')
}
</script>
