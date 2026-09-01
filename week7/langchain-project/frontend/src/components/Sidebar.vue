<template>
  <aside :class="['sidebar', { 'mobile-open': isMobileOpen }]">
    <div class="sidebar-top">
      <div>
        <p class="sidebar-kicker">已登录用户</p>
        <h2 class="sidebar-title">{{ username }}</h2>
      </div>

      <el-button type="primary" class="session-btn" @click="$emit('create-session')">
        新建会话
      </el-button>
    </div>

    <div class="session-list">
      <button
        v-for="session in sessions"
        :key="session.id"
        type="button"
        :class="['session-card', { active: session.id === currentSessionId }]"
        @click="$emit('select-session', session.id)"
      >
        <div class="session-card-main">
          <div class="session-card-title">{{ session.title }}</div>
          <div class="session-card-time">{{ formatTime(session.updated_at) }}</div>
        </div>

        <el-popconfirm title="确认删除这个会话吗？" @confirm.stop="$emit('delete-session', session.id)">
          <template #reference>
            <el-button text type="danger" class="session-delete" @click.stop>
              删除
            </el-button>
          </template>
        </el-popconfirm>
      </button>
    </div>

    <div class="sidebar-bottom">
      <div class="sidebar-tip">
        左侧保留你当前账号下的全部会话，互不串数据。
      </div>

      <el-button text class="logout-btn" @click="$emit('logout')">
        退出登录
      </el-button>
    </div>
  </aside>
</template>

<script setup lang="ts">
defineProps<{
  sessions: Array<{
    id: string
    title: string
    created_at: string
    updated_at: string
  }>
  currentSessionId: string
  username: string
  isMobileOpen: boolean
}>()

defineEmits(['create-session', 'select-session', 'delete-session', 'logout'])

function formatTime(value: string) {
  return new Date(value).toLocaleString()
}
</script>

<style scoped>
.sidebar {
  width: 320px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.95), rgba(245, 247, 250, 0.98)),
    #fff;
  border-right: 1px solid rgba(148, 163, 184, 0.22);
  display: flex;
  flex-direction: column;
  height: 100vh;
  backdrop-filter: blur(12px);
}

.sidebar-top,
.sidebar-bottom {
  padding: 20px 18px;
}

.sidebar-top {
  border-bottom: 1px solid rgba(148, 163, 184, 0.18);
}

.sidebar-kicker {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.18em;
  color: #0f766e;
  margin-bottom: 8px;
}

.sidebar-title {
  color: #0f172a;
  font-size: 22px;
  margin-bottom: 16px;
}

.session-btn {
  width: 100%;
}

.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.session-card {
  width: 100%;
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.88);
  padding: 14px 14px 12px;
  text-align: left;
  cursor: pointer;
  transition: 0.2s ease;
}

.session-card:hover,
.session-card.active {
  border-color: rgba(14, 116, 144, 0.35);
  box-shadow: 0 12px 30px rgba(14, 116, 144, 0.12);
  transform: translateY(-1px);
}

.session-card-main {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.session-card-title {
  font-size: 15px;
  color: #0f172a;
  font-weight: 600;
}

.session-card-time {
  font-size: 12px;
  color: #64748b;
}

.session-delete {
  margin-top: 10px;
  padding: 0;
}

.sidebar-bottom {
  border-top: 1px solid rgba(148, 163, 184, 0.18);
}

.sidebar-tip {
  color: #64748b;
  line-height: 1.6;
  margin-bottom: 12px;
}

.logout-btn {
  width: 100%;
  justify-content: center;
}
</style>
