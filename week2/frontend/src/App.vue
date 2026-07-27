<template>
  <div class="chat-container">
    <header class="chat-header">
      <h1>🤖 AI 助手（流式版）</h1>
      <button class="clear-btn" @click.stop="clearChat">清空对话</button>
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
</template>

<script setup lang="ts">
import { ref, nextTick, watchEffect, watch, onMounted, onUnmounted } from 'vue'
import { marked } from 'marked'
// 消息类型
interface Message {
  role: 'user' | 'assistant'
  content:  string | Promise<string>, 
  time: string  // 新增
}

// 响应式数据
const messages = ref<Message[]>([])
const userInput = ref('')
const isLoading = ref(false)
const controller = ref<AbortController | null>(null)  // 添加这行
const loadingText = ref('思考中...')
const messagesContainer = ref<HTMLElement>()
// WebSocket 相关
const ws = ref<WebSocket | null>(null)
const wsMessages = ref<string[]>([])  // 用于显示 WebSocket 消息
// 连接 WebSocket
function connectWebSocket() {
  ws.value = new WebSocket('ws://127.0.0.1:8000/ws')
  
  ws.value.onopen = () => {
    console.log('WebSocket 连接成功')
  }
  
  ws.value.onmessage = (event) => {
    console.log('收到 WebSocket 消息:', event.data)
    wsMessages.value.push(event.data)
  }
  
  ws.value.onclose = () => {
    console.log('WebSocket 连接关闭')
  }
  
  ws.value.onerror = (error) => {
    console.error('WebSocket 错误:', error)
  }
}
// 发送 WebSocket 消息
function sendWsMessage(text: string) {
  if (ws.value && ws.value.readyState === WebSocket.OPEN) {
    ws.value.send(text)
  }
}

onMounted(async () => {
  // 页面加载时读取
// const saved = localStorage.getItem('chat')
// if (saved) {
//   messages.value = JSON.parse(saved)
// }
connectWebSocket()
try {
    const res = await fetch('/api/history?session_id=default')
    const data = await res.json()
    if (data && data.length > 0) {
      messages.value = data.map((m: any) => ({
        role: m.role,
        content: m.content,
        time: m.time ? m.time.slice(0, 16).replace('T', ' ') : ''
      }))
      // 滚动到底部
      await nextTick()
      scrollToBottom()
    }
  } catch (e) {
    console.warn('加载历史记录失败:', e)
  }
})
// 页面卸载时断开
onUnmounted(() => {
  if (ws.value) {
    ws.value.close()
  }
})

// 每次消息更新后保存
// function saveChat() {
//   localStorage.setItem('chat', JSON.stringify(messages.value))
// }

// watch(messages, () => {
//   saveChat()
// }, { deep: true })

// 历史记录（发给后端）
let chatHistory: Array<{ role: string; content: string }> = []

// 滚动到底部
function scrollToBottom() {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}
// 获取当前时间，格式 YYYY-MM-DD HH:MM
function nowTime(): string {
  const d = new Date()
  const year = d.getFullYear()
  const month = (d.getMonth() + 1).toString().padStart(2, '0')
  const day = d.getDate().toString().padStart(2, '0')
  const hour = d.getHours().toString().padStart(2, '0')
  const minute = d.getMinutes().toString().padStart(2, '0')
  return `${year}-${month}-${day} ${hour}:${minute}`
}
// 发送消息（核心：流式输出）
async function sendMessage() {
  const text = userInput.value.trim()
  // 如果有内容、正在加载、或者没有控制器，直接返回
  if (!text || isLoading.value ) return

  // 添加用户消息
  messages.value.push({ role: 'user', content: text,time: nowTime() })
  userInput.value = ''
  isLoading.value = true
  loadingText.value = '思考中...'

  // 注意：这里必须放在 fetch 之前，否则停止时找不到这个消息对象
  const aiMsgIndex = messages.value.length
  messages.value.push({ role: 'assistant', content: '',time: nowTime() })

  await nextTick()
  scrollToBottom()

  // 【新增】如果之前有未完成的请求，先取消掉
  if (controller.value) {
    controller.value.abort()
  }
  
  // 【新增】创建新的控制器  
  controller.value = new AbortController()
  
  let fullReply = ''

  try {
    const response = await fetch('/api/chat/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: text,
        history: chatHistory
      }),
      signal: controller.value.signal 
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    // 逐块读取流式响应
    const reader = response.body!.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    
    while (true) {
      const { done, value } = await reader.read()
      
      if (done) {
        controller.value = null; 
        break;
      }

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
              // 实时更新消息内容
              // messages.value[aiMsgIndex].content = fullReply
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

    // 更新历史记录
    chatHistory.push({ role: 'user', content: text })
    chatHistory.push({ role: 'assistant', content: fullReply })

  } catch (error) {
    if (error.name === 'AbortError') {
      console.log('请求已被用户手动中断');
      // 即使停止了，也把已收到的内容记入历史，保持上下文连贯
      chatHistory.push({ role: 'user', content: text });
      chatHistory.push({ role: 'assistant', content:  fullReply || ''});
      messages.value[aiMsgIndex].content = '已停止'
      return; 
    }

    console.error('请求失败:', error);
    if (messages.value[aiMsgIndex]) {
       messages.value[aiMsgIndex].content = '❌ ' + (error instanceof Error ? error.message : '未知错误');
    }
  } finally {
    isLoading.value = false
    await nextTick()
    scrollToBottom()
  }
}
// 清空对话（优化版）
// 清空对话（修复版）
function clearChat() {
  // 1. 如果正在请求，强制中断
  if (controller.value) {
    controller.value.abort();
    controller.value = null; 
  }
  
  // 2. 重置所有状态
  isLoading.value = false; 
  
  // 3. 清空数据
  messages.value = [];
  chatHistory = [];
}
// 停止生成
function stopGeneration() {
  if (controller.value) {
    controller.value.abort()
  }
  isLoading.value = false
  // 此时 messages 中最后一条 AI 消息已经保留了已输出的内容
  // 需要将它加入 chatHistory
}
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

.chat-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100%;
  margin: 0 auto;
  background: white;
  box-shadow: 0 0 10px rgba(0,0,0,0.1);
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: #1a73e8;
  color: white;
}
.message-time {
  font-size: 11px;
  color: #999;
  margin-top: 4px;
  text-align: right;
}
.message.user .message-time {
  text-align: right;
}
.message.assistant .message-time {
  text-align: left;
}
.clear-btn {
  padding: 6px 14px;
  background: rgba(255, 255, 255, 0.2);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.4);
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  transition: background 0.2s;
}

.clear-btn:hover {
  background: rgba(255, 255, 255, 0.3);
}
.chat-header h1 {
  font-size: 18px;
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
  transition: border-color 0.2s;
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
  transition: background 0.2s;
}

.chat-input button:hover:not(:disabled) {
  background: #1557b0;
}

.chat-input button:disabled {
  background: #ccc;
  cursor: not-allowed;
}
</style>