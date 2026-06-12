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

const signalLabel = computed(() => signalMap[props.signal]?.label || '持有')
const signalClass = computed(() => signalMap[props.signal]?.class || 'bg-dark-600 text-dark-300')
</script>
