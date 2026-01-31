<template>
  <div class="chat-page">
    <!-- 顶部栏 -->
    <div class="chat-header">
      <button class="btn-back" @click="goBack">←</button>
      <div class="device-info" @click="showDevicePicker = true">
        <div class="device-model">{{ device?.model }}</div>
        <div class="device-serial">SN: {{ device?.serialNo }}</div>
      </div>
      <button class="btn-history" @click="goToHistory">历史</button>
    </div>

    <!-- 聊天区 -->
    <div class="chat-messages" ref="messagesContainer">
      <div v-for="message in messages" :key="message.messageId" class="message-wrapper">
        <ChatMessageBubble :message="message" />
        <!-- 仅在有结构化回复时展示故障排查卡片；conversation 模式（如「你是谁」）只展示对话气泡 -->
        <AiAnswerCard
          v-if="message.role === 'assistant' && shouldShowAnswerCard(message.messageId)"
          :meta="getAIMeta(message.messageId)!"
          :solution="getSolution(message.messageId)"
          :related-articles="getRelatedArticles(message.messageId)"
          :readonly="false"
          @create-ticket="handleCreateTicket(message.messageId)"
          @feedback="handleFeedback(message.messageId, $event)"
          @select-related-question="handleSelectRelatedQuestion"
        />
      </div>
      <!-- 加载状态 -->
      <div v-if="isLoading" class="loading-indicator">
        <div class="loading-dots">
          <span></span>
          <span></span>
          <span></span>
        </div>
        <span class="loading-text">AI 正在思考中...</span>
      </div>
      <!-- 错误提示 -->
      <div v-if="errorMessage" class="error-message">
        {{ errorMessage }}
      </div>
    </div>

    <!-- 底部输入区 -->
    <div class="chat-input-area">
      <!-- 快捷问题已移除，不再显示模拟数据 -->
      <div class="input-row">
        <input
          v-model="inputText"
          type="text"
          class="input-field"
          placeholder="输入您的问题..."
          @keyup.enter="sendMessage"
        />
        <button class="btn-send" @click="sendMessage" :disabled="!inputText.trim() || isLoading">
          {{ isLoading ? '发送中...' : '发送' }}
        </button>
      </div>
    </div>

    <!-- 设备选择弹窗 -->
    <div v-if="showDevicePicker" class="device-picker-modal" @click.self="showDevicePicker = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>选择设备</h3>
          <button class="btn-close" @click="showDevicePicker = false">×</button>
        </div>
        <DevicePicker
          :devices="allDevices"
          :selected-device-id="currentDeviceId"
          @select="handleDeviceChange"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ChatMessageBubble from '@/components/ChatMessageBubble.vue'
import AiAnswerCard from '@/components/AiAnswerCard.vue'
// import QuickQuestions from '@/components/QuickQuestions.vue' // 已移除快捷问题显示
import DevicePicker from '@/components/DevicePicker.vue'
import { sessionRepo, messageRepo, aiMetaRepo, ticketRepo, ticketLogRepo, deviceRepo, feedbackRepo } from '@/store/repositories'
import { generateAIResponse } from '@/ai/ai_service'
import type { ChatSession, ChatMessage, Device, AIResponseMeta, Ticket, TicketLog, RelatedArticle } from '@/models/types'
// import demoQuestionsData from '@/mock/demo_questions.json' // 已移除演示问题

const route = useRoute()
const router = useRouter()

const currentDeviceId = ref<string>('')
const currentCustomerId = ref<string>('')
const currentSessionId = ref<string>('')
const device = ref<Device | null>(null)
const allDevices = ref<Device[]>([])
const messages = ref<ChatMessage[]>([])
const aiMetas = ref<AIResponseMeta[]>([])
// const demoQuestions = ref(demoQuestionsData) // 已移除演示问题
const inputText = ref('')
const showDevicePicker = ref(false)
const messagesContainer = ref<HTMLElement | null>(null)
const isLoading = ref(false)
const errorMessage = ref<string | null>(null)

// 审计相关：后端返回的会话 ID（用于后续消息关联）
const backendConversationId = ref<string | null>(null)

// 会话存储 key
const CONVERSATION_ID_KEY = 'ai_conversation_id'

