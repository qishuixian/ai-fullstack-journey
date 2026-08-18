import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'


export default defineConfig(({ mode }) => {
  // 加载当前模式下的环境变量
  const env = loadEnv(mode, process.cwd(), '')

  return {
    plugins: [vue()],
    base: env.VITE_BASE_URL || '/',  // 默认为 '/'
    server: {
      port: 5173,
      proxy: {
        '/api': {
          target: 'http://127.0.0.1:8001',
          changeOrigin: true,
          rewrite: (path: string): string => path.replace(/^\/api/, '')
        }
      }
    },
    test: {
      environment: 'jsdom',
      globals: true
    }
  }
})