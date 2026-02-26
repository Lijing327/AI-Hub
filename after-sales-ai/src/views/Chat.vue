<template>
  <div class="chat-page">
    <!-- 顶部栏 -->
    <div class="chat-header">
      <!-- <button class="btn-back" @click="goBack" aria-label="返回">←</button> -->
      <div class="device-info" @click="showDevicePicker = true">
        <div class="device-model">{{ isDefaultDevice ? '智能客服' : device?.model }}</div>
        <div class="device-serial">{{ isDefaultDevice ? '点击可切换设备' : `SN: ${device?.serialNo}` }}</div>
      </div>
      <!-- 用户信息区域 -->
      <div class="user-info">
        <div v-if="currentUser" ref="menuContainerRef" class="user-menu-container">
          <button @click="toggleMenu" class="menu-trigger-btn">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" class="user-icon" fill="currentColor"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg>
          </button>
          <transition name="fade">
            <div v-if="isMenuOpen" class="dropdown-menu">
              <div class="dropdown-item user-phone-display">{{ currentUser.account }}</div>
              <div class="dropdown-divider"></div>
              <button @click="goToHistory" class="dropdown-item menu-action">历史记录</button>
              <button @click="handleChangePassword" class="dropdown-item menu-action">修改密码</button>
              <button @click="showProfileUpdate = true" class="dropdown-item menu-action">更新资料</button>
              <div class="dropdown-divider"></div>
              <button @click="handleLogout" class="dropdown-item logout-action">退出登录</button>
            </div>
          </transition>
        </div>
        <router-link v-else to="/login" class="btn-login">登录</router-link>
      </div>
    </div>

    <!-- 聊天区 -->
    <div class="chat-messages" ref="messagesContainer">
      <!-- 空状态欢迎语 -->
      <div v-if="messages.length === 0 && !isLoading" class="welcome-bubble">
        <div class="welcome-avatar">AI</div>
        <div class="welcome-text">
          <p>您好，我是造型机技术资源库。</p>
          <p>您可以描述设备现象、报警码或操作问题，我会帮您排查并给出步骤与方案。</p>
        </div>
      </div>
      <div v-for="message in messages" :key="message.messageId" class="message-wrapper">
        <!-- 有故障排查卡片时不展示短答气泡（顶部短答+时间）；无卡片时照常展示对话气泡 -->
        <ChatMessageBubble v-if="!(message.role === 'assistant' && shouldShowAnswerCard(message.messageId))" :message="message" />
        <!-- 仅在有结构化回复时展示故障排查卡片；conversation 模式（如「你是谁」）只展示对话气泡 -->
        <AiAnswerCard
          v-if="message.role === 'assistant' && shouldShowAnswerCard(message.messageId)"
          :meta="getAIMeta(message.messageId)!"
          :solution="getSolution(message.messageId)"
          :related-articles="getRelatedArticles(message.messageId)"
          :technical-resources="getTechnicalResources(message.messageId)"
          :selected-detail="getSelectedArticleDetail(message.messageId)"
          :loading-detail="isLoadingArticleDetail(message.messageId)"
          :readonly="false"
          @create-ticket="handleCreateTicket(message.messageId)"
          @feedback="handleFeedback(message.messageId, $event)"
          @select-related-question="(article) => handleSelectRelatedQuestion(message.messageId, article)"
        />
        <!-- 转人工：仅展示引导话术 + 客服电话卡片，不展示故障排查 -->
        <div
          v-if="message.role === 'assistant' && getAIMeta(message.messageId)?.replyMode === 'handoff'"
          class="handoff-card"
        >
          <div class="handoff-title">转人工客服</div>
          <p class="handoff-desc">请提供设备型号、故障现象、发生时间及联系方式，我们将转交工程师跟进。</p>
          <a class="handoff-phone" href="tel:0312-7027666">📞 人工客服电话：0312-7027666</a>
        </div>
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

    <!-- 修改密码弹窗 -->
    <div v-if="showPasswordModal" class="modal-overlay" @click.self="showPasswordModal = false">
      <div class="modal-container">
        <div class="modal-header">
          <h3>修改密码</h3>
          <button class="btn-close" @click="showPasswordModal = false">×</button>
        </div>
        <form class="password-form" @submit.prevent="handlePasswordSubmit">
          <div class="form-group">
            <label for="current-password">当前密码</label>
            <input id="current-password" v-model="passwordForm.currentPassword" type="password" required placeholder="请输入当前密码" />
          </div>
          <div class="form-group">
            <label for="new-password">新密码</label>
            <input id="new-password" v-model="passwordForm.newPassword" type="password" required placeholder="请输入新密码（至少 6 位）" minlength="6" />
          </div>
          <div class="form-group">
            <label for="confirm-password">确认新密码</label>
            <input id="confirm-password" v-model="passwordForm.confirmPassword" type="password" required placeholder="请再次输入新密码" minlength="6" />
          </div>
          <p v-if="passwordError" class="form-error">{{ passwordError }}</p>
          <div class="form-actions">
            <button type="button" class="btn-cancel" @click="showPasswordModal = false">取消</button>
            <button type="submit" class="btn-submit" :disabled="passwordSubmitting">提交</button>
          </div>
        </form>
      </div>
    </div>

    <!-- 更新资料弹窗 -->
    <div v-if="showProfileUpdate" class="modal-overlay" @click.self="showProfileUpdate = false">
      <div class="modal-container">
        <div class="modal-header">
          <h3>更新资料</h3>
          <button class="btn-close" @click="showProfileUpdate = false">×</button>
        </div>
        <form class="profile-form" @submit.prevent="handleProfileSubmit">
          <div class="form-group">
            <label>账户状态</label>
            <select v-model="profileForm.status" class="form-control">
              <option value="active">正常 (active)</option>
              <option value="disabled">禁用 (disabled)</option>
            </select>
          </div>
          <p v-if="profileError" class="form-error">{{ profileError }}</p>
          <p v-if="profileSuccess" class="form-success">{{ profileSuccess }}</p>
          <div class="form-actions">
            <button type="button" class="btn-cancel" @click="showProfileUpdate = false">取消</button>
            <button type="submit" class="btn-submit" :disabled="profileSubmitting">提交</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ChatMessageBubble from '@/components/ChatMessageBubble.vue'
