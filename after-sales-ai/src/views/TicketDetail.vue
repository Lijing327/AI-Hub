<template>
  <div class="ticket-detail-page">
    <div class="header">
      <button class="btn-back" @click="goBack">←</button>
      <h2>工单详情</h2>
      <div></div>
    </div>

    <div class="ticket-content" v-if="ticket">
      <div class="ticket-card">
        <div class="card-header">
          <div class="ticket-title">{{ ticket.title }}</div>
          <TicketStatusTag :status="statusToCn(ticket.status)" />
        </div>
        <div class="card-body">
          <div class="info-section">
            <div class="info-item">
              <span class="label">工单号：</span>
              <span class="value">{{ ticket.ticketNo }}</span>
            </div>
            <div class="info-item">
              <span class="label">优先级：</span>
              <span class="value priority" :class="'p-' + ticket.priority">{{ priorityToCn(ticket.priority) }}</span>
            </div>
            <div class="info-item">
              <span class="label">设备：</span>
              <span class="value">{{ ticket.deviceMn || '未知' }}</span>
            </div>
            <div class="info-item">
              <span class="label">创建时间：</span>
              <span class="value">{{ formatTime(ticket.createdAt) }}</span>
            </div>
            <div class="info-item" v-if="ticket.assigneeName">
              <span class="label">处理人：</span>
              <span class="value">{{ ticket.assigneeName }}</span>
            </div>
          </div>

          <div class="description-section">
            <div class="section-title">问题描述</div>
            <div class="description-text">{{ ticket.description || '无' }}</div>
          </div>

          <div class="solution-section" v-if="ticket.finalSolutionSummary">
            <div class="section-title">解决方案</div>
            <div class="solution-text">{{ ticket.finalSolutionSummary }}</div>
          </div>
        </div>
      </div>

      <!-- 工单日志 -->
      <div class="logs-section">
        <div class="section-title">处理日志</div>
        <div class="logs-list">
          <div v-for="log in logs" :key="log.logId" class="log-item">
            <div class="log-header">
              <span class="log-action">{{ getActionText(log.action) }}</span>
              <span class="log-time">{{ formatTime(log.createdAt) }}</span>
            </div>
            <div class="log-content" v-if="log.content">{{ log.content }}</div>
            <div class="log-operator" v-if="log.operatorName">操作人：{{ log.operatorName }}</div>
          </div>
        </div>
      </div>

      <!-- 追加备注 -->
      <div class="action-section">
        <div class="section-title">追加备注</div>
        <textarea v-model="noteContent" placeholder="输入补充说明..." class="note-input" rows="3"></textarea>
        <button class="btn-add-note" @click="addNote" :disabled="!noteContent.trim() || addingNote">提交</button>
      </div>
    </div>

    <div v-else-if="loading" class="loading-state">加载中...</div>
    <div v-else class="empty-state">工单不存在</div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import TicketStatusTag from '@/components/TicketStatusTag.vue'
import { getTicketDetail, getTicketLogs, addTicketLog, type TicketDetail as TicketDetailType, type TicketLogItem } from '@/api/tickets'

const route = useRoute()
const router = useRouter()

const ticket = ref<TicketDetailType | null>(null)
const logs = ref<TicketLogItem[]>([])
const loading = ref(true)
const noteContent = ref('')
const addingNote = ref(false)

onMounted(async () => {
  const ticketId = route.params.id as string
  await loadTicket(ticketId)
})

async function loadTicket(id: string) {
  loading.value = true
  try {
    const [detailRes, logsRes] = await Promise.all([
      getTicketDetail(id),
      getTicketLogs(id)
    ])
    ticket.value = detailRes
    logs.value = logsRes
  } catch (err) {
    console.error('加载工单失败:', err)
    ticket.value = null
  } finally {
    loading.value = false
  }
}

function statusToCn(s: string): string {
  const map: Record<string, string> = { pending: '待处理', processing: '处理中', resolved: '已解决', closed: '已关闭' }
  return map[s] || s
}

function priorityToCn(p: string): string {
  const map: Record<string, string> = { low: '低', medium: '中', high: '高', urgent: '紧急' }
  return map[p] || p
}

function getActionText(action: string): string {
  const map: Record<string, string> = {
    create: '创建工单',
    start: '开始处理',
    resolve: '标记已解决',
    close: '关闭工单',
    comment: '添加备注',
    convert_to_kb: '转为知识库'
  }
  return map[action] || action
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

async function addNote() {
  if (!noteContent.value.trim() || !ticket.value) return
  addingNote.value = true
  try {
    await addTicketLog(ticket.value.ticketId, { content: noteContent.value })
    noteContent.value = ''
    logs.value = await getTicketLogs(ticket.value.ticketId)
    showToast('备注已添加')
  } catch (err) {
    console.error('添加备注失败:', err)
    showToast('添加备注失败')
  } finally {
    addingNote.value = false
  }
}

function showToast(message: string) {
  const toast = document.createElement('div')
  toast.className = 'toast-message'
  toast.textContent = message
  document.body.appendChild(toast)
  setTimeout(() => toast.classList.add('show'), 10)
  setTimeout(() => {
    toast.classList.remove('show')
    setTimeout(() => document.body.removeChild(toast), 300)
  }, 2000)
}

function goBack() {
  router.push('/tickets')
}
</script>

<style scoped>
.ticket-detail-page {
  min-height: 100vh;
  background: #f5f5f5;
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

.ticket-content {
  padding: 16px;
}

.ticket-card {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  margin-bottom: 16px;
  overflow: hidden;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 16px;
  background: #f8f9fa;
  border-bottom: 1px solid #e0e0e0;
}

.ticket-title {
  flex: 1;
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.card-body {
  padding: 16px;
}

.info-section {
  margin-bottom: 20px;
}

.info-item {
  display: flex;
  margin-bottom: 12px;
  font-size: 14px;
}

.info-item:last-child {
  margin-bottom: 0;
}

.label {
  color: #666;
  min-width: 80px;
}

.value {
  color: #333;
  font-weight: 500;
}

.value.priority.p-low { color: #52c41a; }
.value.priority.p-medium { color: #faad14; }
.value.priority.p-high { color: #ff7875; }
.value.priority.p-urgent { color: #ff4d4f; }

.description-section,
.solution-section {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #f0f0f0;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin-bottom: 12px;
}

.description-text,
.solution-text {
  font-size: 14px;
  color: #555;
  line-height: 1.6;
  white-space: pre-wrap;
}

.logs-section {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  margin-bottom: 16px;
}

.logs-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.log-item {
  padding: 12px;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 3px solid #18a058;
}

.log-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.log-action {
  font-weight: 600;
  font-size: 14px;
  color: #333;
}

.log-time {
  font-size: 12px;
  color: #999;
}

.log-content {
  font-size: 13px;
  color: #555;
  line-height: 1.5;
  margin-bottom: 6px;
}

.log-operator {
  font-size: 12px;
  color: #999;
}

.action-section {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.note-input {
  width: 100%;
  padding: 12px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  font-size: 14px;
  resize: vertical;
  margin-bottom: 12px;
  box-sizing: border-box;
}

.btn-add-note {
  padding: 10px 20px;
  background: #18a058;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
}

.btn-add-note:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.loading-state,
.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #999;
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
