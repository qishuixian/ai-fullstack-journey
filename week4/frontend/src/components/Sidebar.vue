<template>
  <aside class="sidebar">
    <div class="sidebar-header">
      <!-- 顶部操作栏 -->
      <el-button
        type="primary"
        :icon="Plus"
        @click="$emit('create-session')"
        style="width: 100%"
      >
        新建对话
      </el-button>

      <!-- 搜索框 -->
      <el-input
        v-model="searchQuery"
        placeholder="搜索会话..."
        :prefix-icon="Search"
        clearable
        class="search-input"
      />
    </div>

    <!-- 会话列表 -->
    <div class="session-list">
      <!-- 空状态 -->
      <el-empty
        v-if="props.sessions.length === 0"
        description="暂无会话，点击上方按钮创建"
        :image-size="80"
      />

      <!-- 无搜索结果 -->
      <el-empty
        v-else-if="filteredSessions.length === 0"
        description="未找到匹配的会话"
        :image-size="80"
      />

      <!-- 会话列表项 -->
      <div v-else ref="sessionListRef" class="session-items">
        <div
          v-for="session in filteredSessions"
          :key="session.id"
          :data-id="session.id"
          :class="['session-item', { active: session.id === currentSessionId }]"
          @click="handleSessionClick(session.id)"
          @contextmenu.prevent="handleContextMenu($event, session)"
        >
          <!-- 拖拽手柄 -->
          <el-icon class="drag-handle" v-if="!searchQuery">
            <Rank />
          </el-icon>

          <!-- 会话名称（编辑模式） -->
          <el-input
            v-if="editingSessionId === session.id"
            v-model="editingSessionName"
            size="small"
            @blur="saveSessionName(session.id)"
            @keyup.enter="saveSessionName(session.id)"
            @keyup.esc="cancelEdit"
            @click.stop
            ref="editInputRef"
          />

          <!-- 会话名称（正常模式） -->
          <div v-else class="session-info">
            <el-icon v-if="session.pinned" class="pin-icon" color="#409eff">
              <StarFilled />
            </el-icon>
            <span class="session-name">{{ session.name }}</span>
          </div>

          <!-- 更多按钮 -->
          <el-dropdown
            trigger="click"
            @click.stop
            @command="(cmd: string) => handleCommand(cmd, session)"
          >
            <el-icon class="more-btn">
              <MoreFilled />
            </el-icon>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item :icon="session.pinned ? StarFilled : Star" :command="'pin'">
                  {{ session.pinned ? '取消置顶' : '置顶' }}
                </el-dropdown-item>
                <el-dropdown-item :icon="Edit" :command="'edit'">
                  重命名
                </el-dropdown-item>
                <el-dropdown-item :icon="Download" :command="'export-json'">
                  导出为 JSON
                </el-dropdown-item>
                <el-dropdown-item :icon="Document" :command="'export-md'">
                  导出为 Markdown
                </el-dropdown-item>
                <el-dropdown-item :icon="Document" :command="'export-pdf'">
                  导出为 PDF
                </el-dropdown-item>
                <el-dropdown-item :icon="Delete" :command="'delete'" divided>
                  删除
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
    </div>

    <!-- 底部 -->
    <div class="sidebar-footer">
      <el-button
        type="info"
        text
        :icon="SwitchButton"
        @click="$emit('logout')"
        style="width: 100%"
      >
        退出登录
      </el-button>
    </div>

    <!-- 右键菜单 -->
    <el-dropdown
      ref="contextMenuRef"
      :style="{ position: 'fixed', left: contextMenuPos.x + 'px', top: contextMenuPos.y + 'px' }"
      trigger="contextmenu"
      @command="handleContextCommand"
    >
      <span style="display: none"></span>
      <template #dropdown>
        <el-dropdown-menu v-if="contextSession">
          <el-dropdown-item :icon="contextSession.pinned ? StarFilled : Star" command="pin">
            {{ contextSession.pinned ? '取消置顶' : '置顶' }}
          </el-dropdown-item>
          <el-dropdown-item :icon="Edit" command="edit">
            重命名
          </el-dropdown-item>
          <el-dropdown-item :icon="Download" command="export-json">
            导出为 JSON
          </el-dropdown-item>
          <el-dropdown-item :icon="Document" command="export-md">
            导出为 Markdown
          </el-dropdown-item>
          <el-dropdown-item :icon="Delete" command="delete" divided>
            删除
          </el-dropdown-item>
        </el-dropdown-menu>
      </template>
    </el-dropdown>
  </aside>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus,
  Search,
  Rank,
  StarFilled,
  Star,
  Edit,
  Download,
  Document,
  Delete,
  MoreFilled,
  SwitchButton
} from '@element-plus/icons-vue'
import Sortable from 'sortablejs'

