<template>
  <div class="flex flex-col h-full p-6">
    <div class="flex items-center justify-between mb-4">
      <h1 class="text-2xl font-bold text-white">数字员工对话</h1>
      <button v-if="messages.length" @click="doExportChat" :disabled="isExporting" class="btn-secondary text-sm">{{ isExporting ? '导出中...' : '📄 导出对话' }}</button>
    </div>
    <!-- 消息列表 -->
    <div class="flex-1 overflow-y-auto space-y-4 mb-4">
      <div v-if="!messages.length" class="text-center text-dark-500 py-12">
        <div class="text-4xl mb-3">🤖</div>
        <p>你好！我是FinAgent Pro数字员工，可以帮你分析股票、查看行情、管理风险。</p>
        <p class="text-sm mt-2">试试说："分析一下贵州茅台"</p>
      </div>
      <div v-for="(msg, i) in messages" :key="i" :class="msg.role === 'user' ? 'flex justify-end' : 'flex justify-start'">
        <div :class="msg.role === 'user' ? 'bg-primary-600 text-white rounded-xl rounded-br-sm' : 'bg-dark-800 text-dark-100 rounded-xl rounded-bl-sm'" class="max-w-2xl px-4 py-3">
          <div v-if="msg.role === 'user'" class="text-sm whitespace-pre-wrap">{{ msg.content }}</div>
          <div v-else class="text-sm markdown-body" v-html="renderMarkdown(msg.content)"></div>
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
import { useRouter } from 'vue-router'
import { useChatStore } from '../stores/chat'
import { useUserStore } from '../stores/user'
import { exportChat } from '../api'
import ThinkingChain from '../components/ThinkingChain.vue'
import { marked } from 'marked'

const chatStore = useChatStore()
const userStore = useUserStore()
const router = useRouter()
const inputText = ref('')
const messages = computed(() => chatStore.messages)
const isLoading = computed(() => chatStore.isLoading)

function renderMarkdown(text) {
  if (!text) return ''
  return marked.parse(text)
}

async function send() {
  if (!inputText.value.trim() || isLoading.value) return
  // 检查免费使用次数
  try {
    await userStore.fetchUsage()
    const usage = userStore.usage
    if (usage && usage.plan === 'free' && usage.used >= usage.limit) {
      alert('免费使用次数已用完，请升级到专业版继续使用')
      router.push('/pricing')
      return
    }
  } catch (e) { /* 不阻断 */ }
  const text = inputText.value
  inputText.value = ''
  try {
    await chatStore.sendMessage(text)
  } catch (e) {
    if (e?.response?.status === 403) {
      router.push('/pricing')
      return
    }
    chatStore.messages.push({ role: 'assistant', content: '抱歉，发送消息时出现错误，请稍后再试。', timestamp: new Date().toISOString() })
  }
}

async function doExportChat() {
  if (!messages.value.length || isExporting.value) return
  isExporting.value = true
  try {
    const exportMessages = messages.value.map(m => ({
      role: m.role,
      content: m.content,
      timestamp: m.timestamp,
    }))
    const { data } = await exportChat({ messages: exportMessages })
    const url = window.URL.createObjectURL(data)
    const a = document.createElement('a')
    a.href = url
    a.download = '对话记录.docx'
    a.click()
    window.URL.revokeObjectURL(url)
  } catch (e) {
    console.error('导出失败:', e)
  }
  isExporting.value = false
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
