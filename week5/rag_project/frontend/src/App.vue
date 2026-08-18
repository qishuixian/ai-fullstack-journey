<template>
  <div class="app-container">
    <!-- 未登录：显示登录/注册页 -->
    <LoginForm v-if="!isLoggedIn" @login-success="handleLoginSuccess" />

    <!-- 已登录：显示聊天界面 -->
    <div v-else class="app-layout">
      <Sidebar
        :sessions="sessions"
        :current-session-id="currentSessionId"
        :token="getToken()"
        @create-session="createSession"
        @switch-session="switchSession"
        @delete-session="deleteSession"
        @logout="handleLogout"
        @session-updated="loadSessions"
      />

      <ChatArea
        ref="chatAreaRef"
        :token="getToken()"
        :current-session-id="currentSessionId"
        @sessions-updated="loadSessions"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import LoginForm from './components/LoginForm.vue'
import Sidebar from './components/Sidebar.vue'
import ChatArea from './components/ChatArea.vue'

// 认证相关
const isLoggedIn = ref(false)

// 会话相关
const sessions = ref([])
const currentSessionId = ref('')
const chatAreaRef = ref(null)

// WebSocket
const ws = ref(null)

// 获取 token
function getToken() {
  return localStorage.getItem('token') || ''
}

// 检查是否已登录
function checkAuth() {
  const token = getToken()
  if (token) {
    isLoggedIn.value = true
    loadSessions()
    connectWebSocket()
  } else {
    isLoggedIn.value = false
  }
}

// 登录成功回调
function handleLoginSuccess() {
  isLoggedIn.value = true
  loadSessions()
  connectWebSocket()
}

// 退出登录
function handleLogout() {
  localStorage.removeItem('token')
  isLoggedIn.value = false
  sessions.value = []
  currentSessionId.value = ''
  if (ws.value) {
    ws.value.close()
    ws.value = null
  }
}

// 会话管理
async function loadSessions() {
  try {
    const res = await fetch('/api/sessions', {
      headers: { 'Authorization': `Bearer ${getToken()}` }
    })
    if (res.ok) {
      sessions.value = await res.json()
      // 如果没有当前会话，自动选择第一个会话
      if (!currentSessionId.value && sessions.value.length > 0) {
        await switchSession(sessions.value[0].id)
      }
    }
  } catch (e) {
    console.warn('加载会话列表失败:', e)
  }
}

async function createSession() {
  try {
    const res = await fetch('/api/sessions', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${getToken()}` }
    })
    if (res.ok) {
      const data = await res.json()
      sessions.value.unshift(data)
      currentSessionId.value = data.id
      if (chatAreaRef.value) {
        chatAreaRef.value.clearMessages()
      }
      await loadSessions()
    }
  } catch (e) {
    console.error('创建会话失败:', e)
  }
}

async function switchSession(sessionId) {
  currentSessionId.value = sessionId
  if (chatAreaRef.value) {
    await chatAreaRef.value.loadHistory(sessionId)
  }
}

async function deleteSession(sessionId) {
  try {
    await fetch(`/api/sessions/${sessionId}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${getToken()}` }
    })
    sessions.value = sessions.value.filter(s => s.id !== sessionId)
    if (currentSessionId.value === sessionId) {
      if (sessions.value.length > 0) {
        switchSession(sessions.value[0].id)
      } else {
        if (chatAreaRef.value) {
          chatAreaRef.value.clearMessages()
        }
        currentSessionId.value = ''
      }
    }
  } catch (e) {
    console.error('删除会话失败:', e)
  }
}

// WebSocket
function connectWebSocket() {
  const token = getToken()
  if (!token) return

  const wsProtocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
  ws.value = new WebSocket(`${wsProtocol}//${location.host}/ws?token=${token}`)

  ws.value.onopen = () => {
    console.log('✅ WebSocket 连接成功')
  }

  ws.value.onmessage = (event) => {
    console.log('📩 WebSocket 消息:', event.data)
  }

  ws.value.onclose = () => {
    console.log('WebSocket 连接关闭')
  }

  ws.value.onerror = (error) => {
    console.error('WebSocket 错误:', error)
  }
}

// 生命周期
onMounted(() => {
  checkAuth()
})

onUnmounted(() => {
  if (ws.value) {
    ws.value.close()
  }
})
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: #f0f2f5;
  height: 100vh;
}

.app-container {
  height: 100vh;
}

.app-layout {
  display: flex;
  height: 100vh;
}
</style>
