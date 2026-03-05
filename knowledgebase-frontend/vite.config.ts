import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

// https://vitejs.dev/config/
export default defineConfig(({ command, mode }) => {
  // 使用项目根目录加载 .env，避免从 workspace 根目录加载导致 .env.production 未生效
  const envDir = resolve(__dirname)
  const env = loadEnv(mode, envDir, '')
  const apiBase = env.VITE_API_BASE ?? ''
  const pythonBase = env.VITE_PYTHON_BASE ?? ''

  if (command === 'build') {
    console.log(`[Vite Build] VITE_API_BASE = ${apiBase || '(空，将使用相对路径 /api)'}`)
  }
  // devprod 模式：代理转发到生产后端；否则转发到本地
  const isDevProd = mode === 'devprod'
  const apiTarget = isDevProd ? 'https://www.yonghongjituan.com:6713' : 'http://localhost:5000'
  const pythonTarget = isDevProd ? 'https://www.yonghongjituan.com:4013' : 'http://localhost:8000'
  if (command === 'serve') {
    console.log(`[Vite] API 代理目标: ${apiTarget}${isDevProd ? ' (生产环境)' : ' (本地)'}`)
  }

  return {
    plugins: [vue()],
    envDir: envDir,
    // 生产环境部署在 /learning 子路径下
    base: command === 'build' ? '/learning/' : '/',
    resolve: {
      alias: {
        '@': resolve(__dirname, 'src')
      }
    },
    server: {
      port: 5173,
      proxy: {
        '/api': {
          target: apiTarget,
          changeOrigin: true,
          secure: false
        },
        '/uploads': {
          target: apiTarget,
          changeOrigin: true,
          secure: false
        },
        '/uploads_test': {
          target: apiTarget,
          changeOrigin: true,
          secure: false
        },
        '/python-api': {
          target: pythonTarget,
          changeOrigin: true,
          secure: false,
          rewrite: (path) => path.replace(/^\/python-api/, '')
        }
      }
    }
  }
})
