<template>
  <div class="p-6 space-y-6">
    <h1 class="text-2xl font-bold text-white">管理后台</h1>

    <div v-if="!isAdmin" class="card border border-danger/50">
      <p class="text-danger">无管理员权限，请联系管理员</p>
    </div>

    <template v-else>
      <!-- 统计卡片 -->
      <div class="grid grid-cols-5 gap-3" v-if="stats">
        <div class="card text-center">
          <div class="text-2xl font-bold text-white">{{ stats.total_users }}</div>
          <div class="text-xs text-dark-400">总用户</div>
        </div>
        <div class="card text-center">
          <div class="text-2xl font-bold text-success">{{ stats.active_24h }}</div>
          <div class="text-xs text-dark-400">24h活跃</div>
        </div>
        <div class="card text-center">
          <div class="text-2xl font-bold text-info">{{ stats.total_analyses }}</div>
          <div class="text-xs text-dark-400">总分析次数</div>
        </div>
        <div class="card text-center">
          <div class="text-2xl font-bold text-warning">{{ stats.total_chats }}</div>
          <div class="text-xs text-dark-400">总对话次数</div>
        </div>
        <div class="card text-center">
          <div class="text-2xl font-bold text-primary">{{ stats.conversion_funnel?.conversion_rate || 0 }}%</div>
          <div class="text-xs text-dark-400">付费转化率</div>
        </div>
      </div>

      <!-- 转化漏斗 -->
      <div class="card" v-if="stats?.conversion_funnel">
        <h3 class="text-lg font-bold text-white mb-3">转化漏斗</h3>
        <div class="space-y-2">
          <div class="flex items-center gap-3">
            <span class="text-sm text-dark-300 w-20">注册用户</span>
            <div class="flex-1 bg-dark-700 rounded-full h-6 overflow-hidden">
              <div class="bg-primary h-full rounded-full flex items-center justify-end px-2" :style="{width: '100%'}">
                <span class="text-xs text-white">{{ stats.conversion_funnel.registered }}</span>
              </div>
            </div>
          </div>
          <div class="flex items-center gap-3">
            <span class="text-sm text-dark-300 w-20">使用过</span>
            <div class="flex-1 bg-dark-700 rounded-full h-6 overflow-hidden">
              <div class="bg-info h-full rounded-full flex items-center justify-end px-2" :style="{width: funnelPercent('used_once')}">
                <span class="text-xs text-white">{{ stats.conversion_funnel.used_once }}</span>
              </div>
            </div>
          </div>
          <div class="flex items-center gap-3">
            <span class="text-sm text-dark-300 w-20">付费用户</span>
            <div class="flex-1 bg-dark-700 rounded-full h-6 overflow-hidden">
              <div class="bg-success h-full rounded-full flex items-center justify-end px-2" :style="{width: funnelPercent('paid')}">
                <span class="text-xs text-white">{{ stats.conversion_funnel.paid }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 计划分布 -->
      <div class="card" v-if="stats?.plan_distribution">
        <h3 class="text-lg font-bold text-white mb-3">计划分布</h3>
        <div class="grid grid-cols-3 gap-3">
          <div class="bg-dark-700 rounded-lg p-3 text-center">
            <div class="text-xl font-bold text-white">{{ stats.plan_distribution.free || 0 }}</div>
            <div class="text-xs text-dark-400">免费版</div>
          </div>
          <div class="bg-dark-700 rounded-lg p-3 text-center">
            <div class="text-xl font-bold text-info">{{ stats.plan_distribution.pro || 0 }}</div>
            <div class="text-xs text-dark-400">专业版</div>
          </div>
          <div class="bg-dark-700 rounded-lg p-3 text-center">
            <div class="text-xl font-bold text-success">{{ stats.plan_distribution.enterprise || 0 }}</div>
            <div class="text-xs text-dark-400">企业版</div>
          </div>
        </div>
      </div>

      <!-- 用户列表 -->
      <div class="card">
        <div class="flex items-center justify-between mb-3">
          <h3 class="text-lg font-bold text-white">用户列表</h3>
          <button @click="loadUsers" class="btn-primary text-sm py-1.5 px-4">刷新</button>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-dark-700">
                <th class="text-left py-2 px-3 text-dark-400">ID</th>
                <th class="text-left py-2 px-3 text-dark-400">用户名</th>
                <th class="text-left py-2 px-3 text-dark-400">邮箱</th>
                <th class="text-left py-2 px-3 text-dark-400">角色</th>
                <th class="text-left py-2 px-3 text-dark-400">计划</th>
                <th class="text-left py-2 px-3 text-dark-400">分析</th>
                <th class="text-left py-2 px-3 text-dark-400">对话</th>
                <th class="text-left py-2 px-3 text-dark-400">导出</th>
                <th class="text-left py-2 px-3 text-dark-400">最后登录</th>
                <th class="text-left py-2 px-3 text-dark-400">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="u in users" :key="u.id" class="border-b border-dark-800 hover:bg-dark-800/50">
                <td class="py-2 px-3 text-dark-300">{{ u.id }}</td>
                <td class="py-2 px-3 text-white font-medium">{{ u.username }}</td>
                <td class="py-2 px-3 text-dark-300">{{ u.email }}</td>
                <td class="py-2 px-3">
                  <span class="badge text-xs" :class="u.role === 'superadmin' ? 'bg-danger/20 text-danger' : u.role === 'admin' ? 'bg-warning/20 text-warning' : 'bg-dark-700 text-dark-300'">{{ u.role }}</span>
                </td>
                <td class="py-2 px-3">
                  <span class="badge text-xs" :class="u.plan === 'enterprise' ? 'bg-success/20 text-success' : u.plan === 'pro' ? 'bg-info/20 text-info' : 'bg-dark-700 text-dark-300'">{{ u.plan }}</span>
                </td>
                <td class="py-2 px-3 text-dark-300">{{ u.total_analyses || 0 }}</td>
                <td class="py-2 px-3 text-dark-300">{{ u.total_chats || 0 }}</td>
                <td class="py-2 px-3 text-dark-300">{{ u.total_exports || 0 }}</td>
                <td class="py-2 px-3 text-dark-400 text-xs">{{ formatTime(u.last_login_at) }}</td>
                <td class="py-2 px-3">
                  <button @click="viewProfile(u.id)" class="text-primary text-xs hover:underline">画像</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- 用户画像弹窗 -->
      <div v-if="showProfile && profile" class="fixed inset-0 bg-black/60 flex items-center justify-center z-50" @click.self="showProfile = false">
        <div class="bg-dark-900 rounded-xl p-6 max-w-lg w-full mx-4 max-h-[80vh] overflow-y-auto">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-bold text-white">用户画像 - {{ profile.user?.username }}</h3>
            <button @click="showProfile = false" class="text-dark-400 hover:text-white">X</button>
          </div>
          <div class="space-y-3">
            <div class="grid grid-cols-2 gap-3">
              <div class="bg-dark-800 rounded-lg p-3">
                <div class="text-xs text-dark-400">参与度评分</div>
                <div class="text-xl font-bold text-white">{{ profile.engagement_score }}/100</div>
              </div>
              <div class="bg-dark-800 rounded-lg p-3">
                <div class="text-xs text-dark-400">活跃天数</div>
                <div class="text-xl font-bold text-white">{{ profile.active_days }}</div>
              </div>
            </div>
            <div class="bg-dark-800 rounded-lg p-3">
              <div class="text-xs text-dark-400 mb-2">行为偏好</div>
              <div class="flex gap-2 flex-wrap">
                <span v-for="(count, action) in profile.action_counts" :key="action" class="badge bg-primary/20 text-primary text-xs">{{ action }}: {{ count }}</span>
              </div>
            </div>
            <div class="bg-dark-800 rounded-lg p-3">
              <div class="text-xs text-dark-400 mb-1">用户类型</div>
              <span class="text-white text-sm">{{ profile.is_new_user ? '新用户(7天内)' : '老用户' }}</span>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useUserStore } from '../stores/user'
