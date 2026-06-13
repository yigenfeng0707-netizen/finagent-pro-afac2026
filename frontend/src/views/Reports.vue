<template>
  <div class="p-6 space-y-6">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-white">报告中心</h1>
      <button @click="showGenerate = true" class="btn-primary">生成报告</button>
    </div>
    <div v-if="errorMsg" class="card border border-danger/50">
      <p class="text-danger text-sm">❌ {{ errorMsg }}</p>
    </div>
    <div class="grid grid-cols-2 gap-4">
      <div v-for="report in reports" :key="report.report_id" class="card">
        <div class="flex items-center justify-between mb-2">
          <h3 class="font-bold text-white text-sm">{{ report.title }}</h3>
          <span class="badge-info">{{ report.report_type }}</span>
        </div>
        <p class="text-xs text-dark-400 line-clamp-2">{{ report.summary }}</p>
        <div class="flex items-center justify-between mt-2">
          <div class="text-xs text-dark-500">{{ formatTime(report.created_at || report.generated_at) }}</div>
          <button @click="toggleReport(report.report_id)" class="text-xs text-primary-400 hover:text-primary-300">
            {{ expandedReports[report.report_id] ? '收起 ▲' : '查看详情 ▼' }}
          </button>
          <button @click="doExportReport(report)" class="text-xs text-primary-400 hover:text-primary-300 ml-2">📄 导出Word</button>
        </div>
        <div v-if="expandedReports[report.report_id] && report.content" class="mt-3 pt-3 border-t border-dark-600">
          <div class="markdown-body text-sm text-dark-200" v-html="renderMarkdown(report.content)"></div>
        </div>
      </div>
    </div>
    <!-- 生成对话框 -->
    <div v-if="showGenerate" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-dark-800 rounded-xl p-6 w-96 space-y-4">
        <h2 class="text-lg font-bold text-white">生成报告</h2>
        <select v-model="genType" class="input-dark w-full">
          <option value="morning_daily">晨报</option>
          <option value="stock_research">个股研报</option>
          <option value="risk_weekly">风控周报</option>
          <option value="portfolio_monthly">组合月报</option>
          <option value="event_flash">事件快报</option>
        </select>
        <input v-model="genSymbol" placeholder="股票代码（可选）" class="input-dark w-full" />
        <div class="flex gap-3">
          <button @click="generate" :disabled="generating" class="btn-primary flex-1">{{ generating ? '生成中...' : '生成' }}</button>
          <button @click="showGenerate = false" class="btn-secondary">取消</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { getReports, generateReport } from '../api'
import { marked } from 'marked'

const reports = ref([])
const expandedReports = reactive({})
const showGenerate = ref(false)
const genType = ref('morning_daily')
const genSymbol = ref('')
const generating = ref(false)
const errorMsg = ref('')

onMounted(async () => {
  try {
    const { data } = await getReports()
    reports.value = data
  } catch (e) {
    errorMsg.value = '获取报告列表失败: ' + (e?.message || '未知错误')
  }
})

async function generate() {
  generating.value = true
  errorMsg.value = ''
  try {
    const { data } = await generateReport(genType.value, genSymbol.value || undefined)
    reports.value.unshift(data)
    showGenerate.value = false
  } catch (e) {
    errorMsg.value = '生成报告失败: ' + (e?.message || '未知错误')
  }
  generating.value = false
}

function toggleReport(id) {
  expandedReports[id] = !expandedReports[id]
}

function renderMarkdown(text) {
  if (!text) return ''
  return marked.parse(text)
}

function formatTime(ts) { return ts ? new Date(ts).toLocaleString('zh-CN') : '' }

async function doExportReport(report) {
  try {
    const exportData = {
      report_id: report.report_id,
      title: report.title,
      report_type: report.report_type,
      content: report.content,
      summary: report.summary,
      symbols: report.symbols,
      generated_at: report.generated_at || report.created_at,
      key_findings: report.key_findings,
      risk_factors: report.risk_factors,
    }
    const { data } = await exportReport(exportData)
    const url = window.URL.createObjectURL(data)
    const a = document.createElement('a')
    a.href = url
    a.download = `${report.title || '报告'}.docx`
    a.click()
    window.URL.revokeObjectURL(url)
  } catch (e) {
    console.error('导出失败:', e)
  }
}
</script>

<style scoped>
.markdown-body :deep(h1) { font-size: 1.25rem; font-weight: 700; margin: 0.5rem 0; }
.markdown-body :deep(h2) { font-size: 1.125rem; font-weight: 700; margin: 0.5rem 0; }
.markdown-body :deep(h3) { font-size: 1rem; font-weight: 600; margin: 0.4rem 0; }
.markdown-body :deep(p) { margin: 0.3rem 0; }
.markdown-body :deep(ul), .markdown-body :deep(ol) { padding-left: 1.25rem; margin: 0.3rem 0; }
.markdown-body :deep(li) { margin: 0.15rem 0; }
.markdown-body :deep(strong) { font-weight: 600; }
.markdown-body :deep(code) { background: rgba(255,255,255,0.1); padding: 0.1rem 0.3rem; border-radius: 0.25rem; font-size: 0.85em; }
.markdown-body :deep(pre) { background: rgba(0,0,0,0.3); padding: 0.5rem; border-radius: 0.375rem; overflow-x: auto; margin: 0.4rem 0; }
.markdown-body :deep(pre code) { background: none; padding: 0; }
.markdown-body :deep(blockquote) { border-left: 3px solid rgba(255,255,255,0.3); padding-left: 0.75rem; margin: 0.4rem 0; color: rgba(255,255,255,0.7); }
.markdown-body :deep(table) { border-collapse: collapse; margin: 0.4rem 0; width: 100%; }
.markdown-body :deep(th), .markdown-body :deep(td) { border: 1px solid rgba(255,255,255,0.2); padding: 0.25rem 0.5rem; }
.markdown-body :deep(th) { background: rgba(255,255,255,0.1); }
</style>
