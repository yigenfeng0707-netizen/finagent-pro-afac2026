<template>
  <div class="min-h-screen bg-dark-950 py-12 px-4">
    <div class="max-w-5xl mx-auto">
      <!-- 标题 -->
      <div class="text-center mb-12">
        <h1 class="text-3xl font-bold text-white mb-3">选择适合您的方案</h1>
        <p class="text-dark-400">解锁更强大的金融智能分析能力</p>
      </div>

      <!-- 计划卡片 -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
        <!-- 免费版 -->
        <div class="card relative" :class="{ 'ring-2 ring-primary-500': currentPlan === 'free' }">
          <div v-if="currentPlan === 'free'" class="absolute -top-3 left-1/2 -translate-x-1/2">
            <span class="bg-primary-600 text-white text-xs px-3 py-1 rounded-full">当前方案</span>
          </div>
          <h3 class="text-lg font-bold text-white mb-1">免费版</h3>
          <div class="mb-4">
            <span class="text-3xl font-bold text-white">¥0</span>
            <span class="text-dark-400 text-sm">/永久</span>
          </div>
          <ul class="space-y-2 mb-6 text-sm">
            <li class="flex items-center gap-2 text-dark-300">
              <span class="text-success">✓</span> 1次综合分析
            </li>
            <li class="flex items-center gap-2 text-dark-300">
              <span class="text-success">✓</span> 市场概览
            </li>
            <li class="flex items-center gap-2 text-dark-300">
              <span class="text-success">✓</span> 预警通知
            </li>
            <li class="flex items-center gap-2 text-dark-500">
              <span class="text-dark-600">✕</span> 自定义LLM配置
            </li>
            <li class="flex items-center gap-2 text-dark-500">
              <span class="text-dark-600">✕</span> 无限次分析
            </li>
          </ul>
          <button disabled class="w-full btn-secondary py-2 opacity-50 cursor-not-allowed">
            当前方案
          </button>
        </div>

        <!-- 专业版 -->
        <div class="card-glow relative border-primary-500/30" :class="{ 'ring-2 ring-primary-500': currentPlan === 'pro' }">
          <div class="absolute -top-3 left-1/2 -translate-x-1/2">
            <span class="bg-primary-600 text-white text-xs px-3 py-1 rounded-full">推荐</span>
          </div>
          <h3 class="text-lg font-bold text-white mb-1">专业版</h3>
          <div class="mb-4">
            <span class="text-3xl font-bold text-white">¥99</span>
            <span class="text-dark-400 text-sm">/月</span>
          </div>
          <ul class="space-y-2 mb-6 text-sm">
            <li class="flex items-center gap-2 text-dark-300">
              <span class="text-success">✓</span> 无限次综合分析
            </li>
            <li class="flex items-center gap-2 text-dark-300">
              <span class="text-success">✓</span> 市场概览
            </li>
            <li class="flex items-center gap-2 text-dark-300">
              <span class="text-success">✓</span> 预警通知
            </li>
            <li class="flex items-center gap-2 text-dark-300">
              <span class="text-success">✓</span> 自定义LLM配置
            </li>
            <li class="flex items-center gap-2 text-dark-300">
              <span class="text-success">✓</span> 报告导出
            </li>
          </ul>
          <button @click="handleUpgrade('pro')" :disabled="upgrading === 'pro'"
            class="w-full btn-primary py-2 disabled:opacity-50">
            <span v-if="upgrading === 'pro'" class="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-1"></span>
            {{ currentPlan === 'pro' ? '当前方案' : '升级专业版' }}
          </button>
        </div>

        <!-- 企业版 -->
        <div class="card relative" :class="{ 'ring-2 ring-primary-500': currentPlan === 'enterprise' }">
          <h3 class="text-lg font-bold text-white mb-1">企业版</h3>
          <div class="mb-4">
            <span class="text-3xl font-bold text-white">¥299</span>
            <span class="text-dark-400 text-sm">/月</span>
          </div>
          <ul class="space-y-2 mb-6 text-sm">
            <li class="flex items-center gap-2 text-dark-300">
              <span class="text-success">✓</span> 无限次综合分析
            </li>
            <li class="flex items-center gap-2 text-dark-300">
              <span class="text-success">✓</span> 全部专业版功能
            </li>
            <li class="flex items-center gap-2 text-dark-300">
              <span class="text-success">✓</span> 多用户协作
            </li>
            <li class="flex items-center gap-2 text-dark-300">
              <span class="text-success">✓</span> 私有化部署支持
            </li>
            <li class="flex items-center gap-2 text-dark-300">
              <span class="text-success">✓</span> 专属技术支持
            </li>
          </ul>
          <button @click="handleUpgrade('enterprise')" :disabled="upgrading === 'enterprise'"
            class="w-full btn-primary py-2 disabled:opacity-50">
            <span v-if="upgrading === 'enterprise'" class="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-1"></span>
            {{ currentPlan === 'enterprise' ? '当前方案' : '升级企业版' }}
          </button>
        </div>
      </div>

      <!-- 自定义LLM配置 -->
      <div class="card max-w-2xl mx-auto">
        <h2 class="text-lg font-bold text-white mb-1">自定义 LLM 配置</h2>
        <p class="text-dark-400 text-sm mb-6">配置您自己的大语言模型API，使用私有化部署或第三方服务</p>

        <div class="space-y-4">
          <div>
            <label class="block text-sm text-dark-300 mb-1.5">API Provider</label>
            <select v-model="llmForm.provider" class="input-dark w-full">
              <option value="custom">自定义 (OpenAI兼容)</option>
              <option value="glm">智谱AI (GLM)</option>
              <option value="deepseek">DeepSeek</option>
              <option value="dashscope">阿里云百炼 (DashScope)</option>
            </select>
          </div>
          <div>
            <label class="block text-sm text-dark-300 mb-1.5">API Key</label>
            <input v-model="llmForm.api_key" type="password" class="input-dark w-full" placeholder="sk-..." />
          </div>
          <div>
            <label class="block text-sm text-dark-300 mb-1.5">Base URL</label>
            <input v-model="llmForm.base_url" type="text" class="input-dark w-full" placeholder="https://api.openai.com/v1" />
          </div>
          <div>
            <label class="block text-sm text-dark-300 mb-1.5">Model 名称</label>
            <input v-model="llmForm.model" type="text" class="input-dark w-full" placeholder="gpt-4o / deepseek-v4-pro / qwen-plus" />
          </div>

          <div v-if="llmMsg" class="text-sm rounded-lg px-3 py-2"
            :class="llmMsgType === 'success' ? 'text-success bg-success/10 border border-success/30' : 'text-danger bg-danger/10 border border-danger/30'">
            {{ llmMsg }}
          </div>

          <button @click="saveLLMConfig" :disabled="savingLLM" class="btn-primary px-6 py-2 disabled:opacity-50">
            <span v-if="savingLLM" class="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-1"></span>
            保存配置
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { saveLLMConfig as saveLLMConfigAPI } from '../api'

