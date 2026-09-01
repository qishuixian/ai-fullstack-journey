<template>
  <div class="shell">
    <LoginForm v-if="!isLoggedIn" @login-success="handleLoginSuccess" />

    <div v-else class="shell-layout">
      <div
        v-if="isMobileSidebarOpen"
        class="mobile-mask"
        @click="isMobileSidebarOpen = false"
      />

      <Sidebar
        :sessions="sessions"
        :current-session-id="currentSessionId"
        :username="username"
        :is-mobile-open="isMobileSidebarOpen"
        @create-session="handleCreateSession"
        @select-session="handleSelectSession"
        @delete-session="handleDeleteSession"
        @logout="handleLogout"
      />

      <ChatArea
        ref="chatAreaRef"
        :token="getToken()"
        :session-id="currentSessionId"
        @toggle-sidebar="isMobileSidebarOpen = !isMobileSidebarOpen"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import ChatArea from './components/ChatArea.vue'
import LoginForm from './components/LoginForm.vue'
import Sidebar from './components/Sidebar.vue'

interface SessionItem {
  id: string
  title: string
  created_at: string
  updated_at: string
}

const isLoggedIn = ref(false)
const sessions = ref<SessionItem[]>([])
const currentSessionId = ref('')
const username = ref('')
const chatAreaRef = ref<InstanceType<typeof ChatArea> | null>(null)
const isMobileSidebarOpen = ref(false)

function getToken() {
  return localStorage.getItem('token') || ''
}

async function request(path: string, options: RequestInit = {}) {
  const res = await fetch(path, {
    ...options,
    headers: {
      Authorization: `Bearer ${getToken()}`,
      ...(options.headers || {})
    }
  })

  if (res.status === 401) {
    handleLogout()
    throw new Error('登录状态已过期，请重新登录')
  }

  return res
}

async function loadProfile() {
  const res = await request('/api/me')
  if (res.ok) {
    const data = await res.json()
    username.value = data.username
  }
}

async function loadSessions() {
  const res = await request('/api/sessions')
  if (!res.ok) {
    throw new Error('加载会话失败')
  }

  const data = await res.json()
  sessions.value = data
  if (!currentSessionId.value && data.length > 0) {
    currentSessionId.value = data[0].id
  }
}

async function ensureDefaultSession() {
  await loadSessions()
  if (!sessions.value.length) {
    await handleCreateSession()
  }
}

async function handleCreateSession() {
  const res = await request('/api/sessions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({})
  })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.detail || '创建会话失败')
  }

  const data = await res.json()
  sessions.value.unshift(data)
  currentSessionId.value = data.id
  isMobileSidebarOpen.value = false
  chatAreaRef.value?.loadHistory()
}

function handleSelectSession(sessionId: string) {
  currentSessionId.value = sessionId
  isMobileSidebarOpen.value = false
  chatAreaRef.value?.loadHistory()
}

async function handleDeleteSession(sessionId: string) {
  const res = await request(`/api/sessions/${sessionId}`, { method: 'DELETE' })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.detail || '删除会话失败')
  }

  sessions.value = sessions.value.filter((item) => item.id !== sessionId)
  if (currentSessionId.value === sessionId) {
    currentSessionId.value = sessions.value[0]?.id || ''
    if (!currentSessionId.value) {
      await handleCreateSession()
    } else {
      chatAreaRef.value?.loadHistory()
    }
  }
}

async function initAfterLogin() {
  await loadProfile()
  await ensureDefaultSession()
  isLoggedIn.value = true
  chatAreaRef.value?.loadHistory()
}

async function handleLoginSuccess() {
  try {
    await initAfterLogin()
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '初始化失败')
  }
}

function handleLogout() {
  localStorage.removeItem('token')
  isLoggedIn.value = false
  sessions.value = []
  currentSessionId.value = ''
  username.value = ''
  isMobileSidebarOpen.value = false
  chatAreaRef.value?.clearMessages()
}

onMounted(async () => {
  if (!getToken()) {
    return
  }

  try {
    await initAfterLogin()
  } catch (error) {
    handleLogout()
  }
})
</script>