import AiAnswerCard from '@/components/AiAnswerCard.vue'
// import QuickQuestions from '@/components/QuickQuestions.vue' // 已移除快捷问题显示
import DevicePicker from '@/components/DevicePicker.vue'
import { sessionRepo, messageRepo, aiMetaRepo, ticketRepo, ticketLogRepo, deviceRepo, feedbackRepo } from '@/store/repositories'
import { generateAIResponse, rewriteAttachmentUrlForDev } from '@/ai/ai_service'
import { getArticleDetail } from '@/api/knowledge'
import { getCurrentUser, changePassword as apiChangePassword, updateProfile as apiUpdateProfile } from '@/api/auth'
import type { ChatMessage, Device, AIResponseMeta, RelatedArticle, TechnicalResource } from '@/models/types'

/** 当前选中的「其他问题」详情（与首条「最有可能」并列展示用） */
interface SelectedArticleDetail {
  topCauses: string[]
  steps: Array<{ title?: string; action?: string; expect?: string; next?: string }>
  solution: { temporary: string; final: string }
  technicalResources: TechnicalResource[]
}
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
const currentUser = ref<{ id: string; account: string; createdAt: string } | null>(null)

// 下拉菜单状态
const isMenuOpen = ref(false)
const menuContainerRef = ref<HTMLElement | null>(null)

// 修改密码弹窗状态
const showPasswordModal = ref(false)
const passwordForm = ref({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})
const passwordError = ref('')
const passwordSubmitting = ref(false)

// 更新资料弹窗状态
const showProfileUpdate = ref(false)
const profileForm = ref({
  status: 'active'
})
const profileError = ref('')
const profileSuccess = ref('')
const profileSubmitting = ref(false)

// 审计相关：后端返回的会话 ID（用于后续消息关联）
const backendConversationId = ref<string | null>(null)

// 点击「其他问题」时按需拉取的详情，key = messageId
const selectedArticleDetailsByMessageId = ref<Record<string, SelectedArticleDetail | null>>({})
const loadingArticleDetailForMessageId = ref<string | null>(null)

// 会话存储 key
const CONVERSATION_ID_KEY = 'ai_conversation_id'

