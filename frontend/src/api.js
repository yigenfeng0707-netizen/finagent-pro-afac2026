import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 60000,
  headers: { 'Content-Type': 'application/json' },
})

// 股票分析
export const analyzeStock = (data) => api.post('/analyze', data)
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
