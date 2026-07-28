<template>
  <div class="chat-main">
    <header class="chat-header">
      <h1>🤖 AI 助手</h1>
    </header>

    <MessageList
      :messages="messages"
      :is-loading="isLoading"
      :loading-text="loadingText"
      ref="messageListRef"
    />

    <ChatInput
      v-model="userInput"
      :is-loading="isLoading"
      @send="handleSend"
      @stop="stopGeneration"
    />
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { marked } from 'marked'
import MessageList from './MessageList.vue'
import ChatInput from './ChatInput.vue'

const props = defineProps({
  token: {
    type: String,
    required: true
  },
  currentSessionId: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['sessions-updated'])

const messages = ref([])
const userInput = ref('')
const isLoading = ref(false)
const controller = ref(null)
const loadingText = ref('思考中...')
const messageListRef = ref(null)

function nowTime() {
  const d = new Date()
  const year = d.getFullYear()
  const month = (d.getMonth() + 1).toString().padStart(2, '0')
  const day = d.getDate().toString().padStart(2, '0')
  const hour = d.getHours().toString().padStart(2, '0')
  const minute = d.getMinutes().toString().padStart(2, '0')
  return `${year}-${month}-${day} ${hour}:${minute}`
}

async function handleSend(text) {
  if (!text || isLoading.value) return

  // 如果当前没有会话ID，不允许发送
  if (!props.currentSessionId) {
    console.warn('没有选中会话，无法发送消息')
    return
  }

  const isFirstMessage = messages.value.length === 0

  messages.value.push({ role: 'user', content: text, time: nowTime() })
  isLoading.value = true
  loadingText.value = '思考中...'

  const aiMsgIndex = messages.value.length
  messages.value.push({ role: 'assistant', content: '', time: nowTime() })

  await nextTick()

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
        'Authorization': `Bearer ${props.token}`
      },
      body: JSON.stringify({
        message: text,
        history: [],
        session_id: props.currentSessionId || 'default'
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
            }
          } catch (e) {
            console.warn('Parse error:', e)
          }
        }
      }
    }

    // 如果是第一条消息，用消息内容更新会话名称
    if (isFirstMessage && props.currentSessionId) {
      const sessionName = text.length > 20 ? text.substring(0, 20) + '...' : text
      await fetch(`/api/sessions/${props.currentSessionId}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${props.token}`
        },
        body: JSON.stringify({ name: sessionName })
      })
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
    emit('sessions-updated')
  }
}

function stopGeneration() {
  if (controller.value) {
    controller.value.abort()
  }
  isLoading.value = false
}

async function loadHistory(sessionId) {
  if (!sessionId) return
  try {
    const res = await fetch(`/api/history?session_id=${sessionId}`, {
      headers: { 'Authorization': `Bearer ${props.token}` }
    })
    if (res.ok) {
      const data = await res.json()
      messages.value = data.map((m) => ({
        role: m.role,
        content: m.content,
        time: m.time ? m.time.slice(0, 16).replace('T', ' ') : ''
      }))
      await nextTick()
      if (messageListRef.value) {
        messageListRef.value.scrollToBottom()
      }
    }
  } catch (e) {
    console.warn('加载历史记录失败:', e)
  }
}

function clearMessages() {
  messages.value = []
}

defineExpose({
  loadHistory,
  clearMessages
})
</script>

<style scoped>
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
</style>