// 获取 AI 元数据
function getAIMeta(messageId: string): AIResponseMeta | null {
  return aiMetas.value.find((m) => m.relatedMessageId === messageId) || null
}

// 是否展示故障排查卡片：有 AI 元数据且非「仅对话」模式时展示
function shouldShowAnswerCard(messageId: string): boolean {
  const meta = getAIMeta(messageId)
  return meta != null && meta.replyMode !== 'conversation'
}

// 获取解决方案（从 AI 响应中提取）
function getSolution(messageId: string): { temporary: string; final: string } {
  const meta = getAIMeta(messageId)
  if (!meta || !meta.solution) return { temporary: '', final: '' }
  return meta.solution
}

// 获取相关文章
function getRelatedArticles(messageId: string): RelatedArticle[] | undefined {
  const meta = getAIMeta(messageId)
  return meta?.relatedArticles
}

onMounted(async () => {
  // 初始化设备
  allDevices.value = deviceRepo.getAll()
  const deviceId = route.query.deviceId as string
  const customerId = route.query.customerId as string

  if (!deviceId) {
    router.push('/')
    return
  }

  currentDeviceId.value = deviceId
  currentCustomerId.value = customerId || ''
  device.value = deviceRepo.getById(deviceId)

  if (!device.value) {
    router.push('/')
    return
  }

  // 恢复后端会话 ID（页面刷新时保持会话连续性）
  const savedConversationId = sessionStorage.getItem(CONVERSATION_ID_KEY)
  if (savedConversationId) {
    backendConversationId.value = savedConversationId
    console.log('恢复后端会话 ID:', savedConversationId)
  }

  // 创建或获取会话
  const sessionId = route.query.sessionId as string
  if (sessionId) {
    const session = sessionRepo.getById(sessionId)
    if (session) {
      currentSessionId.value = sessionId
      loadMessages()
    } else {
      createNewSession()
    }
  } else {
    createNewSession()
  }
})

function createNewSession() {
  const newSession = sessionRepo.create({
    customerId: currentCustomerId.value,
    deviceId: currentDeviceId.value,
    channel: 'H5',
    startTime: new Date().toISOString(),
    resolvedStatus: '未反馈',
    escalatedToTicket: false
  })
  currentSessionId.value = newSession.sessionId
  
  // 清除旧的后端会话 ID（新会话开始）
  backendConversationId.value = null
  sessionStorage.removeItem(CONVERSATION_ID_KEY)
  
  loadMessages()
}

function loadMessages() {
  messages.value = messageRepo.getBySessionId(currentSessionId.value)
  aiMetas.value = aiMetaRepo.getBySessionId(currentSessionId.value)
  scrollToBottom()
}

