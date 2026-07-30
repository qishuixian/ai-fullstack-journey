<template>
  <footer class="chat-input">
    <el-upload
      ref="uploadRef"
      :auto-upload="false"
      :show-file-list="false"
      :on-change="handleFileChange"
      accept=".txt,.pdf,.doc,.docx,.jpg,.jpeg,.png,.gif"
    >
      <el-button :icon="Paperclip" circle title="上传文件" />
    </el-upload>

    <el-input
      v-model="inputValue"
      type="textarea"
      :rows="1"
      :autosize="{ minRows: 1, maxRows: 4 }"
      placeholder="输入消息，按 Ctrl+Enter 发送"
      :disabled="isLoading"
      @keydown.ctrl.enter="handleSend"
      @keydown.meta.enter="handleSend"
    />

    <el-button
      v-if="!isLoading"
      type="primary"
      :icon="Promotion"
      @click="handleSend"
      :disabled="!inputValue.trim()"
      circle
      title="发送"
    />

    <el-button
      v-else
      type="danger"
      :icon="CircleClose"
      @click="$emit('stop')"
      circle
      title="停止生成"
    />
  </footer>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Paperclip, Promotion, CircleClose } from '@element-plus/icons-vue'
import type { UploadFile } from 'element-plus'

const props = defineProps<{
  modelValue: string
  isLoading: boolean
}>()

const emit = defineEmits(['update:modelValue', 'send', 'stop', 'file-upload'])

const inputValue = ref(props.modelValue)
const uploadRef = ref()

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

function handleFileChange(uploadFile: UploadFile) {
  const file = uploadFile.raw
  if (!file) return

  // 检查文件大小（10MB）
  const maxSize = 10 * 1024 * 1024
  if (file.size > maxSize) {
    ElMessage.error('文件大小不能超过 10MB')
    return
  }

  // 发送文件上传事件
  emit('file-upload', file)

  // 清空上传组件
  if (uploadRef.value) {
    uploadRef.value.clearFiles()
  }
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