const router = useRouter()
const userStore = useUserStore()

const upgrading = ref('')
const savingLLM = ref(false)
const llmMsg = ref('')
const llmMsgType = ref('success')

const currentPlan = computed(() => userStore.user?.plan || 'free')

const llmForm = reactive({
  provider: 'custom',
  api_key: '',
  base_url: '',
  model: '',
})

onMounted(() => {
  if (!userStore.isLoggedIn) {
    router.push('/login')
    return
  }
  // 加载已有LLM配置
  const config = userStore.user?.llm_config
  if (config) {
    try {
      const parsed = typeof config === 'string' ? JSON.parse(config) : config
      llmForm.provider = parsed.provider || 'custom'
      llmForm.api_key = parsed.api_key || ''
      llmForm.base_url = parsed.base_url || ''
      llmForm.model = parsed.model || ''
    } catch {}
  }
})

async function handleUpgrade(plan) {
  upgrading.value = plan
  try {
    await userStore.upgradePlan(plan)
  } catch (err) {
    alert(err.response?.data?.detail || '升级失败，请重试')
  } finally {
    upgrading.value = ''
  }
}

async function saveLLMConfig() {
  savingLLM.value = true
  llmMsg.value = ''
  try {
    await saveLLMConfigAPI({
      api_key: llmForm.api_key,
      base_url: llmForm.base_url,
      model: llmForm.model,
      provider: llmForm.provider,
    })
    await userStore.fetchUser()
    llmMsg.value = 'LLM配置保存成功'
    llmMsgType.value = 'success'
  } catch (err) {
    llmMsg.value = err.response?.data?.detail || '保存失败，请重试'
    llmMsgType.value = 'error'
  } finally {
    savingLLM.value = false
  }
}
</script>
