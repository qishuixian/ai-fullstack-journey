<template>
  <main class="chat-messages" ref="messagesContainer">
    <!-- 搜索栏 -->
    <div v-if="showSearch" class="message-search">
      <el-input
        v-model="searchQuery"
        placeholder="搜索消息内容..."
        :prefix-icon="Search"
        clearable
        @input="handleSearch"
      />
    </div>

    <div
      v-for="(msg, index) in filteredMessages"
      :key="index"
      :class="['message-wrapper', msg.role]"
      @mouseenter="hoveredIndex = index"
      @mouseleave="hoveredIndex = -1"
    >
      <el-avatar :size="36" class="message-avatar">
        {{ msg.role === 'user' ? '你' : 'AI' }}
      </el-avatar>

      <div class="message-content-wrapper">
        <div class="message-header">
          <span class="message-role">{{ msg.role === 'user' ? '你' : 'AI 助手' }}</span>
          <div class="message-actions">
            <span class="message-time">{{ msg.time }}</span>
            <!-- 操作按钮 -->
            <div v-if="hoveredIndex === index && msg.id" class="action-buttons">
              <el-button
                :icon="Edit"
                circle
                size="small"
                @click="handleEdit(msg, index)"
                title="编辑"
              />
              <el-button
                :icon="Delete"
                circle
                size="small"
                type="danger"
                @click="handleDelete(msg)"
                title="删除"
              />
            </div>
          </div>
        </div>

        <!-- 编辑模式 -->
        <div v-if="editingIndex === index" class="message-edit">
          <el-input
            v-model="editingContent"
            type="textarea"
            :rows="4"
            placeholder="编辑消息内容"
          />
          <div class="edit-actions">
            <el-button size="small" @click="cancelEdit">取消</el-button>
            <el-button size="small" type="primary" @click="saveEdit(msg)">保存</el-button>
          </div>
        </div>

        <!-- 正常显示模式 -->
        <div v-else class="message-content" v-html="msg.content" ref="contentRefs"></div>
      </div>
    </div>

    <!-- Loading 状态 -->
    <div v-if="isLoading" class="message-wrapper assistant">
      <el-avatar :size="36" class="message-avatar">AI</el-avatar>
      <div class="message-content-wrapper">
        <div class="message-header">
          <span class="message-role">AI 助手</span>
        </div>
        <div class="message-loading">
          <el-icon class="is-loading"><Loading /></el-icon>
          <span>{{ loadingText }}</span>
        </div>
      </div>
    </div>

    <!-- 无搜索结果 -->
    <el-empty
      v-if="showSearch && searchQuery && filteredMessages.length === 0"
      description="未找到匹配的消息"
      :image-size="100"
    />
  </main>
</template>

<script setup lang="ts">
import { ref, watch, nextTick, onMounted, onUpdated, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Loading, Edit, Delete, Search } from '@element-plus/icons-vue'
import hljs from 'highlight.js'
import 'highlight.js/styles/github-dark.css'

interface Message {
  id?: number
  role: string
  content: string
  time: string
}

const props = defineProps<{
  messages: Message[]
  isLoading: boolean
  loadingText: string
  showSearch?: boolean
}>()

const emit = defineEmits(['message-updated', 'message-deleted'])

const messagesContainer = ref<HTMLElement>()
const contentRefs = ref<HTMLElement[]>([])
const hoveredIndex = ref(-1)
const editingIndex = ref(-1)
const editingContent = ref('')
const searchQuery = ref('')

const filteredMessages = computed(() => {
  if (!searchQuery.value.trim()) return props.messages
  const query = searchQuery.value.toLowerCase()
  return props.messages.filter(msg =>
    msg.content.toLowerCase().includes(query)
  )
})

function handleSearch() {
  // 搜索时自动滚动到第一个匹配项
  if (filteredMessages.value.length > 0) {
    nextTick(scrollToBottom)
  }
}

function handleEdit(msg: Message, index: number) {
  editingIndex.value = index
  // 从 HTML 中提取纯文本（简单处理）
  const div = document.createElement('div')
  div.innerHTML = msg.content
  editingContent.value = div.textContent || div.innerText || msg.content
}

function cancelEdit() {
  editingIndex.value = -1
  editingContent.value = ''
}

