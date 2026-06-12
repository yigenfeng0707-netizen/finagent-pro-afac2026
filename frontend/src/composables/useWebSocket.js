import { ref, onUnmounted } from 'vue'
import { useEventBus } from './useEventBus'

const { emit } = useEventBus()

const status = ref('disconnected') // disconnected | connecting | connected
let ws = null
let reconnectTimer = null
let reconnectAttempts = 0
const MAX_RECONNECT_ATTEMPTS = 10
const RECONNECT_BASE_DELAY = 2000

function getWsUrl() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  if (import.meta.env.VITE_API_URL) {
    try {
      const url = new URL(import.meta.env.VITE_API_URL)
      return `${url.protocol === 'https:' ? 'wss:' : 'ws:'}//${url.host}/api/ws`
    } catch {
      // fallback
    }
  }
  return `${protocol}//${window.location.host}/api/ws`
}

function connect() {
  if (ws && (ws.readyState === WebSocket.CONNECTING || ws.readyState === WebSocket.OPEN)) {
    return
  }

  const url = getWsUrl()
  status.value = 'connecting'

  try {
    ws = new WebSocket(url)
  } catch (e) {
    console.warn('[WebSocket] 创建连接失败:', e)
    scheduleReconnect()
    return
  }

  ws.onopen = () => {
    status.value = 'connected'
    reconnectAttempts = 0
    emit('ws:connected')
  }

  ws.onmessage = (event) => {
    try {
      const message = JSON.parse(event.data)
      // 根据后端 ws_manager 推送的消息类型分发事件
      switch (message.type) {
        case 'agent_progress':
          emit('ws:agent_progress', message)
          break
        case 'analysis_complete':
          emit('ws:analysis_complete', message)
          break
        case 'alert':
          emit('ws:alert', message)
          break
        case 'thinking_step':
          emit('ws:thinking_step', message)
          break
        case 'pong':
          // 心跳响应，无需分发
          break
        default:
          emit('ws:message', message)
      }
    } catch {
      // 忽略非JSON消息
    }
  }

  ws.onclose = () => {
    status.value = 'disconnected'
    emit('ws:disconnected')
    scheduleReconnect()
  }

  ws.onerror = (error) => {
    console.warn('[WebSocket] 连接错误:', error)
    // onclose 会在 onerror 之后触发，重连逻辑在 onclose 中处理
  }
}

function scheduleReconnect() {
  if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
    console.warn('[WebSocket] 已达最大重连次数，停止重连')
    return
  }
  clearTimeout(reconnectTimer)
  const delay = RECONNECT_BASE_DELAY * Math.pow(1.5, reconnectAttempts)
  reconnectAttempts++
  reconnectTimer = setTimeout(() => {
    connect()
  }, Math.min(delay, 30000))
}

function disconnect() {
  clearTimeout(reconnectTimer)
  reconnectAttempts = MAX_RECONNECT_ATTEMPTS // 阻止重连
  if (ws) {
    ws.onclose = null // 防止触发重连
    ws.close()
    ws = null
  }
  status.value = 'disconnected'
}

function send(data) {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(typeof data === 'string' ? data : JSON.stringify(data))
  }
}

// 心跳保活
let heartbeatTimer = null
function startHeartbeat() {
  clearInterval(heartbeatTimer)
  heartbeatTimer = setInterval(() => {
    send({ type: 'ping' })
  }, 30000)
}

// 监听连接成功后启动心跳
const { on } = useEventBus()
on('ws:connected', () => startHeartbeat())

export function useWebSocket() {
  onUnmounted(() => {
    // 组件卸载时不自动断开，WebSocket 是全局共享的
    // 断开逻辑由 App.vue 控制
  })

  return {
    status,
    connect,
    disconnect,
    send,
  }
}
