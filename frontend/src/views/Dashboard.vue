<template>
  <div class="p-6 space-y-6">
    <!-- 顶部标题栏 -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-white">数字员工工作台</h1>
        <p class="text-dark-400 text-sm mt-1">FinAgent Pro - 金融自主智能体平台</p>
      </div>
      <div class="flex items-center gap-3">
        <span class="text-xs text-dark-500">{{ currentTime }}</span>
        <button @click="toggleAlertPanel" class="btn-secondary text-sm">🔔 预警</button>
      </div>
    </div>

    <!-- 市场概览卡片 -->
    <div class="grid grid-cols-4 gap-4">
      <div v-for="idx in marketIndices" :key="idx.name" class="card-glow">
        <div class="text-xs text-dark-400">{{ idx.name }}</div>
        <div class="text-xl font-bold mt-1" :class="idx.change_percent >= 0 ? 'text-success' : 'text-danger'">
          {{ idx.current_price?.toFixed(2) || '--' }}
        </div>
        <div class="text-sm" :class="idx.change_percent >= 0 ? 'text-success' : 'text-danger'">
          {{ idx.change_percent >= 0 ? '+' : '' }}{{ idx.change_percent?.toFixed(2) || '--' }}%
        </div>
      </div>
    </div>

    <!-- 快速分析 -->
    <div class="card-glow">
      <h2 class="text-lg font-bold text-white mb-3">快速分析</h2>
      <div class="flex gap-3">
        <input v-model="quickSymbol" @keyup.enter="quickAnalyze" placeholder="输入股票代码，如 600519" class="input-dark flex-1" />
        <button @click="quickAnalyze" :disabled="isAnalyzing" class="btn-primary">
          {{ isAnalyzing ? '分析中...' : '开始分析' }}
        </button>
      </div>
      <div v-if="errorMsg" class="mt-3 text-danger text-sm">❌ {{ errorMsg }}</div>
    </div>

    <!-- 双栏：智能体状态 + 最近预警 -->
    <div class="grid grid-cols-2 gap-4">
      <!-- 智能体状态 -->
      <div class="card">
        <h2 class="text-lg font-bold text-white mb-3">智能体状态</h2>
        <div class="space-y-2">
          <div v-for="(status, name) in agentStatus" :key="name" class="flex items-center justify-between py-2 border-b border-dark-700 last:border-0">
            <div class="flex items-center gap-2">
              <span class="w-2 h-2 rounded-full" :class="status.is_running ? 'bg-success animate-pulse' : (status.tools && status.tools.length > 0 ? 'bg-primary-500' : 'bg-dark-500')"></span>
              <span class="text-sm">{{ status.name }}</span>
            </div>
            <div class="text-xs text-dark-400">
              {{ status.is_running ? '运行中' : (status.tools && status.tools.length > 0 ? '已就绪' : '未就绪') }} · 执行{{ status.execution_count }}次
            </div>
          </div>
        </div>
      </div>

      <!-- 最近预警 -->
      <div class="card">
        <h2 class="text-lg font-bold text-white mb-3">最近预警</h2>
        <div class="space-y-2">
          <div v-for="alert in recentAlerts" :key="alert.alert_id" class="flex items-start gap-2 py-2 border-b border-dark-700 last:border-0">
            <span class="text-sm">{{ alert.severity === 'high' || alert.severity === 'critical' ? '🔴' : '🟡' }}</span>
            <div>
              <div class="text-sm">{{ alert.title }}</div>
              <div class="text-xs text-dark-500">{{ formatTime(alert.timestamp) }}</div>
            </div>
          </div>
          <div v-if="!recentAlerts.length" class="text-dark-500 text-sm text-center py-4">暂无预警</div>
        </div>
      </div>
    </div>

    <!-- 最近分析结果 -->
    <div v-if="currentAnalysis" class="card-glow">
      <h2 class="text-lg font-bold text-white mb-3">
        {{ currentAnalysis.symbol }} {{ currentAnalysis.company_name }} 分析结果
      </h2>
      <div class="grid grid-cols-3 gap-4">
        <div>
          <div class="text-xs text-dark-400">当前价</div>
          <div class="text-xl font-bold text-white">¥{{ currentAnalysis.current_price }}</div>
        </div>
        <div>
          <div class="text-xs text-dark-400">建议信号</div>
          <SignalBadge :signal="currentAnalysis.recommendation?.signal" />
        </div>
        <div>
          <div class="text-xs text-dark-400">置信度</div>
          <div class="text-xl font-bold text-primary-400">{{ (currentAnalysis.recommendation?.confidence * 100).toFixed(0) }}%</div>
        </div>
      </div>
      <div v-if="currentAnalysis.recommendation?.reasoning" class="mt-4 text-sm text-dark-300 bg-dark-900 rounded-lg p-3">
        {{ currentAnalysis.recommendation.reasoning }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, inject } from 'vue'
import { useRouter } from 'vue-router'
import { useAnalysisStore } from '../stores/analysis'
import { getMarketOverview, getAlerts } from '../api'
import SignalBadge from '../components/SignalBadge.vue'

const router = useRouter()
const store = useAnalysisStore()
const toggleAlertPanel = inject('toggleAlertPanel')

const currentTime = ref(new Date().toLocaleString('zh-CN'))
const quickSymbol = ref('')
const isAnalyzing = ref(false)
const marketIndices = ref([
  { name: '上证指数', current_price: 3200, change_percent: 0.5 },
  { name: '深证成指', current_price: 10500, change_percent: -0.3 },
  { name: '创业板指', current_price: 2100, change_percent: 0.8 },
  { name: '科创50', current_price: 980, change_percent: -0.1 },
])
const agentStatus = ref({})
const recentAlerts = ref([])
const currentAnalysis = ref(null)
const errorMsg = ref('')

onMounted(async () => {
  // 更新时间
  setInterval(() => { currentTime.value = new Date().toLocaleString('zh-CN') }, 1000)

  // 获取市场数据
  try {
    const { data } = await getMarketOverview()
    if (data.indices?.length) marketIndices.value = data.indices
  } catch (e) {
    console.warn('获取市场数据失败:', e?.message)
  }

  // 获取智能体状态
  try {
    await store.fetchAgentStatus()
    agentStatus.value = store.agentStatus
  } catch (e) {
    console.warn('获取智能体状态失败:', e?.message)
  }

  // 获取预警
  try {
    const { data } = await getAlerts(5)
    recentAlerts.value = data
  } catch (e) {
    console.warn('获取预警失败:', e?.message)
  }
})

async function quickAnalyze() {
  if (!quickSymbol.value || isAnalyzing.value) return
  isAnalyzing.value = true
  errorMsg.value = ''
  try {
    const result = await store.analyze(quickSymbol.value)
    currentAnalysis.value = result
  } catch (e) {
    errorMsg.value = e?.response?.data?.detail || e?.message || '分析失败，请稍后重试'
  }
  isAnalyzing.value = false
}

function formatTime(ts) {
  if (!ts) return ''
  return new Date(ts).toLocaleString('zh-CN')
}
</script>
