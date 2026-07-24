<template>
  <div class="chat-container">
    <header class="chat-header">
      <h1>🤖 AI 助手（流式版）</h1>
    </header>

    <main class="chat-messages" ref="messagesContainer">
      <div
        v-for="(msg, index) in messages"
        :key="index"
        :class="['message', msg.role]"
      >
        <div class="message-role">{{ msg.role === 'user' ? '你' : 'AI' }}</div>
        <div class="message-content">{{ msg.content }}</div>
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
      <button @click="sendMessage" :disabled="isLoading">
        {{ isLoading ? '思考中...' : '发送' }}
      </button>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue'

// 消息类型
interface Message {
  role: 'user' | 'assistant'
  content: string
}

// 响应式数据
const messages = ref<Message[]>([])
const userInput = ref('')
const isLoading = ref(false)
const loadingText = ref('思考中...')
const messagesContainer = ref<HTMLElement>()

// 历史记录（发给后端）
let chatHistory: Array<{ role: string; content: string }> = []

// 滚动到底部
function scrollToBottom() {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

// 发送消息（核心：流式输出）
async function sendMessage() {
  const text = userInput.value.trim()
  if (!text || isLoading.value) return

  // 添加用户消息
  messages.value.push({ role: 'user', content: text })
  userInput.value = ''
  isLoading.value = true
  loadingText.value = '思考中...'

  // 创建一个空的 AI 消息，后续逐步填充
  const aiMsgIndex = messages.value.length
  messages.value.push({ role: 'assistant', content: '' })

  await nextTick()
  scrollToBottom()

  try {
    const response = await fetch('/api/chat/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: text,
        history: chatHistory
      })
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    // 逐块读取流式响应
    const reader = response.body!.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    let fullReply = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })

      // 按行分割 SSE 数据
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
              // 实时更新消息内容 → 打字机效果
              messages.value[aiMsgIndex].content = fullReply
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
    messages.value[aiMsgIndex].content =
      '❌ 请求失败: ' + (error instanceof Error ? error.message : '未知错误')
  } finally {
    isLoading.value = false
    await nextTick()
    scrollToBottom()
  }
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
  padding: 16px 20px;
  background: #1a73e8;
  color: white;
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