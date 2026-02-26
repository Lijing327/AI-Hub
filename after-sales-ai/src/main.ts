import { createApp } from 'vue'
import App from './App.vue'
import router from './router'

const app = createApp(App)
// Vue 3.4+ 已不再支持 app.config.devtools，改用 Vite 配置或浏览器插件控制
app.use(router)
app.mount('#app')
