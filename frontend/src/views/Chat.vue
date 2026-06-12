<template>
  <div class="flex flex-col h-full p-6">
    <h1 class="text-2xl font-bold text-white mb-4">数字员工对话</h1>
    <!-- 消息列表 -->
    <div class="flex-1 overflow-y-auto space-y-4 mb-4">
      <div v-if="!messages.length" class="text-center text-dark-500 py-12">
        <div class="text-4xl mb-3">🤖</div>
        <p>你好！我是FinAgent Pro数字员工，可以帮你分析股票、查看行情、管理风险。</p>
        <p class="text-sm mt-2">试试说："分析一下贵州茅台"</p>
      </div>
      <div v-for="(msg, i) in messages" :key="i" :class="msg.role === 'user' ? 'flex justify-end' : 'flex justify-start'">
        <div :class="msg.role === 'user' ? 'bg-primary-600 text-white rounded-xl rounded-br-sm' : 'bg-dark-800 text-dark-100 rounded-xl rounded-bl-sm'" class="max-w-2xl px-4 py-3">
          <div class="text-sm whitespace-pre-wrap">{{ msg.content }}</div>
          <div v-if="msg.agentSteps?.length" class="mt-2 pt-2 border-t border-dark-600">
            <ThinkingChain :steps="msg.agentSteps" />
          </div>
        </div>
      </div>
      <div v-if="isLoading" class="flex justify-start">
        <div class="bg-dark-800 rounded-xl px-4 py-3 text-dark-400">
          <span class="thinking-dot"></span><span class="thinking-dot" style="animation-delay:0.15s"></span><span class="thinking-dot" style="animation-delay:0.3s"></span>
        </div>
      </div>
    </div>
    <!-- 输入框 -->
    <div class="flex gap-3">
      <input v-model="inputText" @keyup.enter="send" placeholder="输入消息，如：分析一下600519" class="input-dark flex-1" />
      <button @click="send" :disabled="isLoading" class="btn-primary">发送</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useChatStore } from '../stores/chat'
import ThinkingChain from '../components/ThinkingChain.vue'

const chatStore = useChatStore()
const inputText = ref('')
const messages = computed(() => chatStore.messages)
const isLoading = computed(() => chatStore.isLoading)

async function send() {
  if (!inputText.value.trim() || isLoading.value) return
  const text = inputText.value
  inputText.value = ''
  try {
    await chatStore.sendMessage(text)
  } catch (e) {
    chatStore.messages.push({ role: 'assistant', content: '抱歉，发送消息时出现错误，请稍后再试。', timestamp: new Date().toISOString() })
  }
}
</script>
