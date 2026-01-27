<template>
  <div class="message-bubble" :class="message.role">
    <div class="message-content">
      <div class="message-text">{{ message.content }}</div>
      <div class="message-time">{{ formatTime(message.createdAt) }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { defineProps } from 'vue'
import type { ChatMessage } from '@/models/types'

interface Props {
  message: ChatMessage
}

defineProps<Props>()

function formatTime(timeStr: string): string {
  const date = new Date(timeStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / 60000)

  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (minutes < 1440) return `${Math.floor(minutes / 60)}小时前`

  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>

<style scoped>
.message-bubble {
  display: flex;
  margin-bottom: 16px;
  animation: fadeIn 0.3s;
}

.message-bubble.user {
  justify-content: flex-end;
}

.message-bubble.assistant {
  justify-content: flex-start;
}

.message-content {
  max-width: 75%;
  padding: 12px 16px;
  border-radius: 12px;
  word-wrap: break-word;
}

.message-bubble.user .message-content {
  background: #18a058;
  color: #fff;
  border-bottom-right-radius: 4px;
}

.message-bubble.assistant .message-content {
  background: #f5f5f5;
  color: #333;
  border-bottom-left-radius: 4px;
}

.message-text {
  font-size: 15px;
  line-height: 1.5;
  margin-bottom: 4px;
}

.message-time {
  font-size: 11px;
  opacity: 0.7;
  text-align: right;
}

.message-bubble.assistant .message-time {
  text-align: left;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
