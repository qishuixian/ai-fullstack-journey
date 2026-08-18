<template>
  <div class="app-container">
    <LoginForm v-if="!isLoggedIn" @login-success="handleLoginSuccess" />

    <div v-else class="app-layout">
      <Sidebar
        :files="files"
        :token="getToken()"
        @files-updated="loadFiles"
        @logout="handleLogout"
      />

      <ChatArea
        ref="chatAreaRef"
        :token="getToken()"
      />
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import ChatArea from './components/ChatArea.vue'
import LoginForm from './components/LoginForm.vue'
import Sidebar from './components/Sidebar.vue'

const isLoggedIn = ref(false)
const files = ref([])
const chatAreaRef = ref(null)

function getToken() {
  return localStorage.getItem('token') || ''
}

async function loadFiles() {
  const token = getToken()
  if (!token) return

  try {
    const res = await fetch('/api/files', {
      headers: { Authorization: `Bearer ${token}` }
    })
    if (res.ok) {
      files.value = await res.json()
    } else if (res.status === 401) {
      handleLogout()
    }
  } catch (error) {
    console.warn('加载文件列表失败:', error)
  }
}

function checkAuth() {
  isLoggedIn.value = !!getToken()
  if (isLoggedIn.value) {
    loadFiles()
  }
}

function handleLoginSuccess() {
  isLoggedIn.value = true
  loadFiles()
  chatAreaRef.value?.loadHistory()
}

function handleLogout() {
  localStorage.removeItem('token')
  isLoggedIn.value = false
  files.value = []
  chatAreaRef.value?.clearMessages()
}

onMounted(() => {
  checkAuth()
})
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: #f0f2f5;
  height: 100vh;
}

.app-container {
  height: 100vh;
}

.app-layout {
  display: flex;
  height: 100vh;
}
</style>
