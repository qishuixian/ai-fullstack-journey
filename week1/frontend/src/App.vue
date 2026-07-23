<template>
  <div class="chat-container">
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
        <div class="message-content">{{ msg.content }}</div>
      </div>
      <div v-if="isLoading" class="message assistant">
        <div class="message-role">AI</div>
        <div class="message-content loading">思考中...</div>
      </div>
    </main>

    <footer class="chat-input">
      <input
        v-model="userInput"
        placeholder="输入消息，按 Enter 发送"
        @keyup.enter="sendMessage"
        :disabled="isLoading"
      />
      <button @click="sendMessage" :disabled="isLoading">发送</button>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue'

// 消息类型定义
interface Message {
  role: 'user' | 'assistant'
  content: string
}

// 响应式数据
const messages = ref<Message[]>([])
const userInput = ref('')
const isLoading = ref(false)
const messagesContainer = ref<HTMLElement>()

// 发送消息
async function sendMessage() {
  const text = userInput.value.trim()
  if (!text || isLoading.value) return

  // 添加用户消息到列表
  messages.value.push({ role: 'user', content: text })
  userInput.value = ''
  isLoading.value = true

  // 滚动到底部
  await nextTick()
  scrollToBottom()

  try {
    // 调用后端 API
    const response = await fetch('http://localhost:8000/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text })
    })

    const data = await response.json()
    
    // 添加 AI 回复到列表
    messages.value.push({ role: 'assistant', content: data.reply })
  } catch (error) {
    messages.value.push({
      role: 'assistant',
      content: `❌ 出错了: ${error instanceof Error ? error.message : '未知错误'}`
    })
  } finally {
    isLoading.value = false
    await nextTick()
    scrollToBottom()
  }
}

// 滚动到底部
function scrollToBottom() {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
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
  line-height: 1.5;
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