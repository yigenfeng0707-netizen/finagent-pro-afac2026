<template>
  <span class="badge" :class="signalClass">
    {{ signalLabel }}
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({ signal: { type: String, default: 'hold' } })

const signalMap = {
  strong_buy: { label: '强烈买入', class: 'bg-success/20 text-success' },
  buy: { label: '买入', class: 'bg-success/15 text-success' },
  hold: { label: '持有', class: 'bg-dark-600 text-dark-300' },
  sell: { label: '卖出', class: 'bg-danger/15 text-danger' },
  strong_sell: { label: '强烈卖出', class: 'bg-danger/20 text-danger' },
}

// 规范化signal值：处理 "SignalType.BUY" 和 "BUY" 等格式
const normalizedSignal = computed(() => {
  const raw = props.signal || 'hold'
  // 去除 "SignalType." 前缀
  let cleaned = raw.replace(/^SignalType\./i, '')
  // 转为小写
  cleaned = cleaned.toLowerCase()
  return cleaned
})

const signalLabel = computed(() => signalMap[normalizedSignal.value]?.label || '持有')
const signalClass = computed(() => signalMap[normalizedSignal.value]?.class || 'bg-dark-600 text-dark-300')
</script>