async function saveEdit(msg: Message) {
  if (!editingContent.value.trim()) {
    ElMessage.warning('消息内容不能为空')
    return
  }

  if (!msg.id) {
    ElMessage.warning('无法编辑此消息')
    return
  }

  try {
    const token = localStorage.getItem('token')
    const res = await fetch(`/api/messages/${msg.id}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ content: editingContent.value })
    })

    if (res.ok) {
      ElMessage.success('消息已更新')
      emit('message-updated')
      cancelEdit()
    } else {
      throw new Error('更新失败')
    }
  } catch (error) {
    ElMessage.error('更新消息失败')
  }
}

async function handleDelete(msg: Message) {
  if (!msg.id) {
    ElMessage.warning('无法删除此消息')
    return
  }

  try {
    await ElMessageBox.confirm('确认删除此消息？删除后无法恢复。', '确认删除', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning'
    })

    const token = localStorage.getItem('token')
    const res = await fetch(`/api/messages/${msg.id}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    if (res.ok) {
      ElMessage.success('消息已删除')
      emit('message-deleted')
    } else {
      throw new Error('删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除消息失败')
    }
  }
}

function scrollToBottom() {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

// 为代码块添加复制按钮
function addCopyButtons() {
  nextTick(() => {
    if (!messagesContainer.value) return

    const codeBlocks = messagesContainer.value.querySelectorAll('pre code')
    codeBlocks.forEach((block) => {
      // 如果已经有复制按钮，跳过
      if (block.parentElement?.querySelector('.copy-btn')) return

      // 高亮代码
      hljs.highlightElement(block as HTMLElement)

      // 创建复制按钮
      const button = document.createElement('button')
      button.className = 'copy-btn'
      button.innerHTML = `
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
          <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
        </svg>
        <span>复制</span>
      `

      button.addEventListener('click', async () => {
        const code = block.textContent || ''
        try {
          await navigator.clipboard.writeText(code)
          button.innerHTML = `
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="20 6 9 17 4 12"></polyline>
            </svg>
            <span>已复制</span>
          `
          button.classList.add('copied')

          setTimeout(() => {
            button.innerHTML = `
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
              </svg>
              <span>复制</span>
            `
            button.classList.remove('copied')
          }, 2000)
        } catch (err) {
          ElMessage.error('复制失败')
        }
      })

      // 将按钮添加到 pre 元素
      const pre = block.parentElement
      if (pre && !pre.querySelector('.copy-btn')) {
        pre.style.position = 'relative'
        pre.appendChild(button)
      }
    })
  })
}

// 监听消息变化，自动滚动到底部并添加复制按钮
watch(() => props.messages, async () => {
  await nextTick()
  addCopyButtons()
  scrollToBottom()
}, { deep: true })

watch(() => props.isLoading, async () => {
  await nextTick()
  scrollToBottom()
})

onMounted(() => {
  addCopyButtons()
})

onUpdated(() => {
  addCopyButtons()
})

defineExpose({
  scrollToBottom
})
</script>

<style scoped>
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 24px;
  background: #f5f7fa;
}

.message-search {
  position: sticky;
  top: 0;
  z-index: 10;
  background: #f5f7fa;
  padding-bottom: 12px;
  margin-bottom: 12px;
}

.message-wrapper {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.message-wrapper.user {
  flex-direction: row-reverse;
}

.message-avatar {
  flex-shrink: 0;
  background: #409eff;
  color: white;
  font-size: 14px;
  font-weight: 500;
}

.message-wrapper.user .message-avatar {
  background: #67c23a;
}

.message-content-wrapper {
  flex: 1;
  max-width: calc(100% - 60px);
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.message-role {
  font-size: 13px;
  font-weight: 600;
  color: #303133;
}

.message-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.message-time {
  font-size: 12px;
  color: #909399;
}

.action-buttons {
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.2s;
}

.message-wrapper:hover .action-buttons {
  opacity: 1;
}

.message-edit {
  background: white;
  padding: 12px;
  border-radius: 8px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.edit-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 8px;
}

.message-content {
  background: white;
  padding: 12px 16px;
  border-radius: 8px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  font-size: 14px;
  line-height: 1.6;
  color: #303133;
  word-wrap: break-word;
}

.message-wrapper.user .message-content {
  background: #409eff;
  color: white;
}

.message-loading {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: white;
  border-radius: 8px;
  color: #909399;
  font-size: 14px;
}

/* 代码块样式 */
.message-content :deep(pre) {
  position: relative;
  background: #1e1e1e !important;
  border-radius: 8px;
  padding: 16px;
  margin: 12px 0;
  overflow-x: auto;
}

.message-content :deep(code) {
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.5;
}

.message-content :deep(p code) {
  background: #f4f4f5;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 13px;
  color: #e74c3c;
}

.message-wrapper.user .message-content :deep(p code) {
  background: rgba(255, 255, 255, 0.2);
  color: white;
}

/* 复制按钮 */
.message-content :deep(.copy-btn) {
  position: absolute;
  top: 8px;
  right: 8px;
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 10px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 6px;
  color: #fff;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
  opacity: 0;
}

.message-content :deep(pre:hover .copy-btn) {
  opacity: 1;
}

.message-content :deep(.copy-btn:hover) {
  background: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.3);
}

.message-content :deep(.copy-btn.copied) {
  background: #67c23a;
  border-color: #67c23a;
}

/* Markdown 样式 */
.message-content :deep(h1),
.message-content :deep(h2),
.message-content :deep(h3) {
  margin-top: 16px;
  margin-bottom: 8px;
  font-weight: 600;
}

.message-content :deep(p) {
  margin: 8px 0;
}

.message-content :deep(ul),
.message-content :deep(ol) {
  padding-left: 24px;
  margin: 8px 0;
}

.message-content :deep(li) {
  margin: 4px 0;
}

.message-content :deep(blockquote) {
  border-left: 4px solid #dcdfe6;
  padding-left: 12px;
  margin: 12px 0;
  color: #606266;
}

.message-content :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 12px 0;
}

.message-content :deep(th),
.message-content :deep(td) {
  border: 1px solid #dcdfe6;
  padding: 8px 12px;
  text-align: left;
}

.message-content :deep(th) {
  background: #f5f7fa;
  font-weight: 600;
}

/* 滚动条样式 */
.chat-messages::-webkit-scrollbar {
  width: 6px;
}

.chat-messages::-webkit-scrollbar-track {
  background: transparent;
}

.chat-messages::-webkit-scrollbar-thumb {
  background: #d0d0d0;
  border-radius: 3px;
}

.chat-messages::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style>
