<template>
  <div class="session-detail-page">
    <div class="header">
      <button class="btn-back" @click="goBack">←</button>
      <h2>会话详情</h2>
      <div></div>
    </div>

    <div class="session-info-bar">
      <div class="info-item">
        <span class="label">设备：</span>
        <span class="value">{{ device?.model }} ({{ device?.serialNo }})</span>
      </div>
      <div class="info-item">
        <span class="label">时间：</span>
        <span class="value">{{ formatTime(session?.startTime || '') }}</span>
      </div>
      <div class="info-item" v-if="session?.issueCategory">
        <span class="label">问题：</span>
        <span class="value">{{ session.issueCategory }} <span v-if="session.alarmCode">{{ session.alarmCode }}</span></span>
      </div>
    </div>

    <div class="messages-container">
      <div v-for="message in messages" :key="message.messageId" class="message-wrapper">
        <ChatMessageBubble :message="message" />
        <AiAnswerCard
          v-if="message.role === 'assistant' && shouldShowAnswerCard(message.messageId)"
          :meta="getAIMeta(message.messageId)!"
          :solution="getSolution(message.messageId)"
          :readonly="true"
        />
        <div
          v-if="message.role === 'assistant' && getAIMeta(message.messageId)?.replyMode === 'handoff'"
          class="handoff-card"
        >
          <div class="handoff-title">转人工客服</div>
          <a class="handoff-phone" href="tel:0312-7027666">📞 人工客服电话：0312-7027666</a>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ChatMessageBubble from '@/components/ChatMessageBubble.vue'
import AiAnswerCard from '@/components/AiAnswerCard.vue'
import { sessionRepo, messageRepo, aiMetaRepo, deviceRepo } from '@/store/repositories'
import type { ChatSession, ChatMessage, Device, AIResponseMeta } from '@/models/types'

const route = useRoute()
const router = useRouter()

const session = ref<ChatSession | null>(null)
const device = ref<Device | null>(null)
const messages = ref<ChatMessage[]>([])
const aiMetas = ref<AIResponseMeta[]>([])

onMounted(() => {
  const sessionId = route.params.id as string
  session.value = sessionRepo.getById(sessionId)
  
  if (!session.value) {
    router.push('/history')
    return
  }

  device.value = deviceRepo.getById(session.value.deviceId)
  messages.value = messageRepo.getBySessionId(sessionId)
  aiMetas.value = aiMetaRepo.getBySessionId(sessionId)
})

function getAIMeta(messageId: string): AIResponseMeta | null {
  return aiMetas.value.find((m) => m.relatedMessageId === messageId) || null
}

function shouldShowAnswerCard(messageId: string): boolean {
  const meta = getAIMeta(messageId)
  return meta != null && meta.replyMode !== 'conversation' && meta.replyMode !== 'handoff'
}

function getSolution(messageId: string): { temporary: string; final: string } {
  const meta = getAIMeta(messageId)
  if (!meta || !meta.solution) return { temporary: '', final: '' }
  return meta.solution
}

function formatTime(timeStr: string): string {
  const date = new Date(timeStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function goBack() {
  router.push('/history')
}
</script>

<style scoped>
.session-detail-page {
  min-height: 100vh;
  background: #f5f5f5;
  display: flex;
  flex-direction: column;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.btn-back {
  padding: 8px;
  background: none;
  border: none;
  font-size: 18px;
  color: #333;
  cursor: pointer;
}

.header h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.session-info-bar {
  padding: 12px 16px;
  background: #fff;
  border-bottom: 1px solid #e0e0e0;
}

.info-item {
  font-size: 13px;
  margin-bottom: 6px;
}

.info-item:last-child {
  margin-bottom: 0;
}

.label {
  color: #666;
}

.value {
  color: #333;
  font-weight: 500;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  -webkit-overflow-scrolling: touch;
}

.message-wrapper {
  margin-bottom: 16px;
}

.handoff-card {
  margin-top: 8px;
  padding: 12px 16px;
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  border-radius: 12px;
  border-left: 4px solid #0ea5e9;
}

.handoff-title {
  font-size: 14px;
  font-weight: 600;
  color: #0c4a6e;
  margin-bottom: 8px;
}

.handoff-phone {
  display: inline-block;
  font-size: 14px;
  font-weight: 600;
  color: #0369a1;
  text-decoration: none;
}
</style>
