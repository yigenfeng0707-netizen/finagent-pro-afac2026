<template>
  <div class="flex h-screen overflow-hidden">
    <!-- 登录/注册页面不显示侧边栏 -->
    <template v-if="!isAuthPage">
      <!-- 侧边栏 -->
      <Sidebar />
    </template>
    <!-- 主内容区 -->
    <main class="flex-1 overflow-y-auto" :class="{ 'overflow-hidden': isAuthPage }">
      <router-view />
    </main>
    <!-- 右侧预警面板 -->
    <AlertPanel v-if="showAlertPanel && !isAuthPage" @close="showAlertPanel = false" />

    <!-- 全局 Toast 提示 -->
    <Teleport to="body">
      <div class="fixed top-4 right-4 z-[9999] flex flex-col gap-2 pointer-events-none">
        <TransitionGroup name="toast">
          <div
            v-for="toast in toasts"
            :key="toast.id"
            class="pointer-events-auto max-w-sm px-4 py-3 rounded-lg shadow-lg border flex items-start gap-2"
            :class="toastClass(toast.type)"
          >
            <span class="text-sm mt-0.5">{{ toastIcon(toast.type) }}</span>
            <div class="flex-1 min-w-0">
              <p v-if="toast.title" class="text-sm font-medium" :class="toastTitleClass(toast.type)">{{ toast.title }}</p>
              <p class="text-sm" :class="toastTextClass(toast.type)">{{ toast.message }}</p>
            </div>
            <button @click="removeToast(toast.id)" class="text-dark-400 hover:text-white text-sm ml-2">&times;</button>
          </div>
        </TransitionGroup>
      </div>
    </Teleport>

    <!-- 全局 Loading 遮罩 -->
    <Teleport to="body">
      <Transition name="fade">
        <div v-if="globalLoading" class="fixed inset-0 z-[9998] bg-dark-950/60 flex items-center justify-center">
          <div class="flex flex-col items-center gap-3">
            <div class="w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full animate-spin"></div>
            <span class="text-sm text-dark-300">{{ globalLoadingText || '加载中...' }}</span>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, provide, onMounted, onUnmounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import Sidebar from './components/Sidebar.vue'
import AlertPanel from './components/AlertPanel.vue'
import { useWebSocket } from './composables/useWebSocket'
import { useEventBus } from './composables/useEventBus'
import { useUserStore } from './stores/user'

const route = useRoute()
const userStore = useUserStore()

const isAuthPage = computed(() => route.path === '/login')

const showAlertPanel = ref(false)
provide('toggleAlertPanel', () => { showAlertPanel.value = !showAlertPanel.value })

// ===== WebSocket 连接 =====
const { connect: connectWs, disconnect: disconnectWs, status: wsStatus } = useWebSocket()
const { on: onEvent, off: offEvent, emit: emitEvent } = useEventBus()

// ===== 全局 Toast =====
const toasts = ref([])
let toastId = 0

function addToast({ type = 'info', title = '', message = '', duration = 4000 }) {
  const id = ++toastId
  toasts.value.push({ id, type, title, message })
  if (duration > 0) {
    setTimeout(() => removeToast(id), duration)
  }
  return id
}

function removeToast(id) {
  const idx = toasts.value.findIndex(t => t.id === id)
  if (idx !== -1) toasts.value.splice(idx, 1)
}

function toastClass(type) {
  return {
    success: 'bg-dark-800 border-success/40',
    error: 'bg-dark-800 border-danger/40',
    warning: 'bg-dark-800 border-warning/40',
    info: 'bg-dark-800 border-info/40',
  }[type] || 'bg-dark-800 border-dark-600'
}

function toastIcon(type) {
  return { success: '✓', error: '✕', warning: '⚠', info: 'ℹ' }[type] || 'ℹ'
}

function toastTitleClass(type) {
  return {
    success: 'text-success',
    error: 'text-danger',
    warning: 'text-warning',
    info: 'text-info',
  }[type] || 'text-dark-200'
}

function toastTextClass(type) {
  return 'text-dark-300'
}

// ===== 全局 Loading =====
const globalLoading = ref(false)
const globalLoadingText = ref('')

function showLoading(text = '') {
  globalLoading.value = true
  globalLoadingText.value = text
}

function hideLoading() {
  globalLoading.value = false
  globalLoadingText.value = ''
}

// Provide 全局方法给子组件使用
provide('toast', addToast)
provide('showLoading', showLoading)
provide('hideLoading', hideLoading)

// ===== WebSocket 事件处理 =====
function onAgentProgress(msg) {
  // 智能体进度更新，通知 analysis store
  emitEvent('agent:progress', msg)
}

function onAnalysisComplete(msg) {
  addToast({ type: 'success', title: '分析完成', message: `${msg.symbol} 分析已完成` })
  emitEvent('analysis:complete', msg)
}

function onAlert(msg) {
  const alert = msg.alert || msg
  const severity = alert.severity || 'medium'
  const type = { critical: 'error', high: 'error', medium: 'warning', low: 'info' }[severity] || 'info'
  addToast({ type, title: '预警通知', message: alert.title || alert.message || '收到新预警', duration: 6000 })
  emitEvent('alert:new', msg)
}

function onThinkingStep(msg) {
  emitEvent('thinking:step', msg)
}

function onWsConnected() {
  addToast({ type: 'success', message: '实时连接已建立', duration: 2000 })
}

function onWsDisconnected() {
  // 仅在非首次连接时提示（避免页面加载时弹出断开提示）
  if (wsStatus.value === 'disconnected' && toastId > 1) {
    addToast({ type: 'warning', message: '实时连接已断开，正在尝试重连...', duration: 3000 })
  }
}

// ===== 生命周期 =====
onMounted(() => {
  // 初始化用户信息
  userStore.init()

  // 注册 WebSocket 事件监听
  onEvent('ws:agent_progress', onAgentProgress)
  onEvent('ws:analysis_complete', onAnalysisComplete)
  onEvent('ws:alert', onAlert)
  onEvent('ws:thinking_step', onThinkingStep)
  onEvent('ws:connected', onWsConnected)
  onEvent('ws:disconnected', onWsDisconnected)

  // 建立 WebSocket 连接
  connectWs()
})

onUnmounted(() => {
  offEvent('ws:agent_progress', onAgentProgress)
  offEvent('ws:analysis_complete', onAnalysisComplete)
  offEvent('ws:alert', onAlert)
  offEvent('ws:thinking_step', onThinkingStep)
  offEvent('ws:connected', onWsConnected)
  offEvent('ws:disconnected', onWsDisconnected)
  disconnectWs()
})
</script>

<style scoped>
/* Toast 动画 */
.toast-enter-active {
  transition: all 0.3s ease-out;
}
.toast-leave-active {
  transition: all 0.2s ease-in;
}
.toast-enter-from {
  opacity: 0;
  transform: translateX(100%);
}
.toast-leave-to {
  opacity: 0;
  transform: translateX(100%);
}

/* Loading 遮罩动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
