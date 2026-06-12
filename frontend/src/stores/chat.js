import { defineStore } from 'pinia'
import { ref } from 'vue'
import { chat } from '../api'

export const useChatStore = defineStore('chat', () => {
  const messages = ref([])
  const isLoading = ref(false)

  async function sendMessage(text) {
    messages.value.push({ role: 'user', content: text, timestamp: new Date().toISOString() })
    isLoading.value = true
    try {
      const { data } = await chat({ message: text })
      messages.value.push({ role: 'assistant', content: data.response, timestamp: new Date().toISOString(), agentSteps: data.agent_steps || [], relatedStocks: data.related_stocks || [] })
    } catch (error) {
      messages.value.push({ role: 'assistant', content: '抱歉，处理您的问题时出现错误，请稍后再试。', timestamp: new Date().toISOString() })
    } finally {
      isLoading.value = false
    }
  }

  function clearMessages() { messages.value = [] }

  return { messages, isLoading, sendMessage, clearMessages }
})
