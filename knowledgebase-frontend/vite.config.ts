import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

// https://vitejs.dev/config/
export default defineConfig(({ command, mode }) => {
  // 构建时打印 API 配置，便于排查部署后请求地址错误
  const env = loadEnv(mode, process.cwd(), '')
  if (command === 'build') {
    const apiBase = env.VITE_API_BASE ?? '(空，将使用相对路径 /api)'
    console.log(`[Vite Build] VITE_API_BASE = ${apiBase}`)
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
