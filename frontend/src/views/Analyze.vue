<template>
  <div class="p-6 space-y-6">
    <h1 class="text-2xl font-bold text-white">股票分析</h1>
    <div class="card-glow">
      <div class="flex gap-3 mb-4">
        <input v-model="symbol" placeholder="股票代码" class="input-dark w-40" />
        <select v-model="analysisType" class="input-dark">
          <option value="comprehensive">综合分析</option>
          <option value="quick">快速分析</option>
          <option value="technical">技术分析</option>
          <option value="fundamental">基本面分析</option>
        </select>
        <label class="flex items-center gap-1 text-sm text-dark-300"><input type="checkbox" v-model="includeNews" /> 新闻</label>
        <label class="flex items-center gap-1 text-sm text-dark-300"><input type="checkbox" v-model="includeRisk" checked /> 风控</label>
        <label class="flex items-center gap-1 text-sm text-dark-300"><input type="checkbox" v-model="includeStrategy" /> 策略</label>
        <button @click="analyze" :disabled="isAnalyzing" class="btn-primary">{{ isAnalyzing ? '分析中...' : '分析' }}</button>
      </div>
    </div>

    <!-- 错误提示 -->
    <div v-if="errorMsg" class="card border border-danger/50">
      <p class="text-danger text-sm">❌ {{ errorMsg }}</p>
    </div>

    <!-- 分析结果 -->
    <div v-if="result" class="space-y-4">
      <!-- 核心指标 -->
      <div class="grid grid-cols-4 gap-4">
        <div class="card text-center"><div class="text-xs text-dark-400">当前价</div><div class="text-2xl font-bold text-white">¥{{ result.current_price }}</div></div>
        <div class="card text-center"><div class="text-xs text-dark-400">信号</div><SignalBadge :signal="result.recommendation?.signal" /></div>
        <div class="card text-center"><div class="text-xs text-dark-400">置信度</div><div class="text-2xl font-bold text-primary-400">{{ (result.recommendation?.confidence * 100).toFixed(0) }}%</div></div>
        <div class="card text-center"><div class="text-xs text-dark-400">处理时间</div><div class="text-2xl font-bold text-dark-300">{{ result.processing_time?.toFixed(1) }}s</div></div>
      </div>

      <!-- 智能体结果 -->
      <div class="grid grid-cols-2 gap-4">
        <div v-for="(agent, key) in result.agent_results" :key="key" class="card">
          <div class="flex items-center justify-between mb-2">
            <h3 class="font-bold text-white">{{ agent.agent_name }}</h3>
            <SignalBadge :signal="agent.signal" />
          </div>
          <p class="text-sm text-dark-300">{{ agent.analysis }}</p>
          <div v-if="agent.key_findings?.length" class="mt-2">
            <div v-for="f in agent.key_findings" :key="f" class="text-xs text-dark-400">• {{ f }}</div>
          </div>
        </div>
      </div>

      <!-- 推理详情 -->
      <div v-if="result.recommendation?.reasoning" class="card">
        <h3 class="font-bold text-white mb-2">综合推理</h3>
        <div class="text-sm text-dark-300 whitespace-pre-wrap">{{ result.recommendation.reasoning }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAnalysisStore } from '../stores/analysis'
import SignalBadge from '../components/SignalBadge.vue'

const store = useAnalysisStore()
const route = useRoute()
const symbol = ref('')
const analysisType = ref('comprehensive')
const includeNews = ref(true)
const includeRisk = ref(true)
const includeStrategy = ref(false)
const isAnalyzing = ref(false)
const result = ref(null)
const errorMsg = ref('')

onMounted(() => {
  if (route.query.symbol) {
    symbol.value = route.query.symbol
  }
})

async function analyze() {
  if (!symbol.value) return
  isAnalyzing.value = true
  errorMsg.value = ''
  try {
    result.value = await store.analyze(symbol.value, { analysisType: analysisType.value, includeNews: includeNews.value, includeRisk: includeRisk.value, includeStrategy: includeStrategy.value })
  } catch (e) {
    errorMsg.value = e?.response?.data?.detail || e?.message || '分析失败，请稍后重试'
  }
  isAnalyzing.value = false
}
</script>
