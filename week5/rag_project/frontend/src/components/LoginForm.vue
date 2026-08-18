<template>
  <div class="auth-page">
    <el-card class="auth-card">
      <template #header>
        <div class="auth-header">
          <h1 class="auth-title">🤖 AI 助手</h1>
          <p class="auth-subtitle">登录后开始对话</p>
        </div>
      </template>

      <!-- 切换登录/注册 -->
      <el-tabs v-model="authMode" class="auth-tabs">
        <el-tab-pane label="登录" name="login"></el-tab-pane>
        <el-tab-pane label="注册" name="register"></el-tab-pane>
      </el-tabs>

      <!-- 表单 -->
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
            placeholder="请输入用户名"
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

        <el-form-item>
          <el-button
            type="primary"
            :loading="authLoading"
            @click="handleSubmit"
            style="width: 100%"
          >
            {{ authMode === 'login' ? '登录' : '注册' }}
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'

const emit = defineEmits(['login-success'])

const authMode = ref('login')
const authLoading = ref(false)
const formRef = ref<FormInstance>()

const formData = reactive({
  username: '',
  password: ''
})

// 表单校验规则
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

async function handleSubmit() {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (valid) {
      if (authMode.value === 'login') {
        await handleLogin()
      } else {
        await handleRegister()
      }
    }
  })
}

async function handleLogin() {
  authLoading.value = true
  try {
    const formDataToSend = new FormData()
    formDataToSend.append('username', formData.username)
    formDataToSend.append('password', formData.password)

    const res = await fetch('/api/token', {
      method: 'POST',
      body: formDataToSend
    })

    if (!res.ok) {
      const data = await res.json()
      throw new Error(data.detail || '登录失败')
    }

    const data = await res.json()
    localStorage.setItem('token', data.access_token)

    ElMessage.success('登录成功！')
    formData.username = ''
    formData.password = ''
    emit('login-success')
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '登录失败')
  } finally {
    authLoading.value = false
  }
}

async function handleRegister() {
  authLoading.value = true
  try {
    const formDataToSend = new FormData()
    formDataToSend.append('username', formData.username)
    formDataToSend.append('password', formData.password)

    const res = await fetch('/api/register', {
      method: 'POST',
      body: formDataToSend
    })

    if (!res.ok) {
      const data = await res.json()
      throw new Error(data.detail || '注册失败')
    }

    ElMessage.success('注册成功！正在自动登录...')
    // 注册成功后自动登录
    await handleLogin()
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '注册失败')
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
  width: 420px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
}

.auth-header {
  text-align: center;
}

.auth-title {
  font-size: 28px;
  margin: 0 0 8px 0;
  color: #303133;
}

.auth-subtitle {
  color: #909399;
  margin: 0;
  font-size: 14px;
}

.auth-tabs {
  margin-bottom: 20px;
}

:deep(.el-tabs__nav-wrap::after) {
  background-color: #f0f0f0;
}
</style>
