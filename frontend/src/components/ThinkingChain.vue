<template>
  <div class="space-y-3">
    <div v-for="(step, i) in steps" :key="i" class="relative pl-6">
      <!-- 连接线 -->
      <div v-if="i < steps.length - 1" class="absolute left-2.5 top-6 bottom-0 w-px bg-dark-600"></div>
      <!-- 步骤点 -->
      <div class="absolute left-1 top-1.5 w-3 h-3 rounded-full" :class="stepColor(step)"></div>
      <!-- 内容 -->
      <div class="text-sm">
        <div class="text-dark-300 mb-1">
          <span class="text-dark-500 text-xs">Step {{ i + 1 }}</span>
          <span class="ml-2 font-medium">{{ step.action || '思考' }}</span>
        </div>
        <div v-if="step.thought" class="text-dark-400 text-xs mb-1 italic">💭 {{ step.thought }}</div>
        <div v-if="step.observation" class="text-dark-500 text-xs bg-dark-800 rounded p-2 mt-1">
          👁️ {{ truncate(step.observation, 200) }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({ steps: { type: Array, default: () => [] } })

function stepColor(step) {
  if (step.action === 'finish') return 'bg-success'
  if (step.observation) return 'bg-primary-400'
  return 'bg-dark-500'
}

function truncate(str, len) {
  if (!str) return ''
  return str.length > len ? str.slice(0, len) + '...' : str
}
</script>
