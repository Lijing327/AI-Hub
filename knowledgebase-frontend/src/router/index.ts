import { createRouter, createWebHashHistory } from 'vue-router'
import KnowledgeList from '../views/KnowledgeList.vue'
import KnowledgeEdit from '../views/KnowledgeEdit.vue'
import KnowledgeDetail from '../views/KnowledgeDetail.vue'
import ConversationList from '../views/ConversationList.vue'
import ConversationDetail from '../views/ConversationDetail.vue'
import AuditStats from '../views/AuditStats.vue'
import TicketList from '../views/TicketList.vue'
import TicketDetail from '../views/TicketDetail.vue'

const router = createRouter({
  // 使用 hash 模式，避免服务器配置问题
  history: createWebHashHistory(),
  routes: [
    {
      path: '/',
      redirect: '/knowledge'
    },
    {
      path: '/knowledge',
      name: 'KnowledgeList',
      component: KnowledgeList
    },
    {
      path: '/knowledge/create',
      name: 'KnowledgeCreate',
      component: KnowledgeEdit
    },
    {
      path: '/knowledge/edit/:id',
      name: 'KnowledgeEdit',
      component: KnowledgeEdit,
      props: true
    },
    {
      path: '/knowledge/detail/:id',
      name: 'KnowledgeDetail',
      component: KnowledgeDetail,
      props: true
    },
    // AI 审计
    {
      path: '/audit',
      name: 'ConversationList',
      component: ConversationList
    },
    {
      path: '/audit/conversation/:id',
      name: 'ConversationDetail',
      component: ConversationDetail,
      props: true
    },
    {
      path: '/audit/stats',
      name: 'AuditStats',
      component: AuditStats
    },
    // 工单管理
    {
      path: '/tickets',
      name: 'TicketList',
      component: TicketList
    },
    {
      path: '/tickets/:id',
      name: 'TicketDetail',
      component: TicketDetail,
      props: true
    }
  ]
})

export default router
