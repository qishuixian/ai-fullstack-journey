<template>
  <section class="chat-shell">
    <div class="chat-main">
      <header class="chat-header">
        <div class="chat-header-left">
          <el-button class="mobile-toggle" @click="$emit('toggle-sidebar')">会话</el-button>
          <div>
            <p class="chat-kicker">SSE Streaming</p>
            <h1>Chat Agent 实时控制台</h1>
          </div>
        </div>
        <div class="chat-status">
          <el-tag :type="isLoading ? 'warning' : 'success'">
            {{ isLoading ? '生成中' : '空闲' }}
          </el-tag>
        </div>
      </header>

      <MessageList
        ref="messageListRef"
        :messages="messages"
        :is-loading="isLoading"
        :loading-text="loadingText"
      />

      <ChatInput
        v-model="userInput"
        :is-loading="isLoading"
        @send="handleSend"
        @stop="stopGeneration"
      />
    </div>

    <ToolPanel :tool-events="toolEvents" />
  </section>
</template>

<script setup lang="ts">
import { nextTick, onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { marked } from 'marked'
import { markedHighlight } from 'marked-highlight'
import hljs from 'highlight.js'
import ChatInput from './ChatInput.vue'
import MessageList from './MessageList.vue'
import ToolPanel from './ToolPanel.vue'

marked.use(markedHighlight({
  langPrefix: 'hljs language-',
  highlight(code, lang) {
    const language = hljs.getLanguage(lang) ? lang : 'plaintext'
    return hljs.highlight(code, { language }).value
  }
}))

interface MessageRecord {
  localId: string
  id?: number
  role: 'user' | 'assistant'
  rawContent: string
  renderedContent: string
  time: string
}

interface ToolEventRecord {
  id: string
  type: string
  typeLabel: string
  toolName?: string
  content: string
  time: string
}

const props = defineProps<{
  token: string
  sessionId: string
}>()

defineEmits(['toggle-sidebar'])

const messages = ref<MessageRecord[]>([])
const toolEvents = ref<ToolEventRecord[]>([])
const userInput = ref('')
const isLoading = ref(false)
const loadingText = ref('Agent 正在思考并调度工具...')
const controller = ref<AbortController | null>(null)
const messageListRef = ref<InstanceType<typeof MessageList> | null>(null)

function nowLabel() {
  return new Date().toLocaleTimeString()
}

function createLocalId() {
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`
}

function renderMarkdown(text: string) {
  return text ? String(marked.parse(text)) : ''
}

function appendToolEvent(type: string, content: string, toolName?: string) {
  const typeLabelMap: Record<string, string> = {
    thinking: '思考',
    tool_result: '工具结果',
    retry: '重试',
    error: '错误'
  }
  toolEvents.value.unshift({
    id: createLocalId(),
    type,
    typeLabel: typeLabelMap[type] || type,
    toolName,
    content,
    time: nowLabel()
  })
}

async function loadHistory() {
  if (!props.sessionId || !props.token) {
    messages.value = []
    toolEvents.value = []
    return
  }

  const res = await fetch(`/api/history?session_id=${encodeURIComponent(props.sessionId)}`, {
    headers: { Authorization: `Bearer ${props.token}` }
  })
  if (!res.ok) {
    return
  }

  const data = await res.json()
  messages.value = data.map((item: any) => ({
    localId: createLocalId(),
    id: item.id,
    role: item.role,
    rawContent: item.content,
    renderedContent: item.role === 'assistant' ? renderMarkdown(item.content) : item.content,
    time: new Date(item.time).toLocaleString()
  }))
  toolEvents.value = []
  await nextTick()
  messageListRef.value?.scrollToBottom()
}

async function handleSend(text: string) {
  if (!props.sessionId || !text.trim() || isLoading.value) {
    return
  }

  toolEvents.value = []
  messages.value.push({
    localId: createLocalId(),
    role: 'user',
    rawContent: text,
    renderedContent: text,
    time: nowLabel()
  })

  const assistantMessage: MessageRecord = {
    localId: createLocalId(),
    role: 'assistant',
    rawContent: '',
    renderedContent: '',
    time: nowLabel()
  }
  messages.value.push(assistantMessage)

  controller.value?.abort()
  controller.value = new AbortController()
  isLoading.value = true

  try {
    const response = await fetch('/api/chat/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${props.token}`
      },
      body: JSON.stringify({
        message: text,
        session_id: props.sessionId
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
      if (done) {
        break
      }

      buffer += decoder.decode(value, { stream: true })
      const segments = buffer.split('\n\n')
      buffer = segments.pop() || ''

      for (const segment of segments) {
        const line = segment
          .split('\n')
          .find((item) => item.startsWith('data: '))
        if (!line) {
          continue
        }

        const payload = JSON.parse(line.slice(6))
        if (payload.type === 'token') {
          assistantMessage.rawContent += payload.content || ''
          assistantMessage.renderedContent = renderMarkdown(assistantMessage.rawContent)
        } else if (payload.type === 'final') {
          assistantMessage.rawContent = payload.content || assistantMessage.rawContent
          assistantMessage.renderedContent = renderMarkdown(assistantMessage.rawContent)
        } else if (payload.type === 'thinking' || payload.type === 'tool_result' || payload.type === 'retry') {
          appendToolEvent(payload.type, payload.content || '', payload.tool_name)
        } else if (payload.type === 'error') {
          appendToolEvent('error', payload.content || '发生未知错误')
          throw new Error(payload.content || '请求失败')
        } else if (payload.type === 'done') {
          await loadHistory()
        }
      }
    }
  } catch (error: any) {
    if (error?.name === 'AbortError') {
      appendToolEvent('error', '本次生成已手动停止')
    } else {
      ElMessage.error(error instanceof Error ? error.message : '请求失败')
      assistantMessage.rawContent = error instanceof Error ? error.message : '请求失败'
      assistantMessage.renderedContent = renderMarkdown(assistantMessage.rawContent)
    }
  } finally {
    isLoading.value = false
  }
}

function stopGeneration() {
  controller.value?.abort()
  isLoading.value = false
}

function clearMessages() {
  messages.value = []
  toolEvents.value = []
}

watch(
  () => props.sessionId,
  () => {
    loadHistory()
  }
)

onMounted(() => {
  loadHistory()
})

defineExpose({
  loadHistory,
  clearMessages
})
</script>

<style scoped>
.chat-shell {
  flex: 1;
  display: flex;
  min-width: 0;
  background:
    radial-gradient(circle at top right, rgba(56, 189, 248, 0.1), transparent 22%),
    radial-gradient(circle at bottom left, rgba(249, 115, 22, 0.08), transparent 24%),
    linear-gradient(180deg, #f8fbff 0%, #f4f7fb 100%);
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  padding: 18px 22px;
  border-bottom: 1px solid var(--border-color);
  background: rgba(255, 255, 255, 0.78);
  backdrop-filter: blur(10px);
}

.chat-header-left {
  display: flex;
  align-items: center;
  gap: 14px;
}

.chat-kicker {
  font-size: 12px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: #0f766e;
  margin-bottom: 6px;
}

.chat-header h1 {
  color: #0f172a;
  font-size: 22px;
}

.mobile-toggle {
  display: none;
}

@media (max-width: 1100px) {
  .chat-shell {
    flex-direction: column;
  }

  .mobile-toggle {
    display: inline-flex;
  }
}
</style>