interface Session {
  id: string
  name: string
  pinned: number
  created_at?: string
}

const props = defineProps<{
  sessions: Session[]
  currentSessionId: string
  token: string
}>()

const emit = defineEmits(['create-session', 'switch-session', 'delete-session', 'logout', 'session-updated'])

const searchQuery = ref('')
const editingSessionId = ref('')
const editingSessionName = ref('')
const editInputRef = ref()
const sessionListRef = ref<HTMLElement>()
const contextMenuPos = ref({ x: 0, y: 0 })
const contextSession = ref<Session | null>(null)

let sortableInstance: any = null

const filteredSessions = computed(() => {
  if (!searchQuery.value.trim()) return props.sessions
  const q = searchQuery.value.toLowerCase()
  return props.sessions.filter(s => s.name.toLowerCase().includes(q))
})

function handleSessionClick(sessionId: string) {
  if (editingSessionId.value !== sessionId) {
    emit('switch-session', sessionId)
  }
}

// 右键菜单
function handleContextMenu(event: MouseEvent, session: Session) {
  contextMenuPos.value = { x: event.clientX, y: event.clientY }
  contextSession.value = session
  // 触发 Element Plus 的右键菜单（通过 JS 手动触发比较复杂，这里用 dropdown 的 click 模式）
}

function handleCommand(command: string, session: Session) {
  contextSession.value = session
  handleContextCommand(command)
}

async function handleContextCommand(command: string) {
  if (!contextSession.value) return

  const session = contextSession.value

  switch (command) {
    case 'pin':
      await togglePin(session.id)
      break
    case 'edit':
      startEdit(session.id, session.name)
      break
    case 'export-json':
      await exportSession(session.id, session.name, 'json')
      break
    case 'export-md':
      await exportSession(session.id, session.name, 'markdown')
      break
    case 'export-pdf':
      await exportSessionAsPDF(session.id, session.name)
      break
    case 'delete':
      await handleDelete(session.id)
      break
  }

  contextSession.value = null
}

function startEdit(sessionId: string, currentName: string) {
  editingSessionId.value = sessionId
  editingSessionName.value = currentName
  nextTick(() => {
    if (editInputRef.value) {
      const input = Array.isArray(editInputRef.value) ? editInputRef.value[0] : editInputRef.value
      input?.focus()
      input?.select()
    }
  })
}

async function saveSessionName(sessionId: string) {
  if (!editingSessionName.value.trim()) {
    cancelEdit()
    return
  }

  try {
    const res = await fetch(`/api/sessions/${sessionId}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${props.token}`
      },
      body: JSON.stringify({ name: editingSessionName.value.trim() })
    })

    if (res.ok) {
      ElMessage.success('重命名成功')
      emit('session-updated')
    } else {
      throw new Error('重命名失败')
    }
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '重命名失败')
  } finally {
    cancelEdit()
  }
}

function cancelEdit() {
  editingSessionId.value = ''
  editingSessionName.value = ''
}

async function handleDelete(sessionId: string) {
  try {
    await ElMessageBox.confirm('确认删除此会话？删除后无法恢复。', '确认删除', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning'
    })
    emit('delete-session', sessionId)
  } catch {
    // 用户取消删除
  }
}

