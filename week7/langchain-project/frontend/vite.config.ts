import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')

  return {
    plugins: [vue()],
    base: env.VITE_BASE_URL || '/',
    server: {
      port: 8082,
      proxy: {
        '/api': {
          target: env.VITE_API_PROXY_TARGET || 'http://127.0.0.1:8002',
          changeOrigin: true,
          rewrite: (path: string): string => path.replace(/^\/api/, '')
        }
      }
    }
  }
})
