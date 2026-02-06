<template>
  <el-container class="app-container">
    <el-header class="app-header">
      <div class="header-content">
        <h1>知识库录入与管理系统</h1>
        <div class="header-nav">
          <el-button
            :type="currentRoute === '/knowledge' ? 'primary' : 'default'"
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

// 当前路径（用于高亮，兼容子路径如 /audit/conversation/1）
const currentRoute = computed(() => {
  const path = route.path
  if (path.startsWith('/audit/stats')) return '/audit/stats'
  if (path.startsWith('/audit')) return '/audit'
  if (path.startsWith('/knowledge')) return '/knowledge'
  return path
})

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

.app-main {
  padding: 20px;
  background-color: #f5f5f5;
}
</style>
