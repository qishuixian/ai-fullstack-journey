import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

export const useThemeStore = defineStore('theme', () => {
  // 从 localStorage 读取主题，默认为浅色
  const theme = ref<'light' | 'dark'>(
    (localStorage.getItem('theme') as 'light' | 'dark') || 'light'
  )

  // 切换主题
  function toggleTheme() {
    theme.value = theme.value === 'light' ? 'dark' : 'light'
  }

  // 设置主题
  function setTheme(newTheme: 'light' | 'dark') {
    theme.value = newTheme
  }

  // 监听主题变化，应用到 DOM 并保存到 localStorage
  watch(theme, (newTheme) => {
    // 应用到 document
    if (newTheme === 'dark') {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }

    // 保存到 localStorage
    localStorage.setItem('theme', newTheme)
  }, { immediate: true })

  return {
    theme,
    toggleTheme,
    setTheme
  }
})