async function sendMessage() {
  const text = inputText.value.trim()
  
  // 输入验证
  if (!text || !currentSessionId.value) return
  if (text.length > 500) {
    errorMessage.value = '消息长度不能超过 500 个字符'
    setTimeout(() => { errorMessage.value = null }, 3000)
    return
  }
  
  if (isLoading.value) return // 防止重复发送

  // 清除错误信息
  errorMessage.value = null

  // 添加用户消息
  const userMessage = messageRepo.create({
    sessionId: currentSessionId.value,
    role: 'user',
    content: text,
    createdAt: new Date().toISOString()
  })
  messages.value.push(userMessage)
  inputText.value = ''
  scrollToBottom()

  // 调用 AI
  if (!device.value) return
  
  isLoading.value = true
  try {
    // 传入后端会话 ID（首次为空，后续带上）
    const aiResponse = await generateAIResponse(
      text,
      device.value,
      backendConversationId.value || undefined,
      currentCustomerId.value || undefined,
      'H5'
    )
    
    // 存储后端返回的会话 ID
    if (aiResponse.conversationId && !backendConversationId.value) {
      backendConversationId.value = aiResponse.conversationId
      sessionStorage.setItem(CONVERSATION_ID_KEY, aiResponse.conversationId)
      console.log('存储后端会话 ID:', aiResponse.conversationId)
    }

    // 添加 AI 消息
    const aiMessage = messageRepo.create({
      sessionId: currentSessionId.value,
      role: 'assistant',
      content: aiResponse.shortAnswerText,
      createdAt: new Date().toISOString()
    })
    messages.value.push(aiMessage)

    // 转换相关文章格式
    const relatedArticles: RelatedArticle[] | undefined = aiResponse.relatedArticles?.map(article => ({
      id: article.id,
      title: article.title,
      questionText: article.questionText,
      excerpt: article.questionText || article.title
    }))

    // 保存 AI 元数据
    const aiMeta = aiMetaRepo.create({
      sessionId: currentSessionId.value,
      relatedMessageId: aiMessage.messageId,
      confidence: aiResponse.confidence,
      topCauses: aiResponse.topCauses,
      steps: aiResponse.steps,
      safetyFlag: aiResponse.shouldEscalate,
      citedDocs: aiResponse.citedDocs,
      solution: aiResponse.solution,
      alarmCode: aiResponse.alarmCode,
      issueCategory: aiResponse.issueCategory,
      relatedArticles,
      replyMode: aiResponse.replyMode
    })
    aiMetas.value.push(aiMeta)

    // 更新会话
    sessionRepo.update(currentSessionId.value, {
      issueCategory: aiResponse.issueCategory,
      alarmCode: aiResponse.alarmCode
    })

    scrollToBottom()
  } catch (error) {
    console.error('AI 响应失败:', error)
    errorMessage.value = 'AI 响应失败，请稍后重试'
    setTimeout(() => { errorMessage.value = null }, 5000)
    
    // 添加错误提示消息
    const errorMsg = messageRepo.create({
      sessionId: currentSessionId.value,
      role: 'assistant',
      content: '抱歉，服务暂时不可用，请稍后重试或联系人工客服。',
      createdAt: new Date().toISOString()
    })
    messages.value.push(errorMsg)
    scrollToBottom()
  } finally {
    isLoading.value = false
  }
}

// function handleQuickQuestion(question: string) {
//   inputText.value = question
//   sendMessage()
// }
// 已移除快捷问题功能

function handleCreateTicket(messageId: string) {
  if (!device.value || !currentSessionId.value) return

  const aiMeta = getAIMeta(messageId)
  if (!aiMeta) return

  // 创建工单
  const ticket = ticketRepo.create({
    customerId: currentCustomerId.value,
    deviceId: currentDeviceId.value,
    sessionId: currentSessionId.value,
    title: `工单：${aiMeta.issueCategory}${aiMeta.alarmCode ? ' - ' + aiMeta.alarmCode : ''}`,
    description: `问题描述：${messages.value.find(m => m.messageId === messageId)?.content || ''}`,
    status: '待处理',
    priority: '中',
    createdAt: new Date().toISOString()
  })

  // 创建工单日志
  ticketLogRepo.create({
    ticketId: ticket.ticketId,
    action: '创建工单',
    content: '用户通过 AI 客服生成工单',
    operator: '系统',
    createdAt: new Date().toISOString()
  })

  // 更新会话
  sessionRepo.update(currentSessionId.value, {
    escalatedToTicket: true
  })

  // 跳转到工单详情
  router.push(`/ticket/${ticket.ticketId}`)
}

function handleFeedback(messageId: string, isResolved: boolean) {
  if (!currentSessionId.value) return

  // 创建反馈记录
  feedbackRepo.create({
    sessionId: currentSessionId.value,
    isResolved: isResolved,
    score: isResolved ? 5 : 3, // 已解决给5分，未解决给3分
    comment: isResolved ? '问题已解决' : '问题未解决，需要进一步跟进',
    createdAt: new Date().toISOString()
  })

  // 更新会话状态
  sessionRepo.update(currentSessionId.value, {
    resolvedStatus: isResolved ? '已解决' : '未解决'
  })

  // 显示反馈提示
  showToast(isResolved ? '感谢反馈！问题已标记为已解决。' : '我们会继续跟进您的问题。')
}

/**
 * 处理点击"其他可能匹配的问题"
 * 将选中的问题作为新输入自动发送查询
 */
function handleSelectRelatedQuestion(question: string) {
  if (!question || isLoading.value) return
  
  // 将问题填入输入框并自动发送
  inputText.value = question
  // 使用 nextTick 确保输入框更新后再发送
  nextTick(() => {
    sendMessage()
  })
}

