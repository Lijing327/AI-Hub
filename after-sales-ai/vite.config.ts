import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  // 部署在子路径（如 /cs/）时必须设置 base，否则 JS/CSS 请求到根路径导致白屏
  // 部署到根路径时可设置 VITE_BASE_PATH=/ 再构建
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
