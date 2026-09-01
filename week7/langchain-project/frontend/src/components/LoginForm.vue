<template>
  <div class="auth-page">
    <div class="auth-aurora auth-aurora-left" />
    <div class="auth-aurora auth-aurora-right" />

    <el-card class="auth-card">
      <template #header>
        <div class="auth-header">
          <p class="auth-kicker">Week 7 Agent</p>
          <h1 class="auth-title">Chat Agent 控制台</h1>
          <p class="auth-subtitle">登录后即可体验工具调用、实时推流和会话隔离。</p>
        </div>
      </template>

      <el-tabs v-model="authMode" class="auth-tabs">
        <el-tab-pane label="登录" name="login" />
        <el-tab-pane label="注册" name="register" />
      </el-tabs>

      <el-form
        ref="formRef"
        :model="formData"
        :rules="rules"
        label-position="top"
        @keyup.enter="handleSubmit"
      >
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="formData.username"
            placeholder="例如 qishuixian"
            :prefix-icon="User"
            clearable
          />
        </el-form-item>

        <el-form-item label="密码" prop="password">
          <el-input
            v-model="formData.password"
            type="password"
            placeholder="请输入密码"
            :prefix-icon="Lock"
            show-password
            clearable
          />
        </el-form-item>

        <el-button type="primary" :loading="authLoading" class="submit-btn" @click="handleSubmit">
          {{ authMode === 'login' ? '进入控制台' : '创建账号并进入' }}
        </el-button>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Lock, User } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'

const emit = defineEmits(['login-success'])

const authMode = ref('login')
const authLoading = ref(false)
const formRef = ref<FormInstance>()
const formData = reactive({
  username: '',
  password: ''
})

const rules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度应为 3-20 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 50, message: '密码长度应为 6-50 个字符', trigger: 'blur' }
  ]
}

async function postAuth(path: string) {
  const payload = new FormData()
  payload.append('username', formData.username)
  payload.append('password', formData.password)

  const res = await fetch(path, { method: 'POST', body: payload })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    throw new Error(data.detail || '请求失败')
  }
  return data
}

async function handleLogin() {
  const data = await postAuth('/api/token')
  localStorage.setItem('token', data.access_token)
  ElMessage.success('登录成功')
  emit('login-success')
}

async function handleRegister() {
  await postAuth('/api/register')
  ElMessage.success('注册成功，正在为你登录')
  await handleLogin()
}

async function handleSubmit() {
  if (!formRef.value) {
    return
  }

  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) {
    return
  }

  authLoading.value = true
  try {
    if (authMode.value === 'login') {
      await handleLogin()
    } else {
      await handleRegister()
    }
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '操作失败')
  } finally {
    authLoading.value = false
  }
}
</script>

<style scoped>
.auth-page {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  background:
    radial-gradient(circle at top left, rgba(255, 184, 108, 0.36), transparent 28%),
    radial-gradient(circle at bottom right, rgba(66, 153, 225, 0.28), transparent 25%),
    linear-gradient(135deg, #fff8ef 0%, #f3f7ff 48%, #edf8f4 100%);
}

.auth-aurora {
  position: absolute;
  width: 26rem;
  height: 26rem;
  border-radius: 999px;
  filter: blur(48px);
  opacity: 0.6;
}

.auth-aurora-left {
  left: -8rem;
  top: -8rem;
  background: rgba(255, 123, 0, 0.2);
}

.auth-aurora-right {
  right: -10rem;
  bottom: -8rem;
  background: rgba(0, 122, 204, 0.22);
}

.auth-card {
  width: min(460px, calc(100vw - 32px));
  position: relative;
  z-index: 1;
  border-radius: 24px;
  border: 1px solid rgba(148, 163, 184, 0.2);
  box-shadow: 0 20px 60px rgba(15, 23, 42, 0.12);
}

.auth-header {
  text-align: center;
}

.auth-kicker {
  font-size: 12px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: #0f766e;
  margin-bottom: 12px;
}

.auth-title {
  font-size: 32px;
  line-height: 1.15;
  color: #0f172a;
  margin-bottom: 10px;
}

.auth-subtitle {
  color: #475569;
  line-height: 1.6;
}

.auth-tabs {
  margin-bottom: 22px;
}

.submit-btn {
  width: 100%;
  height: 46px;
  margin-top: 8px;
}
</style>
