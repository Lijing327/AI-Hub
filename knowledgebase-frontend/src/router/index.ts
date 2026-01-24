import { createRouter, createWebHistory } from 'vue-router'
import KnowledgeList from '../views/KnowledgeList.vue'
import KnowledgeEdit from '../views/KnowledgeEdit.vue'
import KnowledgeDetail from '../views/KnowledgeDetail.vue'

const router = createRouter({
  history: createWebHistory(),
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
    }
  ]
})

export default router