import api from '../api'

const userStore = useUserStore()
const stats = ref(null)
const users = ref([])
const profile = ref(null)
const showProfile = ref(false)

const isAdmin = computed(() => {
  const u = userStore.user
  return u && (u.role === 'admin' || u.role === 'superadmin')
})

async function loadStats() {
  try {
    const { data } = await api.get('/auth/admin/stats')
    stats.value = data
  } catch (e) {
    console.error('加载统计失败', e)
  }
}

async function loadUsers() {
  try {
    const { data } = await api.get('/auth/admin/users', { params: { limit: 100 } })
    users.value = data.users || []
  } catch (e) {
    console.error('加载用户列表失败', e)
  }
}

async function viewProfile(userId) {
  try {
    const { data } = await api.get(`/auth/admin/user/${userId}/profile`)
    profile.value = data
    showProfile.value = true
  } catch (e) {
    console.error('加载用户画像失败', e)
  }
}

function funnelPercent(key) {
  if (!stats.value?.conversion_funnel) return '0%'
  const total = stats.value.conversion_funnel.registered || 1
  const val = stats.value.conversion_funnel[key] || 0
  return Math.max(2, Math.round(val / total * 100)) + '%'
}

function formatTime(ts) {
  if (!ts) return '-'
  try { return new Date(ts).toLocaleString('zh-CN') } catch { return ts }
}

onMounted(() => {
  if (isAdmin.value) {
    loadStats()
    loadUsers()
  }
})
</script>
