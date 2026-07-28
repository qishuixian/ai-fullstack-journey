<template>
  <aside class="sidebar">
    <div class="sidebar-header">
      <h3>💬 对话</h3>
      <button class="new-chat-btn" @click="$emit('create-session')">＋ 新对话</button>
    </div>
    <div class="session-list">
      <div
        v-for="session in filteredSessions"
        :key="session.id"
        :class="['session-item', { active: session.id === currentSessionId }]"
        @click="handleSessionClick(session.id)"
      >
        <input
          v-if="editingSessionId === session.id"
          v-model="editingSessionName"
          class="session-name-input"
          @blur="saveSessionName(session.id)"
          @keyup.enter="saveSessionName(session.id)"
          @keyup.esc="cancelEdit"
          @click.stop
          ref="editInput"
        />
        <span
          v-else
          class="session-name"
        >
          {{ session.name }}
        </span>
        <button class="menu-btn" @click.stop="toggleMenu(session.id)">⋮</button>

        <!-- 下拉菜单 -->
        <div v-if="activeMenuId === session.id" class="context-menu" @click.stop>
          <div class="menu-item" @click="startEdit(session.id, session.name)">
            <span class="menu-icon">✏️</span>
            <span>编辑名称</span>
          </div>
          <div class="menu-item delete" @click="handleDelete(session.id)">
            <span class="menu-icon">🗑️</span>
            <span>删除</span>
          </div>
        </div>
      </div>
    </div>
    <div class="sidebar-footer">
      <button class="logout-btn" @click="$emit('logout')">退出登录</button>
    </div>
  </aside>
</template>

<script setup>
import { ref, computed, nextTick, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  sessions: {
    type: Array,
    required: true
  },
  currentSessionId: {
    type: String,
    default: ''
  },
  token: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['create-session', 'switch-session', 'delete-session', 'logout', 'session-updated'])

const searchQuery = ref('')
const editingSessionId = ref('')
const editingSessionName = ref('')
const editInput = ref(null)
const activeMenuId = ref('')

const filteredSessions = computed(() => {
  if (!searchQuery.value.trim()) return props.sessions
  const q = searchQuery.value.toLowerCase()
  return props.sessions.filter(s => s.name.toLowerCase().includes(q))
})

function handleSessionClick(sessionId) {
  if (editingSessionId.value !== sessionId) {
    emit('switch-session', sessionId)
  }
}

function toggleMenu(sessionId) {
  activeMenuId.value = activeMenuId.value === sessionId ? '' : sessionId
}

function closeMenu() {
  activeMenuId.value = ''
}

function startEdit(sessionId, currentName) {
  closeMenu()
  editingSessionId.value = sessionId
  editingSessionName.value = currentName
  nextTick(() => {
    if (editInput.value && editInput.value[0]) {
      editInput.value[0].focus()
      editInput.value[0].select()
    }
  })
}

async function saveSessionName(sessionId) {
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
      emit('session-updated')
    }
  } catch (e) {
    console.error('更新会话名称失败:', e)
  } finally {
    cancelEdit()
  }
}

function cancelEdit() {
  editingSessionId.value = ''
  editingSessionName.value = ''
}

function handleDelete(sessionId) {
  closeMenu()
  emit('delete-session', sessionId)
}

// 点击外部关闭菜单
function handleClickOutside(event) {
  if (!event.target.closest('.menu-btn') && !event.target.closest('.context-menu')) {
    closeMenu()
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
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
  position: relative;
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

.session-name-input {
  flex: 1;
  background: #40414f;
  border: 1px solid #1a73e8;
  border-radius: 4px;
  color: white;
  padding: 4px 8px;
  font-size: 13px;
  outline: none;
}

.menu-btn {
  background: none;
  border: none;
  color: #888;
  cursor: pointer;
  font-size: 18px;
  padding: 0 4px;
  line-height: 1;
  opacity: 0;
  transition: opacity 0.2s;
}

.session-item:hover .menu-btn {
  opacity: 1;
}

.menu-btn:hover {
  color: #ccc;
}

.context-menu {
  position: absolute;
  right: 8px;
  top: 100%;
  background: #2a2b32;
  border: 1px solid #444;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  z-index: 100;
  min-width: 150px;
  margin-top: 4px;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.2s;
}

.menu-item:first-child {
  border-radius: 8px 8px 0 0;
}

.menu-item:last-child {
  border-radius: 0 0 8px 8px;
}

.menu-item:hover {
  background: #343541;
}

.menu-item.delete {
  color: #ff4444;
}

.menu-item.delete:hover {
  background: #3d2020;
}

.menu-icon {
  font-size: 14px;
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
</style>
