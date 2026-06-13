import axios from 'axios'
import router from './router'

// 生产环境使用Render后端地址，开发环境走Vite代理
const baseURL = import.meta.env.VITE_API_URL
  ? import.meta.env.VITE_API_URL + '/api'
  : '/api'

const api = axios.create({
  baseURL,
  timeout: 60000,
  headers: { 'Content-Type': 'application/json' },
})

// 请求拦截器 - 自动添加Authorization header
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('finagent_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 统一响应拦截器
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      const { status, data } = error.response
      switch (status) {
        case 401:
          error.message = '登录已过期，请重新登录'
          // 401自动跳转登录页
          localStorage.removeItem('finagent_token')
          if (router.currentRoute.value.path !== '/login') {
            router.push({ path: '/login', query: { redirect: router.currentRoute.value.fullPath } })
          }
          break
        case 403:
          error.message = '没有权限执行此操作'
          break
        case 404:
          error.message = '请求的资源不存在'
          break
        case 422:
          error.message = data?.detail || '请求参数错误'
          break
        case 500:
          error.message = '服务器内部错误，请稍后重试'
          break
        case 502:
        case 503:
          error.message = '服务暂时不可用，请稍后重试'
          break
        default:
          error.message = data?.detail || `请求失败(${status})`
      }
    } else if (error.code === 'ECONNABORTED') {
      error.message = '请求超时，请检查网络后重试'
    } else if (!window.navigator.onLine) {
      error.message = '网络连接已断开，请检查网络'
    } else {
      error.message = '网络异常，请稍后重试'
    }
    return Promise.reject(error)
  }
)

// ===== 认证相关 API =====
export const authRegister = (data) => api.post('/auth/register', data)
export const authLogin = (data) => api.post('/auth/login', data)
export const authGetMe = () => api.get('/auth/me')
export const authUpgrade = (data) => api.post('/auth/upgrade', data)
export const saveLLMConfig = (data) => api.post('/auth/llm-config', data)
export const authGetUsage = () => api.get('/auth/usage')

// 股票分析
export const analyzeStock = (data) => api.post('/analyze', data, { timeout: 120000 })
export const getStockData = (symbol) => api.get(`/stock/${symbol}`)
export const getChartData = (symbol, period = '6mo') => api.get(`/stock/${symbol}/chart`, { params: { period } })
export const getMarketOverview = () => api.get('/market/overview')

// 对话
export const chat = (data) => api.post('/chat', data)

// 组合
export const analyzePortfolio = (data) => api.post('/portfolio/analyze', data)

// 预警
export const getAlerts = (limit = 20) => api.get('/alerts', { params: { limit } })

// 报告
export const getReports = (params) => api.get('/reports', { params })
export const generateReport = (reportType, symbol) => api.post('/reports/generate', null, { params: { report_type: reportType, symbol } })

// 定时任务
export const getScheduledTasks = () => api.get('/tasks')
export const createScheduledTask = (data) => api.post('/tasks', data)
export const deleteScheduledTask = (id) => api.delete(`/tasks/${id}`)

// 智能体状态
export const getAgentStatus = () => api.get('/agents/status')

// 导出Word
export const exportAnalysis = (data) => api.post('/export/analysis', data, { responseType: 'blob' })
export const exportReport = (data) => api.post('/export/report', data, { responseType: 'blob' })
export const exportChat = (data) => api.post('/export/chat', data, { responseType: 'blob' })

// 合规审计
export const getAuditLog = (limit = 50) => api.get('/audit/log', { params: { limit } })

export default api
