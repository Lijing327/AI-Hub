<template>
  <span class="status-tag" :class="displayStatus">
    {{ displayStatus }}
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'

// 支持中文字符串或英文状态，统一转为中文显示
type StatusCn = '待处理' | '处理中' | '已解决' | '已关闭'
interface Props {
  status: string
}

const props = defineProps<Props>()

const statusMap: Record<string, StatusCn> = {
  pending: '待处理',
  processing: '处理中',
  resolved: '已解决',
  closed: '已关闭',
  待处理: '待处理',
  处理中: '处理中',
  已解决: '已解决',
  已关闭: '已关闭'
}

const displayStatus = computed<StatusCn>(() => statusMap[props.status] || '待处理')
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
