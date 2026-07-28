<template>
  <div class="app-container">
    <!-- ===== 未登录：显示登录/注册页 ===== -->
    <div v-if="!isLoggedIn" class="auth-page">
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
          @keyup.enter="authMode === 'login' ? handleLogin() : handleRegister()"
        />

        <!-- 密码输入 -->
        <input
          v-model="password"
          type="password"
          class="auth-input"
          placeholder="密码"
          @keyup.enter="authMode === 'login' ? handleLogin() : handleRegister()"
        />

        <!-- 提交按钮 -->
        <button
          class="auth-submit"
          :disabled="authLoading"
          @click="authMode === 'login' ? handleLogin() : handleRegister()"
        >
          {{ authLoading ? '处理中...' : (authMode === 'login' ? '登录' : '注册') }}
        </button>
      </div>
    </div>

    <!-- ===== 已登录：显示聊天界面 ===== -->
    <div v-else class="app-layout">
      <!-- 侧边栏 -->
      <aside class="sidebar">
        <div class="sidebar-header">
          <h3>💬 对话</h3>
          <button class="new-chat-btn" @click="createSession">＋ 新对话</button>
        </div>
        <div class="session-list">
          <div
            v-for="session in sessions"
            :key="session.id"
            :class="['session-item', { active: session.id === currentSessionId }]"
            @click="switchSession(session.id)"
          >
            <span class="session-name">{{ session.name }}</span>
            <button class="delete-btn" @click.stop="deleteSession(session.id)">×</button>
          </div>
        </div>
        <div class="sidebar-footer">
          <button class="logout-btn" @click="handleLogout">退出登录</button>
        </div>
      </aside>

      <!-- 主聊天区 -->
      <div class="chat-main">
        <header class="chat-header">
          <h1>🤖 AI 助手</h1>
        </header>

        <main class="chat-messages" ref="messagesContainer">
          <div
            v-for="(msg, index) in messages"
            :key="index"
            :class="['message', msg.role]"
          >
            <div class="message-role">{{ msg.role === 'user' ? '你' : 'AI' }}</div>
            <div class="message-content" v-html="msg.content"></div>
            <div class="message-time">{{ msg.time }}</div>
          </div>
          <div v-if="isLoading" class="message assistant">
            <div class="message-role">AI</div>
            <div class="message-content loading">{{ loadingText }}</div>
          </div>
        </main>

        <footer class="chat-input">
          <input
            v-model="userInput"
            placeholder="输入消息，按 Enter 发送"
            @keyup.enter="sendMessage"
            :disabled="isLoading"
          />
          <button @click.stop="sendMessage" :disabled="isLoading">
            {{ isLoading ? '思考中...' : '发送' }}
          </button>
          <button v-if="isLoading" @click.stop="stopGeneration">停止</button>
        </footer>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted, onUnmounted } from 'vue'
import { marked } from 'marked'

// ===== 认证相关 =====
const isLoggedIn = ref(false)
const authMode = ref('login') // 'login' | 'register'
const username = ref('')
const password = ref('')
const authError = ref('')
const authLoading = ref(false)

// 消息类型
// interface Message { role: string; content: string; time: string }

// 响应式数据
const messages = ref([])
const userInput = ref('')
const isLoading = ref(false)
const controller = ref(null)
const loadingText = ref('思考中...')
const messagesContainer = ref(null)
const ws = ref(null)
const wsMessages = ref([])

// 会话相关
const sessions = ref([])
const currentSessionId = ref('')

// 获取 token
function getToken() {
  return localStorage.getItem('token')
}

// 检查是否已登录
function checkAuth() {
  const token = getToken()
  if (token) {
    isLoggedIn.value = true
    loadSessions()
    loadHistory()
    connectWebSocket()
  } else {
    isLoggedIn.value = false
  }
}

// 登录
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
    isLoggedIn.value = true
    username.value = ''
    password.value = ''
    loadSessions()
    connectWebSocket()
  } catch (e) {
    authError.value = e instanceof Error ? e.message : '登录失败'
  } finally {
    authLoading.value = false
  }
}

// 注册
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

// 退出登录
function handleLogout() {
  localStorage.removeItem('token')
  isLoggedIn.value = false
  messages.value = []
  sessions.value = []
  if (ws.value) {
    ws.value.close()
    ws.value = null
  }
}

// ===== 会话管理 =====
async function loadSessions() {
  try {
    const res = await fetch('/api/sessions', {
      headers: { 'Authorization': `Bearer ${getToken()}` }
    })
    if (res.ok) {
      sessions.value = await res.json()
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
      messages.value = []
      await loadSessions()
    }
  } catch (e) {
    console.error('创建会话失败:', e)
  }
}

async function switchSession(sessionId) {
  currentSessionId.value = sessionId
  await loadHistory(sessionId)
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
        messages.value = []
        currentSessionId.value = ''
      }
    }
  } catch (e) {
    console.error('删除会话失败:', e)
  }
}

// ===== 历史记录 =====
async function loadHistory(sessionId) {
  const sid = sessionId || currentSessionId.value
  if (!sid) return
  try {
    const res = await fetch(`/api/history?session_id=${sid}`, {
      headers: { 'Authorization': `Bearer ${getToken()}` }
    })
    if (res.ok) {
      const data = await res.json()
      messages.value = data.map((m) => ({
        role: m.role,
        content: m.content,
        time: m.time ? m.time.slice(0, 16).replace('T', ' ') : ''
      }))
      await nextTick()
      scrollToBottom()
    }
  } catch (e) {
    console.warn('加载历史记录失败:', e)
  }
}

