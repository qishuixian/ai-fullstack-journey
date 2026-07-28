<template>
  <aside class="sidebar">
    <div class="sidebar-header">
      <h3>💬 对话</h3>
      <button class="new-chat-btn" @click="$emit('create-session')">＋ 新对话</button>
    </div>
    <div class="session-list">
      <div
        v-for="session in sessions"
        :key="session.id"
        :class="['session-item', { active: session.id === currentSessionId }]"
        @click="$emit('switch-session', session.id)"
      >
        <span class="session-name">{{ session.name }}</span>
        <button class="delete-btn" @click.stop="$emit('delete-session', session.id)">×</button>
      </div>
    </div>
    <div class="sidebar-footer">
      <button class="logout-btn" @click="$emit('logout')">退出登录</button>
    </div>
  </aside>
</template>

<script setup>
defineProps({
  sessions: {
    type: Array,
    required: true
  },
  currentSessionId: {
    type: String,
    default: ''
  }
})

defineEmits(['create-session', 'switch-session', 'delete-session', 'logout'])
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
</style>
