<template>
  <footer class="chat-input">
    <input
      v-model="inputValue"
      placeholder="输入消息，按 Enter 发送"
      @keyup.enter="handleSend"
      :disabled="isLoading"
    />
    <button @click="handleSend" :disabled="isLoading || !inputValue.trim()">
      {{ isLoading ? '思考中...' : '发送' }}
    </button>
    <button v-if="isLoading" @click="$emit('stop')">停止</button>
  </footer>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  isLoading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'send', 'stop'])

const inputValue = ref(props.modelValue)

watch(() => props.modelValue, (newVal) => {
  inputValue.value = newVal
})

watch(inputValue, (newVal) => {
  emit('update:modelValue', newVal)
})

function handleSend() {
  if (inputValue.value.trim() && !props.isLoading) {
    emit('send', inputValue.value)
    inputValue.value = ''
  }
}
</script>

<style scoped>
.chat-input {
  display: flex;
  padding: 12px 16px;
  border-top: 1px solid #e0e0e0;
  gap: 8px;
}

.chat-input input {
  flex: 1;
  padding: 10px 14px;
  border: 1px solid #d0d0d0;
  border-radius: 8px;
  font-size: 14px;
  outline: none;
}

.chat-input input:focus {
  border-color: #1a73e8;
}

.chat-input button {
  padding: 10px 20px;
  background: #1a73e8;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
}

.chat-input button:hover:not(:disabled) {
  background: #1557b0;
}

.chat-input button:disabled {
  background: #ccc;
  cursor: not-allowed;
}
</style>
