<template>
  <div class="auth-page">
    <div class="auth-card">
      <h1 class="auth-title">🤖 AI 助手</h1>
      <p class="auth-subtitle">登录后开始对话</p>

      <!-- 切换登录/注册 -->
      <div class="auth-tabs">
        <button :class="['tab-btn', { active: authMode === 'login' }]" @click="authMode = 'login'">登录</button>
        <button :class="['tab-btn', { active: authMode === 'register' }]" @click="authMode = 'register'">注册</button>
      </div>

      <!-- 错误提示 -->
      <div v-if="authError" class="auth-error">{{ authError }}</div>

      <!-- 用户名输入 -->
      <input
        v-model="username"
        class="auth-input"
        placeholder="用户名"
        @keyup.enter="handleSubmit"
      />

      <!-- 密码输入 -->
      <input
        v-model="password"
        type="password"
        class="auth-input"
        placeholder="密码"
        @keyup.enter="handleSubmit"
      />

      <!-- 提交按钮 -->
      <button
        class="auth-submit"
        :disabled="authLoading"
        @click="handleSubmit"
      >
        {{ authLoading ? '处理中...' : (authMode === 'login' ? '登录' : '注册') }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const emit = defineEmits(['login-success'])

const authMode = ref('login')
const username = ref('')
const password = ref('')
const authError = ref('')
const authLoading = ref(false)

async function handleSubmit() {
  if (authMode.value === 'login') {
    await handleLogin()
  } else {
    await handleRegister()
  }
}

async function handleLogin() {
  authError.value = ''
  authLoading.value = true
  try {
    const formData = new FormData()
    formData.append('username', username.value)
    formData.append('password', password.value)

    const res = await fetch('/api/token', {
      method: 'POST',
      body: formData
    })

    if (!res.ok) {
      const data = await res.json()
      throw new Error(data.detail || '登录失败')
    }

    const data = await res.json()
    localStorage.setItem('token', data.access_token)
    username.value = ''
    password.value = ''
    emit('login-success')
  } catch (e) {
    authError.value = e instanceof Error ? e.message : '登录失败'
  } finally {
    authLoading.value = false
  }
}

async function handleRegister() {
  authError.value = ''
  authLoading.value = true
  try {
    const formData = new FormData()
    formData.append('username', username.value)
    formData.append('password', password.value)

    const res = await fetch('/api/register', {
      method: 'POST',
      body: formData
    })

    if (!res.ok) {
      const data = await res.json()
      throw new Error(data.detail || '注册失败')
    }

    // 注册成功后自动登录
    await handleLogin()
  } catch (e) {
    authError.value = e instanceof Error ? e.message : '注册失败'
  } finally {
    authLoading.value = false
  }
}
</script>

<style scoped>
.auth-page {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.auth-card {
  background: white;
  padding: 40px;
  border-radius: 16px;
  box-shadow: 0 10px 40px rgba(0,0,0,0.2);
  width: 380px;
}

.auth-title {
  font-size: 24px;
  text-align: center;
  margin-bottom: 8px;
}

.auth-subtitle {
  text-align: center;
  color: #666;
  margin-bottom: 24px;
  font-size: 14px;
}

.auth-tabs {
  display: flex;
  margin-bottom: 20px;
  border-bottom: 2px solid #f0f0f0;
}

.tab-btn {
  flex: 1;
  padding: 10px;
  background: none;
  border: none;
  font-size: 15px;
  cursor: pointer;
  color: #999;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
  transition: all 0.2s;
}

.tab-btn.active {
  color: #1a73e8;
  border-bottom-color: #1a73e8;
  font-weight: bold;
}

.auth-input {
  width: 100%;
  padding: 12px 14px;
  margin-bottom: 14px;
  border: 1px solid #d0d0d0;
  border-radius: 8px;
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
}

.auth-input:focus {
  border-color: #1a73e8;
}

.auth-submit {
  width: 100%;
  padding: 12px;
  background: #1a73e8;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 15px;
  cursor: pointer;
  transition: background 0.2s;
}

.auth-submit:hover:not(:disabled) {
  background: #1557b0;
}

.auth-submit:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.auth-error {
  background: #fce8e8;
  color: #d93025;
  padding: 10px 12px;
  border-radius: 8px;
  margin-bottom: 14px;
  font-size: 13px;
}
</style>