// 获取 AI 元数据
function getAIMeta(messageId: string): AIResponseMeta | null {
  return aiMetas.value.find((m) => m.relatedMessageId === messageId) || null
}

// 是否展示故障排查卡片：有 AI 元数据且为 troubleshooting 时展示；conversation/handoff 不展示
function shouldShowAnswerCard(messageId: string): boolean {
  const meta = getAIMeta(messageId)
  return meta != null && meta.replyMode !== 'conversation' && meta.replyMode !== 'handoff'
}

// 获取解决方案（选中「其他问题」时用其 solution，否则用首条 meta）
function getSolution(messageId: string): { temporary: string; final: string } {
  const selected = getSelectedArticleDetail(messageId)
  if (selected?.solution) return selected.solution
  const meta = getAIMeta(messageId)
  if (!meta?.solution) return { temporary: '', final: '' }
  return meta.solution
}

// 获取相关文章
function getRelatedArticles(messageId: string): RelatedArticle[] | undefined {
  const meta = getAIMeta(messageId)
  return meta?.relatedArticles
}

// 获取技术资料（附件）：选中其他问题时用其附件，否则用首条 meta
function getTechnicalResources(messageId: string): TechnicalResource[] | undefined {
  const selected = selectedArticleDetailsByMessageId.value[messageId]
  if (selected) return selected.technicalResources ?? []
  const meta = getAIMeta(messageId)
  return meta?.technicalResources
}

// 当前消息是否正在拉取「其他问题」详情
function isLoadingArticleDetail(messageId: string): boolean {
  return loadingArticleDetailForMessageId.value === messageId
}

// 当前消息选中的文章详情（点击其他问题时拉取）；为 null 时展示首条「最有可能」的数据
function getSelectedArticleDetail(messageId: string): SelectedArticleDetail | null {
  return selectedArticleDetailsByMessageId.value[messageId] ?? null
}

// 是否从欢迎页直接进入（未选设备，使用默认）
const isDefaultDevice = ref(false)

const toggleMenu = () => {
  isMenuOpen.value = !isMenuOpen.value;
};

const closeMenuOnClickOutside = (event: MouseEvent) => {
  if (menuContainerRef.value && !menuContainerRef.value.contains(event.target as Node)) {
    isMenuOpen.value = false;
  }
};

onMounted(async () => {
  // 检查是否已登录
  const token = localStorage.getItem('token')
  if (!token) {
    router.push('/login')
    return
  }

  // 获取当前用户信息
  try {
    const user = await getCurrentUser()
    currentUser.value = user
  } catch (error) {
    console.error('获取用户信息失败:', error)
    localStorage.removeItem('token')
    router.push('/login')
    return
  }

  // 初始化设备
  allDevices.value = deviceRepo.getAll()
  let deviceId = route.query.deviceId as string
  const customerId = route.query.customerId as string

  // 无 deviceId 时使用默认设备（欢迎页「开始咨询」进入）
  if (!deviceId && allDevices.value.length > 0) {
    deviceId = allDevices.value[0].deviceId
    isDefaultDevice.value = true
  }

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
  document.addEventListener('click', closeMenuOnClickOutside);
})

onUnmounted(() => {
  document.removeEventListener('click', closeMenuOnClickOutside);
});

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
  const loadingTimeoutId = window.setTimeout(() => {
    if (isLoading.value) {
      isLoading.value = false
      errorMessage.value = '请求超时，请检查网络或稍后重试'
      setTimeout(() => { errorMessage.value = null }, 5000)
    }
  }, 65000)
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
      technicalResources: aiResponse.technicalResources,
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
    window.clearTimeout(loadingTimeoutId)
    isLoading.value = false
  }
}

// function handleQuickQuestion(question: string) {
//   inputText.value = question
//   sendMessage()
// }
// 已移除快捷问题功能

