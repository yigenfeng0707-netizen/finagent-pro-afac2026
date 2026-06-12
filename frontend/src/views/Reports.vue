<template>
  <div class="p-6 space-y-6">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-white">报告中心</h1>
      <button @click="showGenerate = true" class="btn-primary">生成报告</button>
    </div>
    <div class="grid grid-cols-2 gap-4">
      <div v-for="report in reports" :key="report.report_id" class="card">
        <div class="flex items-center justify-between mb-2">
          <h3 class="font-bold text-white text-sm">{{ report.title }}</h3>
          <span class="badge-info">{{ report.report_type }}</span>
        </div>
        <p class="text-xs text-dark-400 line-clamp-2">{{ report.summary }}</p>
        <div class="text-xs text-dark-500 mt-2">{{ formatTime(report.created_at || report.generated_at) }}</div>
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
import { ref, onMounted } from 'vue'
import { getReports, generateReport } from '../api'

const reports = ref([])
const showGenerate = ref(false)
const genType = ref('morning_daily')
const genSymbol = ref('')
const generating = ref(false)

onMounted(async () => {
  try { const { data } = await getReports(); reports.value = data } catch {}
})

async function generate() {
  generating.value = true
  try { const { data } = await generateReport(genType.value, genSymbol.value || undefined); reports.value.unshift(data); showGenerate.value = false } catch {}
  generating.value = false
}

function formatTime(ts) { return ts ? new Date(ts).toLocaleString('zh-CN') : '' }
</script>
