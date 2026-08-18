<template>
  <footer class="chat-input">
    <el-input
      v-model="inputValue"
      type="textarea"
      :rows="1"
      :autosize="{ minRows: 1, maxRows: 4 }"
      placeholder="输入问题，默认检索当前账号下的全部 PDF 文件"
      :disabled="isLoading"
      @keydown.ctrl.enter="handleSend"
      @keydown.meta.enter="handleSend"
    />

    <el-button
      v-if="!isLoading"
      type="primary"
      :icon="Promotion"
      :disabled="!inputValue.trim()"
      circle
      title="发送"
      @click="handleSend"
    />

    <el-button
      v-else
      type="danger"
      :icon="CircleClose"
      circle
      title="停止生成"
      @click="$emit('stop')"
    />
  </footer>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { CircleClose, Promotion } from '@element-plus/icons-vue'

const props = defineProps<{
  modelValue: string
  isLoading: boolean
}>()

const emit = defineEmits(['update:modelValue', 'send', 'stop'])

const inputValue = ref(props.modelValue)

watch(() => props.modelValue, (newVal) => {
  inputValue.value = newVal
})

watch(inputValue, (newVal) => {
  emit('update:modelValue', newVal)
})

function handleSend() {
  if (!inputValue.value.trim() || props.isLoading) return
  emit('send', inputValue.value)
  inputValue.value = ''
}
</script>

<style scoped>
.chat-input {
  display: flex;
  align-items: flex-end;
  padding: 16px;
  gap: 12px;
  border-top: 1px solid var(--border-color);
  background: var(--bg-primary);
}

.chat-input :deep(.el-textarea__inner) {
  resize: none;
  padding: 10px 14px;
  font-size: 14px;
  line-height: 1.5;
}

.chat-input :deep(.el-button.is-circle) {
  flex-shrink: 0;
}
</style>