function handleCreateTicket(_messageId: string) {
  if (!device.value || !currentSessionId.value) return

  const aiMeta = getAIMeta(_messageId)
  if (!aiMeta) return

  // 创建工单
  const ticket = ticketRepo.create({
    customerId: currentCustomerId.value,
    deviceId: currentDeviceId.value,
    sessionId: currentSessionId.value,
    title: `工单：${aiMeta.issueCategory}${aiMeta.alarmCode ? ' - ' + aiMeta.alarmCode : ''}`,
    description: `问题描述：${messages.value.find(m => m.messageId === _messageId)?.content || ''}`,
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

function handleFeedback(_messageId: string, isResolved: boolean) {
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
 * 处理点击问题列表：首条「最有可能」直接展开已有数据；其他问题再请求详情后展示
 */
async function handleSelectRelatedQuestion(messageId: string, article: RelatedArticle) {
  const related = getRelatedArticles(messageId)
  const primaryId = related?.[0]?.id
  // 点击的是首条（最有可能）→ 直接展示当前 meta，清空选中详情
  if (primaryId != null && article.id === primaryId) {
    selectedArticleDetailsByMessageId.value[messageId] = null
    return
  }
  // 点击其他问题 → 按需拉取该文章详情
  loadingArticleDetailForMessageId.value = messageId
  try {
    const res = await getArticleDetail(article.id)
    const detail: SelectedArticleDetail = {
      topCauses: Array.isArray(res.top_causes) ? res.top_causes : [],
      steps: Array.isArray(res.steps) ? res.steps : [],
      solution: res.solution && typeof res.solution === 'object' ? res.solution : { temporary: '', final: '' },
      technicalResources: (res.technical_resources ?? []).filter(r => r != null).map(r => ({
        id: Number((r as any)?.id) || 0,
        name: (r as any)?.name ?? '',
        type: (r as any)?.type ?? 'other',
        url: rewriteAttachmentUrlForDev((r as any)?.url ?? ''),
        size: (r as any)?.size,
        duration: (r as any)?.duration
      }))
    }
    selectedArticleDetailsByMessageId.value[messageId] = detail
  } catch (e) {
    console.error('拉取文章详情失败:', e)
    selectedArticleDetailsByMessageId.value[messageId] = null
  } finally {
    loadingArticleDetailForMessageId.value = null
  }
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

function goToHistory() {
  router.push({
    path: '/history',
    query: { deviceId: currentDeviceId.value }
  })
}

function handleLogout() {
  localStorage.removeItem('token')
  currentUser.value = null
  isMenuOpen.value = false // 关闭菜单
  router.push('/login')
}

async function handlePasswordSubmit() {
  passwordError.value = ''

  if (passwordForm.value.newPassword !== passwordForm.value.confirmPassword) {
    passwordError.value = '两次输入的新密码不一致'
    return
  }

  if (passwordForm.value.newPassword.length < 6) {
    passwordError.value = '新密码至少需要 6 个字符'
    return
  }

  passwordSubmitting.value = true
  try {
    const result = await apiChangePassword({
      currentPassword: passwordForm.value.currentPassword,
      newPassword: passwordForm.value.newPassword
    })

    if (result.success) {
      showToast('密码修改成功')
      showPasswordModal.value = false
      passwordForm.value = {
        currentPassword: '',
        newPassword: '',
        confirmPassword: ''
      }
    } else {
      passwordError.value = result.message || '修改密码失败'
    }
  } catch (error) {
    console.error('修改密码失败:', error)
    passwordError.value = '修改密码失败，请重试'
  } finally {
    passwordSubmitting.value = false
  }
}

async function handleProfileSubmit() {
  profileError.value = ''
  profileSuccess.value = ''

  profileSubmitting.value = true
  try {
    const result = await apiUpdateProfile({
      status: profileForm.value.status
    })

    if (result.success) {
      profileSuccess.value = '资料更新成功'
      setTimeout(() => {
        showProfileUpdate.value = false
        profileSuccess.value = ''
        profileForm.value.status = 'active'
      }, 1500)
    } else {
      profileError.value = result.message || '更新资料失败'
    }
  } catch (error) {
    console.error('更新资料失败:', error)
    profileError.value = '更新资料失败，请重试'
  } finally {
    profileSubmitting.value = false
  }
}

function handleChangePassword() {
  showPasswordModal.value = true
  passwordError.value = ''
  passwordForm.value = {
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  }
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

.user-info {
  margin-left: auto;
}

/* Dropdown Menu Styles */
.user-menu-container {
  position: relative;
  display: flex;
  align-items: center;
}

.menu-trigger-btn {
  background: none;
  border: none;
  padding: 6px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.2s;
}

.menu-trigger-btn:hover {
  background-color: #f0f0f0;
}

.user-icon {
  width: 22px;
  height: 22px;
  color: #333;
}

.dropdown-menu {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  min-width: 160px;
  z-index: 100;
  padding: 8px 0;
  border: 1px solid #ebeeef;
}

.dropdown-item {
  display: block;
  width: 100%;
  text-align: left;
  padding: 8px 16px;
  font-size: 14px;
  color: #333;
  background: none;
  border: none;
  cursor: default;
}

.user-phone-display {
  font-weight: 500;
  color: #000;
}

.logout-action {
  cursor: pointer;
  color: #f56c6c;
}

.logout-action:hover {
  background-color: #fef0f0;
}

.dropdown-divider {
  border: none;
  border-top: 1px solid #ebeeef;
  margin: 8px 0;
}

.btn-login {
  padding: 6px 12px;
  font-size: 14px;
  border-radius: 6px;
  border: none;
  cursor: pointer;
  transition: all 0.2s;
  background: #18a058;
  color: #fff;
  text-decoration: none;
}

.btn-login:hover {
  background: #159050;
}

/* Fade Transition */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

.btn-login:hover {
  background: #159050;
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

.welcome-bubble {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  padding: 16px;
  margin-bottom: 16px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 1px 8px rgba(0, 0, 0, 0.06);
}

.welcome-avatar {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: linear-gradient(135deg, #38bdf8 0%, #0ea5e9 100%);
  color: #fff;
  font-size: 12px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.welcome-text {
  flex: 1;
}

.welcome-text p {
  margin: 0 0 6px;
  font-size: 15px;
  color: #333;
  line-height: 1.5;
}

.welcome-text p:last-child {
  margin-bottom: 0;
  color: #666;
}

.message-wrapper {
  margin-bottom: 16px;
}

.handoff-card {
  margin-top: 8px;
  padding: 14px 16px;
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  border-radius: 12px;
  border-left: 4px solid #0ea5e9;
}

.handoff-title {
  font-size: 15px;
  font-weight: 600;
  color: #0c4a6e;
  margin-bottom: 8px;
}

.handoff-desc {
  font-size: 14px;
  color: #475569;
  margin: 0 0 10px;
  line-height: 1.5;
}

.handoff-phone {
  display: inline-block;
  font-size: 15px;
  font-weight: 600;
  color: #0369a1;
  text-decoration: none;
  padding: 6px 12px;
  background: #fff;
  border-radius: 8px;
  border: 1px solid #0ea5e9;
  transition: background 0.2s;
}

.handoff-phone:hover {
  background: #e0f2fe;
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

/* 模态框覆盖层 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}

.modal-container {
  background: #fff;
  border-radius: 12px;
  width: 90%;
  max-width: 400px;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.2);
}

.modal-container .modal-header {
  position: sticky;
  top: 0;
  background: #fff;
  z-index: 1;
  border-bottom: 1px solid #e0e0e0;
  padding: 16px 20px;
}

/* 表单样式 */
.password-form,
.profile-form {
  padding: 20px;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.form-group input[type="password"],
.form-control {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
  box-sizing: border-box;
}

.form-group input:focus,
.form-control:focus {
  border-color: #18a058;
}

.form-group input[type="password"]::placeholder {
  color: #999;
}

.form-control {
  cursor: pointer;
}

.form-actions {
  display: flex;
  gap: 12px;
  margin-top: 24px;
}

.btn-cancel,
.btn-submit {
  flex: 1;
  padding: 10px 16px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-cancel {
  background: #f5f5f5;
  color: #666;
}

.btn-cancel:hover {
  background: #e8e8e8;
}

.btn-submit {
  background: #18a058;
  color: #fff;
}

.btn-submit:hover:not(:disabled) {
  background: #159050;
}

.btn-submit:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.form-error {
  color: #f56c6c;
  font-size: 13px;
  margin-top: 8px;
}

.form-success {
  color: #18a058;
  font-size: 13px;
  margin-top: 8px;
}

/* 菜单项样式 */
.menu-action {
  cursor: pointer;
  text-align: left;
  color: #333;
}

.menu-action:hover {
  background-color: #f5f5f5;
}
</style>
