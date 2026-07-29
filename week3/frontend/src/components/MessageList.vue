<template>
  <main class="chat-messages" ref="messagesContainer">
    <div
      v-for="(msg, index) in messages"
      :key="index"
      :class="['message', msg.role]"
    >
      <div class="message-role">{{ msg.role === 'user' ? '你' : 'AI' }}</div>
      <div class="message-content" v-html="msg.content"></div>
      <div class="message-time">{{ msg.time }}</div>
    </div>
    <div v-if="isLoading" class="message assistant">
      <div class="message-role">AI</div>
      <div class="message-content loading">{{ loadingText }}</div>
    </div>
  </main>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'

const props = defineProps({
  messages: {
    type: Array,
    required: true
  },
  isLoading: {
    type: Boolean,
    default: false
  },
  loadingText: {
    type: String,
    default: '思考中...'
  }
})

const messagesContainer = ref(null)

function scrollToBottom() {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

// 监听消息变化，自动滚动到底部
watch(() => props.messages, async () => {
  await nextTick()
  scrollToBottom()
}, { deep: true })

watch(() => props.isLoading, async () => {
  await nextTick()
  scrollToBottom()
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
  line-height: 1.6;
  white-space: pre-wrap;
}

.message-content.loading {
  color: #999;
  font-style: italic;
}

.message-time {
  font-size: 11px;
  color: #999;
  margin-top: 4px;
  text-align: right;
}
</style>
