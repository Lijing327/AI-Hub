<template>
  <router-view />
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { initIfNeeded } from '@/store/storage'

onMounted(async () => {
  // 初始化存储
  await initIfNeeded()
})
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
  -webkit-tap-highlight-color: transparent; /* 移除移动端点击高亮 */
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  background: #f5f5f5;
  /* 移动端优化 */
  -webkit-text-size-adjust: 100%;
  touch-action: manipulation; /* 优化触摸响应 */
}

#app {
  min-height: 100vh;
  /* 移动端安全区域适配 */
  padding-bottom: env(safe-area-inset-bottom);
}

/* 移动端按钮优化 */
button {
  -webkit-appearance: none;
  appearance: none;
  touch-action: manipulation;
  user-select: none;
}

/* 输入框优化 */
input, textarea {
  -webkit-appearance: none;
  appearance: none;
  font-size: 16px; /* 防止 iOS 自动缩放 */
}

/* 滚动优化 */
* {
  -webkit-overflow-scrolling: touch;
}

/* 选择文本优化 */
::selection {
  background: rgba(24, 160, 88, 0.2);
}
</style>
