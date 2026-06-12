import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'
import { analyzeStock, getAgentStatus } from '../api'

export const useAnalysisStore = defineStore('analysis', () => {
  const currentSymbol = ref('')
  const currentAnalysis = ref(null)
  const agentStatus = ref({})
  const isAnalyzing = ref(false)
  const thinkingSteps = reactive([])

  async function analyze(symbol, options = {}) {
    isAnalyzing.value = true
    currentSymbol.value = symbol
    thinkingSteps.length = 0
    try {
      const { data } = await analyzeStock({
        symbol,
        analysis_type: options.analysisType || 'comprehensive',
        include_news: options.includeNews !== false,
        include_risk: options.includeRisk !== false,
        include_strategy: options.includeStrategy || false,
      })
      currentAnalysis.value = data
      return data
    } catch (error) {
      console.error('分析失败:', error)
      throw error
    } finally {
      isAnalyzing.value = false
    }
  }

  async function fetchAgentStatus() {
    try {
      const { data } = await getAgentStatus()
      agentStatus.value = data
    } catch (error) {
      console.error('获取智能体状态失败:', error)
    }
  }

  function addThinkingStep(step) {
    thinkingSteps.push(step)
  }

  return { currentSymbol, currentAnalysis, agentStatus, isAnalyzing, thinkingSteps, analyze, fetchAgentStatus, addThinkingStep }
})
