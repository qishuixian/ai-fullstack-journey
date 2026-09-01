<template>
  <main ref="containerRef" class="message-list">
    <div
      v-for="message in messages"
      :key="message.localId"
      :class="['message-row', message.role]"
    >
      <div class="message-card">
        <div class="message-meta">
          <span>{{ message.role === 'user' ? '你' : 'Agent' }}</span>
          <span>{{ message.time }}</span>
        </div>
        <div class="message-body" v-html="message.renderedContent" />
      </div>
    </div>

    <div v-if="isLoading" class="message-row assistant">
      <div class="message-card loading-card">
        <span class="typing-dot" />
        <span>{{ loadingText }}</span>
      </div>
    </div>
  </main>
</template>

<script setup lang="ts">
import { nextTick, ref, watch } from 'vue'

interface ChatMessage {
  localId: string
  role: 'user' | 'assistant'
  renderedContent: string
  time: string
}

const props = defineProps<{
  messages: ChatMessage[]
  isLoading: boolean
  loadingText: string
}>()

const containerRef = ref<HTMLElement | null>(null)

function scrollToBottom() {
  if (!containerRef.value) {
    return
  }
  containerRef.value.scrollTop = containerRef.value.scrollHeight
}

watch(
  () => [props.messages, props.isLoading],
  async () => {
    await nextTick()
    scrollToBottom()
  },
  { deep: true }
)

defineExpose({ scrollToBottom })
</script>

<style scoped>
.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.message-row {
  display: flex;
}

.message-row.user {
  justify-content: flex-end;
}

.message-row.assistant {
  justify-content: flex-start;
}

.message-card {
  width: min(840px, 100%);
  border-radius: 22px;
  padding: 16px 18px;
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid rgba(148, 163, 184, 0.18);
  box-shadow: 0 14px 28px rgba(15, 23, 42, 0.06);
}

.message-row.user .message-card {
  background: linear-gradient(135deg, #14532d, #0f766e);
  color: #fff;
}

.message-meta {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  font-size: 12px;
  color: #64748b;
  margin-bottom: 10px;
}

.message-row.user .message-meta {
  color: rgba(255, 255, 255, 0.75);
}

.message-body {
  line-height: 1.7;
  color: #0f172a;
}

.message-row.user .message-body {
  color: #fff;
}

.message-body :deep(pre) {
  background: #0f172a;
  color: #e2e8f0;
  padding: 14px;
  border-radius: 14px;
  overflow-x: auto;
  margin: 12px 0;
}

.message-body :deep(code) {
  font-family: Consolas, Monaco, monospace;
}

.message-body :deep(p code) {
  background: rgba(15, 23, 42, 0.06);
  border-radius: 6px;
  padding: 2px 6px;
}

.loading-card {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #475569;
}

.typing-dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  background: #0f766e;
  animation: pulse 1s infinite ease-in-out;
}

@keyframes pulse {
  0%,
  100% {
    transform: scale(0.7);
    opacity: 0.55;
  }

  50% {
    transform: scale(1);
    opacity: 1;
  }
}
</style>
