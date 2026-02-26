import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  // 客服部署在 /cs/ 子路径，访问地址为 https://域名:4013/cs/#/
  base: process.env.VITE_BASE_PATH || '/cs/',
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  server: {
    port: 3000,
    host: '0.0.0.0', // 允许通过局域网 IP 访问
    open: true,
    // 仅开发环境生效：代理到本机 .NET / Python，生产环境用 .env.production 里的完整地址
    proxy: {
      '/api': {
        target: process.env.VITE_DEV_API_TARGET || 'http://localhost:5000',
        changeOrigin: true,
        secure: false
      },
      '/uploads': {
        target: process.env.VITE_DEV_API_TARGET || 'http://localhost:5000',
        changeOrigin: true,
        secure: false
      },
      '/python-api': {
        target: process.env.VITE_DEV_PYTHON_TARGET || 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path.replace(/^\/python-api/, '')
      }
    }
  }
})
