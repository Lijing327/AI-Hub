/**
 * 路由配置
 */

import { createRouter, createWebHistory } from 'vue-router'
import { initIfNeeded } from '@/store/storage'
import Home from '@/views/Home.vue'
import Chat from '@/views/Chat.vue'
import History from '@/views/History.vue'
import SessionDetail from '@/views/SessionDetail.vue'
import Tickets from '@/views/Tickets.vue'
import TicketDetail from '@/views/TicketDetail.vue'
import Admin from '@/views/Admin.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/chat',
    name: 'Chat',
    component: Chat
  },
  {
    path: '/history',
    name: 'History',
    component: History
  },
  {
    path: '/session/:id',
    name: 'SessionDetail',
    component: SessionDetail
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
  history: createWebHistory(),
  routes
})

// 路由守卫：确保数据初始化完成
let initPromise: Promise<void> | null = null

router.beforeEach(async (to, from, next) => {
  // 确保只初始化一次
  if (!initPromise) {
    initPromise = initIfNeeded()
  }
  await initPromise
  next()
})

export default router
