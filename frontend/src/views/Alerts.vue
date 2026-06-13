<template>
  <div class="p-6 space-y-6">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-white">预警中心</h1>
      <div class="flex items-center gap-3">
        <select v-model="filterType" class="input-dark text-sm py-1.5 px-3">
          <option value="">全部类型</option>
          <option value="price">价格预警</option>
          <option value="risk">风险预警</option>
          <option value="news">新闻预警</option>
          <option value="compliance">合规预警</option>
          <option value="market">市场预警</option>
          <option value="analysis">分析预警</option>
        </select>
        <button @click="refresh" :disabled="loading" class="btn-primary text-sm py-1.5 px-4">
          {{ loading ? '加载中...' : '刷新' }}
        </button>
      </div>
    </div>

    <div v-if="errorMsg" class="card border border-danger/50">
      <p class="text-danger text-sm">{{ errorMsg }}</p>
    </div>

    <!-- 统计卡片 -->
    <div class="grid grid-cols-4 gap-3" v-if="alerts.length">
      <div class="card text-center">
        <div class="text-2xl font-bold text-white">{{ alerts.length }}</div>
        <div class="text-xs text-dark-400">总预警</div>
      </div>
      <div class="card text-center">
        <div class="text-2xl font-bold text-danger">{{ alerts.filter(a => a.severity === 'critical').length }}</div>
        <div class="text-xs text-dark-400">严重</div>
      </div>
      <div class="card text-center">
        <div class="text-2xl font-bold text-warning">{{ alerts.filter(a => a.severity === 'high').length }}</div>
        <div class="text-xs text-dark-400">高</div>
      </div>
      <div class="card text-center">
        <div class="text-2xl font-bold text-info">{{ alerts.filter(a => ['medium', 'low'].includes(a.severity)).length }}</div>
        <div class="text-xs text-dark-400">中/低</div>
      </div>
    </div>

    <!-- 预警列表 -->
    <div class="space-y-3">
      <div v-for="alert in filteredAlerts" :key="alert.alert_id || alert.timestamp" class="card flex items-start gap-3" :class="severityBorder(alert.severity)">
        <span class="text-xl mt-0.5">{{ severityIcon(alert.severity) }}</span>
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2 flex-wrap">
            <span class="font-bold text-white text-sm">{{ alert.title }}</span>
            <span class="badge text-xs" :class="severityBadge(alert.severity)">{{ alert.severity }}</span>
            <span v-if="alert.alert_type" class="badge bg-dark-700 text-dark-300 text-xs">{{ alert.alert_type }}</span>
            <span v-if="alert.symbol" class="badge bg-primary-900 text-primary-300 text-xs cursor-pointer" @click="goAnalyze(alert.symbol)">{{ alert.symbol }}</span>
          </div>
          <p class="text-xs text-dark-400 mt-1">{{ alert.message || '暂无详情' }}</p>
          <div class="text-xs text-dark-500 mt-1">{{ formatTime(alert.timestamp) }}</div>
        </div>
      </div>
      <div v-if="!filteredAlerts.length && !loading" class="text-center text-dark-500 py-12">
        {{ filterType ? '该类型暂无预警信息' : '暂无预警信息' }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getAlerts } from '../api'

const router = useRouter()
const alerts = ref([])
const errorMsg = ref('')
const loading = ref(false)
const filterType = ref('')

const filteredAlerts = computed(() => {
  if (!filterType.value) return alerts.value
  return alerts.value.filter(a => a.alert_type === filterType.value)
})

async function refresh() {
  loading.value = true
  errorMsg.value = ''
  try {
    const { data } = await getAlerts(50)
    alerts.value = Array.isArray(data) ? data : (data.alerts || [])
  } catch (e) {
    errorMsg.value = '获取预警列表失败: ' + (e?.message || '未知错误')
  } finally {
    loading.value = false
  }
}

function goAnalyze(symbol) {
  router.push(`/analyze?symbol=${symbol}`)
}

function severityIcon(s) {
  return { critical: '🔴', high: '🟠', medium: '🟡', low: '🔵' }[s] || '⚪'
}
function severityBorder(s) {
  return { low: 'border-info/30', medium: 'border-warning/30', high: 'border-danger/30', critical: 'border-danger/50' }[s] || ''
}
function severityBadge(s) {
  return { low: 'bg-info/20 text-info', medium: 'bg-warning/20 text-warning', high: 'bg-danger/20 text-danger', critical: 'bg-danger/30 text-danger' }[s] || ''
}
function formatTime(ts) {
  if (!ts) return ''
  try { return new Date(ts).toLocaleString('zh-CN') } catch { return ts }
}

onMounted(refresh)
</script>
