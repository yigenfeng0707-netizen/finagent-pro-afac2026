<template>
  <div class="p-6 space-y-6">
    <div>
      <h1 class="text-2xl font-bold text-white">试点案例</h1>
      <p class="text-dark-400 text-sm mt-1">AFAC2026 初创组 · 落地验证</p>
    </div>

    <div v-if="loading" class="text-dark-400 text-center py-12">加载中...</div>

    <template v-else-if="pilot">
      <!-- 客户概览 -->
      <div class="card-glow">
        <div class="flex items-start justify-between">
          <div>
            <h2 class="text-lg font-bold text-white">{{ pilot.partner_name }}</h2>
            <span class="badge bg-primary-600/20 text-primary-400 text-xs mt-1">{{ pilot.partner_type }}</span>
          </div>
          <span class="badge bg-success/20 text-success">✅ 试点完成</span>
        </div>
        <p class="text-sm text-dark-400 mt-2">试点周期：{{ pilot.period }}</p>
      </div>

      <!-- Before / After -->
      <div class="grid grid-cols-2 gap-4">
        <div class="card border border-danger/30">
          <h3 class="text-sm font-bold text-danger mb-3">使用前</h3>
          <div class="space-y-2 text-sm">
            <div class="flex justify-between"><span class="text-dark-400">晨报撰写</span><span class="text-white">{{ pilot.metrics_before.daily_report_hours }}h/天</span></div>
            <div class="flex justify-between"><span class="text-dark-400">预警响应</span><span class="text-white">{{ pilot.metrics_before.alert_response_minutes }}min</span></div>
            <div class="flex justify-between"><span class="text-dark-400">合规覆盖</span><span class="text-white">{{ pilot.metrics_before.compliance_coverage_percent }}%</span></div>
          </div>
        </div>
        <div class="card border border-success/30">
          <h3 class="text-sm font-bold text-success mb-3">使用后</h3>
          <div class="space-y-2 text-sm">
            <div class="flex justify-between"><span class="text-dark-400">晨报撰写</span><span class="text-success font-bold">{{ pilot.metrics_after.daily_report_hours }}h/天 ↓{{ pilot.improvements.report_time_reduction_percent }}%</span></div>
            <div class="flex justify-between"><span class="text-dark-400">预警响应</span><span class="text-success font-bold">{{ pilot.metrics_after.alert_response_minutes }}min</span></div>
            <div class="flex justify-between"><span class="text-dark-400">合规覆盖</span><span class="text-success font-bold">{{ pilot.metrics_after.compliance_coverage_percent }}%</span></div>
          </div>
        </div>
      </div>

      <!-- 痛点 & 方案 -->
      <div class="grid grid-cols-2 gap-4">
        <div class="card">
          <h3 class="font-bold text-white mb-2">核心痛点</h3>
          <ul class="space-y-1">
            <li v-for="p in pilot.pain_points" :key="p" class="text-sm text-dark-300">• {{ p }}</li>
          </ul>
        </div>
        <div class="card">
          <h3 class="font-bold text-white mb-2">FinAgent Pro 方案</h3>
          <ul class="space-y-1">
            <li v-for="f in pilot.solution.features" :key="f" class="text-sm text-dark-300">✅ {{ f }}</li>
          </ul>
        </div>
      </div>

      <!-- 客户证言 -->
      <div class="card-glow border-l-4 border-primary-500">
        <p class="text-dark-200 italic">"{{ pilot.testimonial }}"</p>
        <p class="text-xs text-dark-500 mt-2">—— {{ pilot.testimonial_role }}</p>
      </div>

      <!-- Benchmark -->
      <div v-if="benchmark?.latency" class="card">
        <h3 class="font-bold text-white mb-3">系统 Benchmark 数据</h3>
        <div class="grid grid-cols-4 gap-4 text-center">
          <div><div class="text-xs text-dark-400">P95时延</div><div class="text-xl font-bold text-primary-400">{{ benchmark.latency.p95_s }}s</div></div>
          <div><div class="text-xs text-dark-400">合规通过率</div><div class="text-xl font-bold text-success">{{ benchmark.compliance_pass_rate_percent }}%</div></div>
          <div><div class="text-xs text-dark-400">真实数据率</div><div class="text-xl font-bold text-white">{{ benchmark.real_data_rate_percent }}%</div></div>
          <div><div class="text-xs text-dark-400">样本量</div><div class="text-xl font-bold text-white">{{ benchmark.sample_size }}</div></div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getPilotCase, getBenchmarkSummary } from '../api'

const pilot = ref(null)
const benchmark = ref(null)
const loading = ref(true)

onMounted(async () => {
  try {
    const [p, b] = await Promise.all([getPilotCase(), getBenchmarkSummary()])
    pilot.value = p.data
    benchmark.value = b.data?.latency ? b.data : null
  } catch (e) {
    console.error(e)
  }
  loading.value = false
})
</script>