async function togglePin(sessionId: string) {
  try {
    const res = await fetch(`/api/sessions/${sessionId}/pin`, {
      method: 'PATCH',
      headers: { 'Authorization': `Bearer ${props.token}` }
    })
    if (res.ok) {
      emit('session-updated')
    }
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

async function exportSession(sessionId: string, sessionName: string, format: string) {
  try {
    const res = await fetch(`/api/sessions/${sessionId}/export?format=${format}`, {
      headers: { 'Authorization': `Bearer ${props.token}` }
    })

    if (res.ok) {
      const blob = await res.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${sessionName}.${format === 'markdown' ? 'md' : 'json'}`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      ElMessage.success('导出成功')
    } else {
      throw new Error('导出失败')
    }
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '导出失败')
  }
}

async function exportSessionAsPDF(sessionId: string, sessionName: string) {
  try {
    // 获取会话消息
    const res = await fetch(`/api/history?session_id=${sessionId}`, {
      headers: { 'Authorization': `Bearer ${props.token}` }
    })

    if (!res.ok) {
      throw new Error('获取消息失败')
    }

    const messages = await res.json()

    // 动态导入 jspdf
    const { jsPDF } = await import('jspdf')

    // 创建 PDF 文档
    const doc = new jsPDF()

    // 添加标题
    doc.setFontSize(16)
    doc.text(sessionName, 20, 20)

    doc.setFontSize(10)
    let yPos = 40

    // 添加消息内容
    for (const msg of messages) {
      const role = msg.role === 'user' ? '用户' : 'AI'
      const time = msg.time ? new Date(msg.time).toLocaleString() : ''

      // 角色和时间
      doc.setFontSize(12)
      doc.text(`${role} - ${time}`, 20, yPos)
      yPos += 10

      // 消息内容（简单处理，去除 HTML）
      doc.setFontSize(10)
      const content = msg.content.replace(/<[^>]*>/g, '')
      const lines = doc.splitTextToSize(content, 170)

      lines.forEach((line: string) => {
        if (yPos > 280) {
          doc.addPage()
          yPos = 20
        }
        doc.text(line, 20, yPos)
        yPos += 7
      })

      yPos += 10
    }

    // 保存 PDF
    doc.save(`${sessionName}.pdf`)
    ElMessage.success('PDF 导出成功')
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : 'PDF 导出失败')
  }
}

// 初始化拖拽排序
function initSortable() {
  if (!sessionListRef.value || searchQuery.value) return

  sortableInstance = new Sortable(sessionListRef.value, {
    animation: 150,
    handle: '.drag-handle',
    ghostClass: 'sortable-ghost',
    chosenClass: 'sortable-chosen',
    dragClass: 'sortable-drag',
    onEnd: async () => {
      // 保存排序到后端
      const sessionOrders = Array.from(sessionListRef.value?.children || []).map((el, index) => ({
        id: el.getAttribute('data-id'),
        order: index
      }))

      try {
        const res = await fetch('/api/sessions/order/batch', {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${props.token}`
          },
          body: JSON.stringify({ session_orders: sessionOrders })
        })

        if (res.ok) {
          console.log('排序已保存')
        }
      } catch (e) {
        console.error('保存排序失败:', e)
      }
    }
  })
}

// 监听搜索状态，禁用/启用拖拽
watch(searchQuery, (newVal) => {
  if (sortableInstance) {
    sortableInstance.option('disabled', !!newVal)
  }
})

watch(() => props.sessions.length, () => {
  nextTick(() => {
    if (sortableInstance) {
      sortableInstance.destroy()
      sortableInstance = null
    }
    initSortable()
  })
})

onMounted(() => {
  nextTick(initSortable)
})
</script>

<style scoped>
.sidebar {
  width: 280px;
  background: #f5f7fa;
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
  height: 100vh;
}

.sidebar-header {
  padding: 16px;
  border-bottom: 1px solid #e4e7ed;
}

.search-input {
  margin-top: 12px;
}

.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.session-items {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.session-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  background: white;
  border: 1px solid transparent;
}

.session-item:hover {
  background: #ecf5ff;
  border-color: #d9ecff;
}

.session-item.active {
  background: #409eff;
  color: white;
  border-color: #409eff;
}

.session-item.active .session-name {
  color: white;
}

.drag-handle {
  cursor: grab;
  color: #909399;
  flex-shrink: 0;
}

.drag-handle:active {
  cursor: grabbing;
}

.session-info {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 6px;
  overflow: hidden;
}

.pin-icon {
  flex-shrink: 0;
}

.session-item.active .pin-icon {
  color: white !important;
}

.session-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 14px;
  color: #303133;
}

.more-btn {
  color: #909399;
  cursor: pointer;
  flex-shrink: 0;
  opacity: 0;
  transition: opacity 0.2s;
}

.session-item:hover .more-btn {
  opacity: 1;
}

.session-item.active .more-btn {
  color: white;
  opacity: 1;
}

.more-btn:hover {
  color: #606266;
}

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid #e4e7ed;
}

/* Sortable 拖拽样式 */
.sortable-ghost {
  opacity: 0.4;
  background: #c6e2ff;
}

.sortable-chosen {
  cursor: grabbing;
}

.sortable-drag {
  opacity: 1;
  background: white;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

/* 深色模式适配 */
.dark .sidebar {
  background: #1a1a1a;
  border-right-color: #333;
}

.dark .sidebar-header,
.dark .sidebar-footer {
  border-color: #333;
}

.dark .session-item {
  background: #2a2a2a;
  color: #e0e0e0;
}

.dark .session-item:hover {
  background: #333;
  border-color: #444;
}

.dark .session-name {
  color: #e0e0e0;
}
</style>