function handleDeviceChange(newDevice: Device) {
  currentDeviceId.value = newDevice.deviceId
  device.value = newDevice
  showDevicePicker.value = false
  // 重新创建会话
  createNewSession()
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

function goBack() {
  router.push('/')
}

function goToHistory() {
  router.push({
    path: '/history',
    query: { deviceId: currentDeviceId.value }
  })
}

// 显示提示消息（简单的 toast 实现）
function showToast(message: string) {
  const toast = document.createElement('div')
  toast.className = 'toast-message'
  toast.textContent = message
  document.body.appendChild(toast)
  
  setTimeout(() => {
    toast.classList.add('show')
  }, 10)
  
  setTimeout(() => {
    toast.classList.remove('show')
    setTimeout(() => {
      document.body.removeChild(toast)
    }, 300)
  }, 2000)
}

// 监听消息变化，自动滚动
watch(messages, () => {
  scrollToBottom()
}, { deep: true })
</script>

<style scoped>
.chat-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f5f5f5;
}

.chat-header {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  background: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  z-index: 10;
}

.btn-back,
.btn-history {
  padding: 8px;
  background: none;
  border: none;
  font-size: 18px;
  color: #333;
  cursor: pointer;
}

.device-info {
  flex: 1;
  margin: 0 12px;
  cursor: pointer;
}

.device-model {
  font-size: 15px;
  font-weight: 600;
  color: #333;
}

.device-serial {
  font-size: 12px;
  color: #666;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  -webkit-overflow-scrolling: touch;
}

.message-wrapper {
  margin-bottom: 16px;
}

.chat-input-area {
  background: #fff;
  border-top: 1px solid #e0e0e0;
  padding-bottom: env(safe-area-inset-bottom);
}

.input-row {
  display: flex;
  gap: 8px;
  padding: 12px 16px;
}

.input-field {
  flex: 1;
  padding: 10px 16px;
  border: 1px solid #e0e0e0;
  border-radius: 20px;
  font-size: 15px;
  outline: none;
  /* 移动端优化 */
  -webkit-appearance: none;
  appearance: none;
  touch-action: manipulation;
}

.input-field:focus {
  border-color: #18a058;
}

.btn-send {
  padding: 10px 20px;
  background: #18a058;
  color: #fff;
  border: none;
  border-radius: 20px;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-send:hover:not(:disabled) {
  background: #159050;
}

.btn-send:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.device-picker-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: flex-end;
  z-index: 1000;
}

.modal-content {
  width: 100%;
  max-height: 80vh;
  background: #fff;
  border-radius: 16px 16px 0 0;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid #e0e0e0;
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.btn-close {
  padding: 4px 12px;
  background: none;
  border: none;
  font-size: 24px;
  color: #666;
  cursor: pointer;
}

.loading-indicator {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  justify-content: flex-start;
}

.loading-dots {
  display: flex;
  gap: 6px;
}

.loading-dots span {
  width: 8px;
  height: 8px;
  background: #18a058;
  border-radius: 50%;
  animation: loadingDot 1.4s infinite ease-in-out;
}

.loading-dots span:nth-child(1) {
  animation-delay: -0.32s;
}

.loading-dots span:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes loadingDot {
  0%, 80%, 100% {
    transform: scale(0.8);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

.loading-text {
  font-size: 14px;
  color: #666;
}

.error-message {
  padding: 12px 16px;
  background: #fff3cd;
  border-left: 4px solid #ffc107;
  border-radius: 6px;
  color: #856404;
  font-size: 14px;
  margin: 16px;
  animation: slideIn 0.3s;
}

.toast-message {
  position: fixed;
  bottom: 100px;
  left: 50%;
  transform: translateX(-50%) translateY(20px);
  background: rgba(0, 0, 0, 0.8);
  color: #fff;
  padding: 12px 24px;
  border-radius: 8px;
  font-size: 14px;
  z-index: 10000;
  opacity: 0;
  transition: all 0.3s;
  pointer-events: none;
}

.toast-message.show {
  opacity: 1;
  transform: translateX(-50%) translateY(0);
}
</style>
