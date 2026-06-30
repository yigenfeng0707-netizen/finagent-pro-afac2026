<template>
  <div v-if="steps.length" class="card border border-primary-600/30">
    <h3 class="font-bold text-white mb-3 flex items-center gap-2">
      <span class="animate-pulse">🧠</span> 思维链推理
      <span v-if="loading" class="text-xs text-primary-400 font-normal">智能体协同分析中...</span>
    </h3>
    <div class="space-y-2">
      <div
        v-for="(step, idx) in steps"
        :key="idx"
        class="flex gap-3 p-2 rounded-lg bg-dark-800/50 transition-all duration-500"
        :class="{ 'opacity-100': idx <= visibleCount, 'opacity-30': idx > visibleCount }"
      >
        <div class="flex-shrink-0 w-6 h-6 rounded-full bg-primary-600/30 text-primary-400 text-xs flex items-center justify-center font-bold">
          {{ idx + 1 }}
        </div>
        <div class="flex-1 min-w-0">
          <div class="text-sm font-medium text-white">{{ step.agent }}</div>
          <div class="text-xs text-dark-400 mt-0.5">{{ step.thought }}</div>
          <div v-if="step.observation" class="text-xs text-dark-300 mt-1 font-mono truncate">{{ step.observation }}</div>
        </div>
        <SignalBadge v-if="step.signal" :signal="step.signal" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import SignalBadge from './SignalBadge.vue'

const props = defineProps({
  agentResults: { type: Object, default: () => ({}) },
  loading: { type: Boolean, default: false },
})

const steps = ref([])
const visibleCount = ref(-1)

const agentLabels = {
  market: '市场分析智能体',
  news: '新闻舆情智能体',
  risk: '风控合规智能体',
  strategy: '投资策略智能体',
  report: '报告生成智能体',
  execution: '执行监控智能体',
}

function buildSteps(results) {
  if (!results || !Object.keys(results).length) return []
  return Object.entries(results).map(([key, agent]) => ({
    agent: agent.agent_name || agentLabels[key] || key,
    thought: agent.analysis?.slice(0, 120) || '完成专业领域分析',
    observation: agent.key_findings?.[0] || '',
    signal: agent.signal,
  }))
}

function animateSteps() {
  visibleCount.value = -1
  const total = steps.value.length
  let i = 0
  const timer = setInterval(() => {
    visibleCount.value = i
    i++
    if (i >= total) clearInterval(timer)
  }, 400)
}

watch(() => props.agentResults, (val) => {
  steps.value = buildSteps(val)
  if (steps.value.length) animateSteps()
}, { immediate: true, deep: true })

watch(() => props.loading, (val) => {
  if (val) {
    steps.value = [
      { agent: '市场分析智能体', thought: '获取实时行情，计算 RSI/MACD 技术指标...', observation: '', signal: null },
      { agent: '新闻舆情智能体', thought: '抓取金融新闻，进行情感分析与事件提取...', observation: '', signal: null },
      { agent: '风控合规智能体', thought: '执行集中度检查与监管规则引擎审查...', observation: '', signal: null },
    ]
    visibleCount.value = 0
  }
})
</script>
