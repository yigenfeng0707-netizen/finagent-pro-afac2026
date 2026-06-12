<template>
  <div class="p-6 space-y-6">
    <h1 class="text-2xl font-bold text-white">预警中心</h1>
    <div class="space-y-3">
      <div v-for="alert in alerts" :key="alert.alert_id" class="card flex items-start gap-3" :class="severityBorder(alert.severity)">
        <span class="text-xl">{{ alert.severity === 'critical' ? '🔴' : alert.severity === 'high' ? '🟠' : alert.severity === 'medium' ? '🟡' : '🔵' }}</span>
        <div class="flex-1">
          <div class="flex items-center gap-2">
            <span class="font-bold text-white text-sm">{{ alert.title }}</span>
            <span class="badge" :class="severityBadge(alert.severity)">{{ alert.severity }}</span>
          </div>
          <p class="text-xs text-dark-400 mt-1">{{ alert.message || '暂无详情' }}</p>
          <div class="text-xs text-dark-500 mt-1">{{ formatTime(alert.timestamp) }}</div>
        </div>
      </div>
      <div v-if="!alerts.length" class="text-center text-dark-500 py-12">暂无预警信息</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getAlerts } from '../api'

const alerts = ref([])

onMounted(async () => {
  try { const { data } = await getAlerts(50); alerts.value = data } catch {}
})

function severityBorder(s) { return { low: 'border-info/30', medium: 'border-warning/30', high: 'border-danger/30', critical: 'border-danger/50' }[s] || '' }
function severityBadge(s) { return { low: 'bg-info/20 text-info', medium: 'bg-warning/20 text-warning', high: 'bg-danger/20 text-danger', critical: 'bg-danger/30 text-danger' }[s] || '' }
function formatTime(ts) { return ts ? new Date(ts).toLocaleString('zh-CN') : '' }
</script>
