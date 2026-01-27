<template>
  <span class="status-tag" :class="status">
    {{ status }}
  </span>
</template>

<script setup lang="ts">
import { defineProps } from 'vue'

interface Props {
  status: '待处理' | '处理中' | '已解决' | '已关闭'
}

defineProps<Props>()
</script>

<style scoped>
.status-tag {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.status-tag.待处理 {
  background: #fff3cd;
  color: #856404;
}

.status-tag.处理中 {
  background: #cfe2ff;
  color: #084298;
}

.status-tag.已解决 {
  background: #d1e7dd;
  color: #0f5132;
}

.status-tag.已关闭 {
  background: #f8d7da;
  color: #842029;
}
</style>
