<template>
  <el-container class="app-container">
    <el-header class="app-header">
      <div class="header-content">
        <h1>知识库录入与管理系统</h1>
      </div>
    </el-header>
    <el-main class="app-main">
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
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

.header-content h1 {
  margin: 0;
  font-size: 20px;
}

.app-main {
  padding: 20px;
  background-color: #f5f5f5;
}
</style>
