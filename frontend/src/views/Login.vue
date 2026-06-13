<template>
  <div class="min-h-screen flex items-center justify-center bg-dark-950 px-4">
    <div class="w-full max-w-md">
      <!-- Logo -->
      <div class="text-center mb-8">
        <div class="w-16 h-16 bg-primary-600 rounded-2xl flex items-center justify-center text-white font-bold text-2xl mx-auto mb-4">F</div>
        <h1 class="text-2xl font-bold text-white">FinAgent Pro</h1>
        <p class="text-dark-400 mt-1">金融自主智能体平台</p>
      </div>

      <!-- 切换标签 -->
      <div class="flex bg-dark-800 rounded-lg p-1 mb-6">
        <button
          @click="mode = 'login'"
          class="flex-1 py-2 text-sm font-medium rounded-md transition-colors"
          :class="mode === 'login' ? 'bg-primary-600 text-white' : 'text-dark-400 hover:text-white'"
        >登录</button>
        <button
          @click="mode = 'register'"
          class="flex-1 py-2 text-sm font-medium rounded-md transition-colors"
          :class="mode === 'register' ? 'bg-primary-600 text-white' : 'text-dark-400 hover:text-white'"
        >注册</button>
      </div>

      <!-- 表单 -->
      <form @submit.prevent="handleSubmit" class="space-y-4">
        <div v-if="mode === 'register'">
          <label class="block text-sm text-dark-300 mb-1.5">用户名</label>
          <input v-model="form.username" type="text" required minlength="3" maxlength="50"
            class="input-dark w-full" placeholder="请输入用户名" />
        </div>

        <div>
          <label class="block text-sm text-dark-300 mb-1.5">{{ mode === 'login' ? '用户名' : '邮箱' }}</label>
          <input v-if="mode === 'login'" v-model="form.username" type="text" required
            class="input-dark w-full" placeholder="请输入用户名" />
          <input v-else v-model="form.email" type="email" required
            class="input-dark w-full" placeholder="请输入邮箱" />
        </div>

        <div>
          <label class="block text-sm text-dark-300 mb-1.5">密码</label>
          <input v-model="form.password" type="password" required minlength="6"
            class="input-dark w-full" placeholder="请输入密码" />
        </div>

        <div v-if="mode === 'register'">
          <label class="block text-sm text-dark-300 mb-1.5">确认密码</label>
          <input v-model="form.confirmPassword" type="password" required minlength="6"
            class="input-dark w-full" placeholder="请再次输入密码" />
        </div>

        <!-- 错误提示 -->
        <div v-if="errorMsg" class="text-danger text-sm bg-danger/10 border border-danger/30 rounded-lg px-3 py-2">
          {{ errorMsg }}
        </div>

        <button type="submit" :disabled="loading"
          class="w-full btn-primary py-2.5 flex items-center justify-center gap-2 disabled:opacity-50">
          <div v-if="loading" class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
          {{ mode === 'login' ? '登 录' : '注 册' }}
        </button>
      </form>

      <!-- 底部提示 -->
      <p class="text-center text-dark-500 text-sm mt-6">
        {{ mode === 'login' ? '还没有账号？' : '已有账号？' }}
        <button @click="mode = mode === 'login' ? 'register' : 'login'" class="text-primary-400 hover:text-primary-300">
          {{ mode === 'login' ? '立即注册' : '立即登录' }}
        </button>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'

const router = useRouter()
const userStore = useUserStore()

const mode = ref('login')
const loading = ref(false)
const errorMsg = ref('')

const form = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
})

async function handleSubmit() {
  errorMsg.value = ''
  loading.value = true

  try {
    if (mode.value === 'register') {
      if (form.password !== form.confirmPassword) {
        errorMsg.value = '两次输入的密码不一致'
        return
      }
      await userStore.register(form.username, form.email, form.password)
      // 注册成功后不自动登录，切换到登录页并提示
      mode.value = 'login'
      form.confirmPassword = ''
      errorMsg.value = ''
      alert('注册成功！请登录')
    } else {
      await userStore.login(form.username, form.password)
      router.push('/')
    }
  } catch (err) {
    errorMsg.value = err.response?.data?.detail || err.message || '操作失败，请重试'
  } finally {
    loading.value = false
  }
}
</script>
