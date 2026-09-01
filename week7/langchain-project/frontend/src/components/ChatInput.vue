<template>
  <footer class="chat-input">
    <el-input
      v-model="inputValue"
      type="textarea"
      :rows="1"
      :autosize="{ minRows: 1, maxRows: 5 }"
      placeholder="输入你的问题，按 Ctrl + Enter 发送"
      :disabled="isLoading"
      @keydown.ctrl.enter="handleSend"
      @keydown.meta.enter="handleSend"
    />

    <el-button
      v-if="!isLoading"
      type="primary"
      class="send-btn"
      :disabled="!inputValue.trim()"
      @click="handleSend"
    >
      发送
    </el-button>

    <el-button
      v-else
      type="danger"
      class="send-btn"
      @click="$emit('stop')"
    >
      停止
    </el-button>
  </footer>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

const props = defineProps<{
  modelValue: string
  isLoading: boolean
}>()

const emit = defineEmits(['update:modelValue', 'send', 'stop'])
const inputValue = ref(props.modelValue)

watch(
  () => props.modelValue,
  (newValue) => {
    inputValue.value = newValue
  }
)

watch(inputValue, (newValue) => {
  emit('update:modelValue', newValue)
})

function handleSend() {
  if (!inputValue.value.trim() || props.isLoading) {
    return
  }

  emit('send', inputValue.value.trim())
  inputValue.value = ''
}
</script>

<style scoped>
.chat-input {
  display: flex;
  gap: 14px;
  padding: 18px 20px 22px;
  border-top: 1px solid var(--border-color);
  background: rgba(255, 255, 255, 0.88);
}

.send-btn {
  align-self: flex-end;
  min-width: 88px;
  height: 42px;
}
</style>
