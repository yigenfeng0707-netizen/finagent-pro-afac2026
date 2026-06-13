import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authLogin, authRegister, authGetMe, authUpgrade, authGetUsage } from '../api'

const TOKEN_KEY = 'finagent_token'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem(TOKEN_KEY) || '')
  const user = ref(null)
  const usage = ref({ used: 0, limit: 1, plan: 'free', remaining: 1 })

  const isLoggedIn = computed(() => !!token.value)
  const isFreeUser = computed(() => user.value?.plan === 'free')
  const isUsageExceeded = computed(() => {
    if (!isFreeUser.value) return false
    return usage.value.remaining <= 0
  })

  async function login(username, password) {
    const { data } = await authLogin({ username, password })
    token.value = data.token
    user.value = data.user
    localStorage.setItem(TOKEN_KEY, data.token)
  }

  async function register(username, email, password) {
    const { data } = await authRegister({ username, email, password })
    // 注册成功不自动登录，用户需手动登录
    return data
  }

  function logout() {
    token.value = ''
    user.value = null
    usage.value = { used: 0, limit: 1, plan: 'free', remaining: 1 }
    localStorage.removeItem(TOKEN_KEY)
  }

  async function fetchUser() {
    if (!token.value) return
    try {
      const { data } = await authGetMe()
      user.value = data
    } catch {
      logout()
    }
  }

  async function fetchUsage() {
    if (!token.value) return
    try {
      const { data } = await authGetUsage()
      usage.value = data
    } catch {}
  }

  async function upgradePlan(plan) {
    const { data } = await authUpgrade({ plan })
    await fetchUser()
    await fetchUsage()
    return data
  }

  // 初始化时自动获取用户信息
  async function init() {
    if (token.value) {
      await fetchUser()
      await fetchUsage()
    }
  }

  return {
    token, user, usage,
    isLoggedIn, isFreeUser, isUsageExceeded,
    login, register, logout, fetchUser, fetchUsage, upgradePlan, init,
  }
})
