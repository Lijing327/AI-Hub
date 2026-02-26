/**
 * 路由配置
 */

import { createRouter, createWebHashHistory } from 'vue-router'
import { initIfNeeded } from '@/store/storage'
import Welcome from '@/views/Welcome.vue'
import Home from '@/views/Home.vue'
import Chat from '@/views/Chat.vue'
import History from '@/views/History.vue'
import SessionDetail from '@/views/SessionDetail.vue'
import Tickets from '@/views/Tickets.vue'
import TicketDetail from '@/views/TicketDetail.vue'
import Admin from '@/views/Admin.vue'
import Login from '@/views/Login.vue'
import Register from '@/views/Register.vue'

const routes = [
  {
    path: '/',
    name: 'Welcome',
    component: Welcome
  },
  {
    path: '/home',
    name: 'Home',
    component: Home
  },
  {
    path: '/login',
    name: 'Login',
    component: Login
  },
  {
    path: '/register',
    name: 'Register',
    component: Register
  },
  {
    path: '/chat',
    name: 'Chat',
    component: Chat,
    meta: { requiresAuth: true }
  },
  {
    path: '/history',
    name: 'History',
    component: History,
    meta: { requiresAuth: true }
  },
  {
    path: '/session/:id',
    name: 'SessionDetail',
    component: SessionDetail,
    meta: { requiresAuth: true }
  },
  {
    path: '/tickets',
    name: 'Tickets',
    component: Tickets
  },
  {
    path: '/ticket/:id',
    name: 'TicketDetail',
    component: TicketDetail
  },
  {
    path: '/admin',
    name: 'Admin',
    component: Admin
  }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

// 路由守卫：确保数据初始化完成
let initPromise: Promise<void> | null = null

router.beforeEach(async (to, _from, next) => {
  // 确保只初始化一次
  if (!initPromise) {
    initPromise = initIfNeeded()
  }
  await initPromise

  // 检查是否需要认证
  if (to.meta.requiresAuth) {
    const token = localStorage.getItem('token')
    if (!token) {
      // 未登录，重定向到登录页，并携带当前路由作为redirect参数
      next({
        path: '/login',
        query: { redirect: to.fullPath }
      })
      return
    }

    // 可以在这里添加token验证逻辑
    // 例如调用 /api/auth/me 验证token是否有效
  }

  next()
})

export default router
