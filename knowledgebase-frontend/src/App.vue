<template>
  <el-container class="app-container">
    <el-header class="app-header">
      <div class="header-content">
        <h1>智能问答管理平台</h1>
        <div class="header-nav">
          <span class="nav-group-label">知识库录入与管理系统</span>
          <el-button
            :type="isKnowledgeActive ? 'primary' : 'default'"
            link
            class="nav-btn"
            @click="goTo('/knowledge')"
          >
            知识条目列表
          </el-button>
          <el-button
            :type="currentRoute === '/audit' ? 'primary' : 'default'"
            link
            class="nav-btn"
            @click="goTo('/audit')"
          >
            AI 对话审计
          </el-button>
          <el-button
            :type="currentRoute === '/audit/stats' ? 'primary' : 'default'"
            link
            class="nav-btn"
            @click="goTo('/audit/stats')"
          >
            AI 统计报表
          </el-button>
          <el-divider direction="vertical" />
          <span class="nav-group-label">工单管理系统</span>
          <el-button
            :type="isTicketsActive ? 'primary' : 'default'"
            link
            class="nav-btn"
            @click="goTo('/tickets')"
          >
            工单列表
          </el-button>
        </div>
      </div>
    </el-header>
    <el-main class="app-main">
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()

// 当前路径（用于高亮，兼容子路径）
const currentRoute = computed(() => {
  const path = route.path
  if (path.startsWith('/audit/stats')) return '/audit/stats'
  if (path.startsWith('/audit')) return '/audit'
  if (path.startsWith('/knowledge')) return '/knowledge'
  if (path.startsWith('/tickets')) return '/tickets'
  return path
})

const isKnowledgeActive = computed(() =>
  currentRoute.value === '/knowledge' || currentRoute.value === '/audit' || currentRoute.value === '/audit/stats'
)
const isTicketsActive = computed(() => currentRoute.value === '/tickets')

const goTo = (path: string) => {
  router.push(path)
}
</script>

<style scoped>
.app-container {
  height: 100vh;
}

.app-header {
  background-color: #409eff;
  color: white;
  display: flex;
  align-items: center;
  padding: 0 20px;
}

.header-content {
  display: flex;
  align-items: center;
  gap: 24px;
  width: 100%;
}

.header-content h1 {
  margin: 0;
  font-size: 20px;
  white-space: nowrap;
}

.header-nav {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-nav .nav-btn {
  color: rgba(255, 255, 255, 0.9);
}

.header-nav .nav-btn:hover {
  color: #fff;
}

.header-nav .el-button.is-link.el-button--primary {
  color: #fff;
  font-weight: 600;
}

.nav-group-label {
  font-size: 12px;
  opacity: 0.85;
  margin-right: 4px;
}

.header-nav .el-divider--vertical {
  height: 20px;
  margin: 0 8px;
  border-color: rgba(255, 255, 255, 0.5);
}

.app-main {
  padding: 20px;
  background-color: #f5f5f5;
}
</style>
