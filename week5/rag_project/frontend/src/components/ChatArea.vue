<template>
  <div class="chat-main">
    <header class="chat-header">
      <h1>RAG 问答助手</h1>
      <div class="header-actions">
        <el-button
          :icon="Search"
          circle
          title="搜索消息"
          @click="toggleSearch"
        />
        <el-button
          :icon="theme === 'dark' ? Sunny : Moon"
          circle
          title="切换主题"
          @click="toggleTheme"
        />
      </div>
    </header>

    <MessageList
      ref="messageListRef"
      :messages="messages"
      :is-loading="isLoading"
      :loading-text="loadingText"
      :show-search="showSearch"
      @message-updated="loadHistory"
      @message-deleted="loadHistory"
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
import { nextTick, onMounted, ref } from 'vue'
import { storeToRefs } from 'pinia'
import { marked } from 'marked'
import { markedHighlight } from 'marked-highlight'
import hljs from 'highlight.js'
import { Moon, Search, Sunny } from '@element-plus/icons-vue'
import { useThemeStore } from '../stores/theme'
import ChatInput from './ChatInput.vue'
import MessageList from './MessageList.vue'

marked.use(markedHighlight({
  langPrefix: 'hljs language-',
  highlight(code, lang) {
    const language = hljs.getLanguage(lang) ? lang : 'plaintext'
    return hljs.highlight(code, { language }).value
  }
}))

const props = defineProps({
  token: {
    type: String,
    required: true
  }
})

const themeStore = useThemeStore()
const { theme } = storeToRefs(themeStore)
const { toggleTheme } = themeStore

const messages = ref([])
const userInput = ref('')
const isLoading = ref(false)
const loadingText = ref('检索并生成中...')
const controller = ref(null)
const messageListRef = ref(null)
const showSearch = ref(false)

function toggleSearch() {
  showSearch.value = !showSearch.value
}

function nowTime() {
  return new Date().toISOString().slice(0, 16).replace('T', ' ')
}

async function handleSend(text) {
  if (!text || isLoading.value) return

  messages.value.push({ role: 'user', content: text, time: nowTime() })
  isLoading.value = true
  await nextTick()

  if (controller.value) {
    controller.value.abort()
  }
  controller.value = new AbortController()

  let fullReply = ''
  let aiMsgIndex = -1

  try {
    const response = await fetch('/api/chat/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${props.token}`
      },
      body: JSON.stringify({
        message: text,
        history: [],
        // week5 当前不再做多会话切换，统一把聊天历史挂在默认会话下。
        session_id: 'default'
      }),
      signal: controller.value.signal
    })

    if (!response.ok || !response.body) {
      const data = await response.json().catch(() => ({}))
      throw new Error(data.detail || `请求失败: ${response.status}`)
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
        if (!line.startsWith('data: ')) continue
        const dataStr = line.slice(6)
        if (dataStr === '[DONE]') continue

        const parsed = JSON.parse(dataStr)
        if (!parsed.content) continue

        fullReply += parsed.content
        // assistant 响应按 markdown 实时渲染，代码块等格式能边生成边展示。
        const html = marked.parse(fullReply)

        if (aiMsgIndex === -1) {
          messages.value.push({ role: 'assistant', content: html, time: nowTime() })
          aiMsgIndex = messages.value.length - 1
        } else {
          messages.value[aiMsgIndex].content = html
        }
      }
    }

    if (aiMsgIndex === -1) {
      messages.value.push({ role: 'assistant', content: '未收到回复', time: nowTime() })
    }
  } catch (error) {
    if (error.name === 'AbortError') {
      if (aiMsgIndex !== -1) {
        messages.value[aiMsgIndex].content = '已停止生成'
      }
      return
    }

    messages.value.push({
      role: 'assistant',
      content: error instanceof Error ? error.message : '请求失败',
      time: nowTime()
    })
  } finally {
    isLoading.value = false
    await loadHistory()
  }
}

function stopGeneration() {
  controller.value?.abort()
  isLoading.value = false
}

async function loadHistory() {
  try {
    const res = await fetch('/api/history?session_id=default', {
      headers: {
        Authorization: `Bearer ${props.token}`
      }
    })
    if (!res.ok) return

    const data = await res.json()
    messages.value = data.map((item) => ({
      id: item.id,
      role: item.role,
      // 数据库存的是原始文本，重新加载历史时要再转一次 markdown HTML。
      content: item.role === 'assistant' ? marked.parse(item.content) : item.content,
      time: item.time ? item.time.slice(0, 16).replace('T', ' ') : ''
    }))

    await nextTick()
    messageListRef.value?.scrollToBottom()
  } catch (error) {
    console.warn('加载历史失败:', error)
  }
}

function clearMessages() {
  messages.value = []
}

defineExpose({
  loadHistory,
  clearMessages
})

onMounted(() => {
  loadHistory()
})
</script>

<style scoped>
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--bg-primary);
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 20px;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
}

.chat-header h1 {
  font-size: 16px;
  color: var(--text-primary);
}

.header-actions {
  display: flex;
  gap: 8px;
}
</style>