// ===== WebSocket =====
function connectWebSocket() {
  const token = getToken()
  if (!token) return

  ws.value = new WebSocket(`ws://127.0.0.1:8000/ws?token=${token}`)

  ws.value.onopen = () => {
    console.log('✅ WebSocket 连接成功')
  }

  ws.value.onmessage = (event) => {
    console.log('📩 WebSocket 消息:', event.data)
    wsMessages.value.push(event.data)
  }

  ws.value.onclose = () => {
    console.log('WebSocket 连接关闭')
  }

  ws.value.onerror = (error) => {
    console.error('WebSocket 错误:', error)
  }
}

// ===== 聊天功能 =====
function scrollToBottom() {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

function nowTime() {
  const d = new Date()
  const year = d.getFullYear()
  const month = (d.getMonth() + 1).toString().padStart(2, '0')
  const day = d.getDate().toString().padStart(2, '0')
  const hour = d.getHours().toString().padStart(2, '0')
  const minute = d.getMinutes().toString().padStart(2, '0')
  return `${year}-${month}-${day} ${hour}:${minute}`
}

async function sendMessage() {
  const text = userInput.value.trim()
  if (!text || isLoading.value) return

  messages.value.push({ role: 'user', content: text, time: nowTime() })
  userInput.value = ''
  isLoading.value = true
  loadingText.value = '思考中...'

  const aiMsgIndex = messages.value.length
  messages.value.push({ role: 'assistant', content: '', time: nowTime() })

  await nextTick()
  scrollToBottom()

  if (controller.value) {
    controller.value.abort()
  }
  controller.value = new AbortController()

  let fullReply = ''

  try {
    const response = await fetch('/api/chat/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getToken()}`
      },
      body: JSON.stringify({
        message: text,
        history: []
      }),
      signal: controller.value.signal
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const dataStr = line.slice(6)
          if (dataStr === '[DONE]') break
          try {
            const parsed = JSON.parse(dataStr)
            if (parsed.content) {
              fullReply += parsed.content
              const html = marked.parse(fullReply)
              messages.value[aiMsgIndex].content = html
              scrollToBottom()
            }
          } catch (e) {
            console.warn('Parse error:', e)
          }
        }
      }
    }
  } catch (error) {
    if (error.name === 'AbortError') {
      console.log('请求已被用户手动中断')
      messages.value[aiMsgIndex].content = '已停止'
      return
    }
    console.error('请求失败:', error)
    messages.value[aiMsgIndex].content = '❌ 请求失败'
  } finally {
    isLoading.value = false
    await nextTick()
    scrollToBottom()
    await loadSessions()
  }
}

function clearChat() {
  if (controller.value) {
    controller.value.abort()
    controller.value = null
  }
  isLoading.value = false
  messages.value = []
}

function stopGeneration() {
  if (controller.value) {
    controller.value.abort()
  }
  isLoading.value = false
}

// ===== 生命周期 =====
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

/* ===== 登录/注册页 ===== */
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

/* ===== 主布局 ===== */
.app-layout {
  display: flex;
  height: 100vh;
}

/* ===== 侧边栏 ===== */
.sidebar {
  width: 260px;
  background: #202123;
  color: white;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: 16px;
  border-bottom: 1px solid #333;
}

.sidebar-header h3 {
  font-size: 15px;
  margin-bottom: 12px;
  color: #ccc;
}

.new-chat-btn {
  width: 100%;
  padding: 10px;
  background: #343541;
  color: white;
  border: 1px solid #555;
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  transition: background 0.2s;
}

.new-chat-btn:hover {
  background: #40414f;
}

.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.session-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  margin-bottom: 4px;
  transition: background 0.2s;
}

.session-item:hover {
  background: #343541;
}

.session-item.active {
  background: #40414f;
}

.session-name {
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}

.delete-btn {
  background: none;
  border: none;
  color: #888;
  cursor: pointer;
  font-size: 16px;
  padding: 0 4px;
}

.delete-btn:hover {
  color: #ff4444;
}

.sidebar-footer {
  padding: 12px 16px;
  border-top: 1px solid #333;
}

.logout-btn {
  width: 100%;
  padding: 8px;
  background: none;
  color: #ccc;
  border: 1px solid #555;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
}

.logout-btn:hover {
  background: #343541;
}

/* ===== 聊天主区 ===== */
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #ffffff;
}

.chat-header {
  padding: 14px 20px;
  background: #fafafa;
  border-bottom: 1px solid #e0e0e0;
}

.chat-header h1 {
  font-size: 16px;
  color: #333;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.message {
  max-width: 70%;
  padding: 10px 14px;
  border-radius: 12px;
  word-wrap: break-word;
}

.message.user {
  align-self: flex-end;
  background: #1a73e8;
  color: white;
}

.message.assistant {
  align-self: flex-start;
  background: #f1f3f4;
  color: #333;
}

.message-role {
  font-size: 11px;
  font-weight: bold;
  margin-bottom: 4px;
  opacity: 0.7;
}

.message-content {
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
}

.message-content.loading {
  color: #999;
  font-style: italic;
}

.message-time {
  font-size: 11px;
  color: #999;
  margin-top: 4px;
  text-align: right;
}

.chat-input {
  display: flex;
  padding: 12px 16px;
  border-top: 1px solid #e0e0e0;
  gap: 8px;
}

.chat-input input {
  flex: 1;
  padding: 10px 14px;
  border: 1px solid #d0d0d0;
  border-radius: 8px;
  font-size: 14px;
  outline: none;
}

.chat-input input:focus {
  border-color: #1a73e8;
}

.chat-input button {
  padding: 10px 20px;
  background: #1a73e8;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
}

.chat-input button:hover:not(:disabled) {
  background: #1557b0;
}

.chat-input button:disabled {
  background: #ccc;
  cursor: not-allowed;
}
</style>