/**
 * 构建前将 .env.production 加载到 process.env 并启动 vite build，
 * 确保 Vite 能正确读取 VITE_API_BASE（解决 workspace 下 cwd 导致 .env 未加载的问题）
 */
import fs from 'fs'
import path from 'path'
import { spawnSync } from 'child_process'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

const envPath = path.join(__dirname, '..', '.env.production')
if (fs.existsSync(envPath)) {
  const content = fs.readFileSync(envPath, 'utf8')
  content.split(/\r?\n/).forEach((line) => {
    const m = line.match(/^([^=]+)=(.*)$/)
    if (m && m[1].startsWith('VITE_')) {
      process.env[m[1].trim()] = m[2].trim()
    }
  })
  console.log('[load-env] 已加载 .env.production, VITE_API_BASE =', process.env.VITE_API_BASE || '(空)')
}

const cwd = path.join(__dirname, '..')
const result = spawnSync('npx', ['vite', 'build'], {
  stdio: 'inherit',
  env: process.env,
  cwd,
  shell: true
})
if (result.error) {
  console.error('[load-env] vite build 失败:', result.error)
  process.exit(1)
}
process.exit(result.status ?? 1)
