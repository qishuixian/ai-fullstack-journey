<template>
  <aside class="sidebar">
    <div class="sidebar-header">
      <h2>文件管理</h2>
      <p>上传、查看并删除当前账号的 PDF 文件。</p>

      <el-upload
        :auto-upload="false"
        :show-file-list="false"
        accept=".pdf"
        :on-change="handleFileChange"
      >
        <el-button type="primary" :icon="UploadFilled" style="width: 100%">
          上传 PDF
        </el-button>
      </el-upload>

      <el-input
        v-model="searchQuery"
        placeholder="搜索文件名"
        :prefix-icon="Search"
        clearable
        class="search-input"
      />
    </div>

    <div class="file-list">
      <el-empty
        v-if="props.files.length === 0"
        description="还没有上传文件"
        :image-size="84"
      />

      <el-empty
        v-else-if="filteredFiles.length === 0"
        description="没有匹配的文件"
        :image-size="84"
      />

      <div v-else class="file-items">
        <div v-for="file in filteredFiles" :key="file.id" class="file-item">
          <div class="file-info">
            <div class="file-name">{{ file.filename }}</div>
            <div class="file-meta">
              <span>{{ formatSize(file.size) }}</span>
              <span>{{ formatTime(file.created_at) }}</span>
            </div>
          </div>

          <el-button
            circle
            type="danger"
            plain
            :icon="Delete"
            @click="handleDelete(file)"
          />
        </div>
      </div>
    </div>

    <div class="sidebar-footer">
      <el-button
        type="info"
        text
        :icon="SwitchButton"
        style="width: 100%"
        @click="$emit('logout')"
      >
        退出登录
      </el-button>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { ElLoading, ElMessage, ElMessageBox } from 'element-plus'
import { Delete, Search, SwitchButton, UploadFilled } from '@element-plus/icons-vue'
import type { UploadFile } from 'element-plus'

interface FileItem {
  id: string
  filename: string
  size: number
  created_at: string
}

const props = defineProps<{
  files: FileItem[]
  token: string
}>()

const emit = defineEmits(['files-updated', 'logout'])
const searchQuery = ref('')

const filteredFiles = computed(() => {
  if (!searchQuery.value.trim()) return props.files
  const keyword = searchQuery.value.toLowerCase()
  return props.files.filter(file => file.filename.toLowerCase().includes(keyword))
})

async function handleFileChange(uploadFile: UploadFile) {
  const file = uploadFile.raw
  if (!file) return

  if (!file.name.toLowerCase().endsWith('.pdf')) {
    ElMessage.error('只支持上传 PDF 文件')
    return
  }

  const maxSize = 10 * 1024 * 1024
  if (file.size > maxSize) {
    ElMessage.error('文件大小不能超过 10MB')
    return
  }

  const formData = new FormData()
  formData.append('file', file)
  let loadingInstance: ReturnType<typeof ElLoading.service> | null = null

  try {
    // 上传入口移动到左侧文件管理区，聊天输入区不再承担文件选择职责。
    loadingInstance = ElLoading.service({
      lock: true,
      text: 'PDF 上传处理中，请稍候...',
      background: 'rgba(255, 255, 255, 0.72)'
    })

    const res = await fetch('/api/upload', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${props.token}`
      },
      body: formData
    })

    const data = await res.json()
    if (!res.ok) {
      throw new Error(data.detail || '上传失败')
    }

    ElMessage.success(`上传成功，已写入 ${data.chunks} 个分片`)
    emit('files-updated')
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '上传失败')
  } finally {
    loadingInstance?.close()
  }
}

async function handleDelete(file: FileItem) {
  try {
    await ElMessageBox.confirm(
      `确认删除文件“${file.filename}”吗？删除后会同步移除 ChromaDB 中的向量数据。`,
      '删除文件',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const res = await fetch(`/api/files/${file.id}`, {
      method: 'DELETE',
      headers: {
        Authorization: `Bearer ${props.token}`
      }
    })

    const data = await res.json()
    if (!res.ok) {
      throw new Error(data.detail || '删除失败')
    }

    ElMessage.success('文件已删除')
    emit('files-updated')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error instanceof Error ? error.message : '删除失败')
    }
  }
}

function formatSize(size: number) {
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / 1024 / 1024).toFixed(1)} MB`
}

function formatTime(value: string) {
  return new Date(value).toLocaleString()
}
</script>

<style scoped>
.sidebar {
  width: 320px;
  background: #f5f7fa;
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
  height: 100vh;
}

.sidebar-header {
  padding: 18px 16px;
  border-bottom: 1px solid #e4e7ed;
}

.sidebar-header h2 {
  font-size: 18px;
  color: #303133;
}

.sidebar-header p {
  margin: 6px 0 14px;
  color: #606266;
  font-size: 13px;
  line-height: 1.5;
}

.search-input {
  margin-top: 12px;
}

.file-list {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.file-items {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px;
  background: #fff;
  border-radius: 10px;
  border: 1px solid #ebeef5;
}

.file-info {
  flex: 1;
  min-width: 0;
}

.file-name {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  word-break: break-all;
}

.file-meta {
  margin-top: 6px;
  display: flex;
  justify-content: space-between;
  gap: 8px;
  color: #909399;
  font-size: 12px;
}

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid #e4e7ed;
}
</style>
