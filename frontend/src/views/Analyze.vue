<template>
  <div class="p-6 space-y-6">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-white">股票分析</h1>
      <span v-if="demoMode" class="badge bg-warning/20 text-warning text-xs">Demo模式 · 仅真实数据</span>
    </div>

    <div class="card-glow">
      <div class="flex flex-wrap gap-3 mb-4">
        <input v-model="symbol" placeholder="股票代码，如 600519" class="input-dark w-40" />
        <select v-model="analysisType" class="input-dark">
          <option value="comprehensive">综合分析</option>
          <option value="quick">快速分析</option>
        </select>
        <label class="flex items-center gap-1 text-sm text-dark-300"><input type="checkbox" v-model="includeNews" /> 新闻</label>
        <label class="flex items-center gap-1 text-sm text-dark-300"><input type="checkbox" v-model="includeRisk" checked /> 风控</label>
        <label class="flex items-center gap-1 text-sm text-dark-300"><input type="checkbox" v-model="includeStrategy" /> 策略</label>
        <button @click="analyze" :disabled="isAnalyzing" class="btn-primary">{{ isAnalyzing ? '分析中...' : '开始分析' }}</button>
      </div>
    </div>

    <!-- Mock 警告 -->
    <div v-if="result?.is_mock" class="card border border-danger/50 bg-danger/5">
      <p class="text-danger text-sm">⚠️ 当前为模拟数据，非实盘行情。Demo模式或生产环境请确保数据源可用。</p>
    </div>

    <!-- 思维链（分析中） -->
    <ThinkingChain v-if="isAnalyzing" :loading="true" :agent-results="{}" />

    <div v-if="errorMsg" class="card border border-danger/50">
      <p class="text-danger text-sm">❌ {{ errorMsg }}</p>
    </div>

    <div v-if="result" class="space-y-4">
      <!-- 数据来源 -->
      <div class="flex items-center gap-3 text-xs">
        <span class="badge" :class="result.is_mock ? 'bg-danger/20 text-danger' : 'bg-success/20 text-success'">
          {{ result.is_mock ? '模拟数据' : '真实数据' }}
        </span>
        <span class="text-dark-400">来源: {{ result.data_source || 'unknown' }}</span>
        <span v-if="result.compliance_passed" class="badge bg-success/20 text-success">✅ 合规审查通过</span>
      </div>

      <div class="grid grid-cols-4 gap-4">
        <div class="card text-center"><div class="text-xs text-dark-400">当前价</div><div class="text-2xl font-bold text-white">¥{{ result.current_price }}</div></div>
        <div class="card text-center"><div class="text-xs text-dark-400">信号</div><SignalBadge :signal="result.recommendation?.signal" /></div>
        <div class="card text-center"><div class="text-xs text-dark-400">置信度</div><div class="text-2xl font-bold text-primary-400">{{ ((result.recommendation?.confidence || 0) * 100).toFixed(0) }}%</div></div>
        <div class="card text-center"><div class="text-xs text-dark-400">处理时间</div><div class="text-2xl font-bold text-dark-300">{{ result.processing_time?.toFixed(1) }}s</div></div>
      </div>

      <!-- 思维链（完成后） -->
      <ThinkingChain :agent-results="result.agent_results" />

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

      <div v-if="result.recommendation?.reasoning" class="card">
        <h3 class="font-bold text-white mb-2">综合推理</h3>
        <div class="text-sm text-dark-300 whitespace-pre-wrap">{{ result.recommendation.reasoning }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAnalysisStore } from '../stores/analysis'
import { useUserStore } from '../stores/user'
import { getAppConfig } from '../api'
import SignalBadge from '../components/SignalBadge.vue'
import ThinkingChain from '../components/ThinkingChain.vue'

const store = useAnalysisStore()
const userStore = useUserStore()
const route = useRoute()
const router = useRouter()
const symbol = ref('')
const analysisType = ref('comprehensive')
const includeNews = ref(true)
const includeRisk = ref(true)
const includeStrategy = ref(false)
const isAnalyzing = ref(false)
const result = ref(null)
const errorMsg = ref('')
const demoMode = ref(false)

onMounted(async () => {
  if (route.query.symbol) symbol.value = route.query.symbol
  try {
    const { data } = await getAppConfig()
    demoMode.value = data.demo_mode
  } catch {}
})

async function analyze() {
  if (!symbol.value) return
  try {
    await userStore.fetchUsage()
    const usage = userStore.usage
    if (usage && usage.plan === 'free' && usage.used >= usage.limit) {
      errorMsg.value = '免费使用次数已用完，请升级到专业版'
      router.push('/pricing')
      return
    }
  } catch {}

  isAnalyzing.value = true
  errorMsg.value = ''
  result.value = null
  try {
    result.value = await store.analyze(symbol.value, {
      analysisType: analysisType.value,
      includeNews: includeNews.value,
      includeRisk: includeRisk.value,
      includeStrategy: includeStrategy.value,
    })
  } catch (e) {
    const detail = e?.response?.data?.detail || e?.message || '分析失败'
    if (e?.response?.status === 403) {
      router.push('/pricing')
      return
    }
    errorMsg.value = detail
  }
  isAnalyzing.value = false
}
</script>
