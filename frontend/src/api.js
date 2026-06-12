import axios from 'axios'

// 生产环境使用Render后端地址，开发环境走Vite代理
const baseURL = import.meta.env.VITE_API_URL
  ? import.meta.env.VITE_API_URL + '/api'
  : '/api'

const api = axios.create({
  baseURL,
  timeout: 60000,
  headers: { 'Content-Type': 'application/json' },
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

// 合规审计
export const getAuditLog = (limit = 50) => api.get('/audit/log', { params: { limit } })

export default api
