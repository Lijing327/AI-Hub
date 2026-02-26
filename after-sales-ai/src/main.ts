import { createApp } from 'vue'
import App from './App.vue'
import router from './router'

const app = createApp(App)
// 开发环境显式启用 DevTools，确保 Chrome 插件能识别（避免子路径 /cs/ 等导致检测失败）
if (import.meta.env.DEV) {
  app.config.devtools = true
}
app.use(router)
app.mount('#app')
