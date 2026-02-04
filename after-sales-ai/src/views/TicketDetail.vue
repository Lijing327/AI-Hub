<template>
  <div class="ticket-detail-page">
    <div class="header">
      <button class="btn-back" @click="goBack">←</button>
      <h2>工单详情</h2>
      <div></div>
    </div>

    <div class="ticket-content">
      <div class="ticket-card">
        <div class="card-header">
          <div class="ticket-title">{{ ticket?.title }}</div>
          <TicketStatusTag :status="ticket?.status || '待处理'" />
        </div>
        <div class="card-body">
          <div class="info-section">
            <div class="info-item">
              <span class="label">设备：</span>
              <span class="value">{{ getDeviceModel(ticket?.deviceId || '') }}</span>
            </div>
            <div class="info-item">
              <span class="label">优先级：</span>
              <span class="value priority" :class="ticket?.priority">{{ ticket?.priority }}</span>
            </div>
            <div class="info-item">
              <span class="label">创建时间：</span>
              <span class="value">{{ formatTime(ticket?.createdAt || '') }}</span>
            </div>
            <div class="info-item" v-if="ticket?.assignee">
              <span class="label">处理人：</span>
              <span class="value">{{ ticket.assignee }}</span>
            </div>
          </div>

          <div class="description-section">
            <div class="section-title">问题描述</div>
            <div class="description-text">{{ ticket?.description }}</div>
          </div>

          <div class="solution-section" v-if="ticket?.finalSolutionSummary">
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
              <span class="log-action">{{ log.action }}</span>
              <span class="log-time">{{ formatTime(log.createdAt) }}</span>
            </div>
            <div class="log-content">{{ log.content }}</div>
            <div class="log-operator">操作人：{{ log.operator }}</div>
          </div>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="action-section" v-if="ticket && ticket.status !== '已解决' && ticket.status !== '已关闭'">
        <button class="btn-action" @click="simulateEngineerAction">模拟工程师处理</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import TicketStatusTag from '@/components/TicketStatusTag.vue'
import { ticketRepo, ticketLogRepo, deviceRepo } from '@/store/repositories'
import type { Ticket, TicketLog } from '@/models/types'

const route = useRoute()
const router = useRouter()

const ticket = ref<Ticket | null>(null)
const logs = ref<TicketLog[]>([])

onMounted(() => {
  const ticketId = route.params.id as string
  ticket.value = ticketRepo.getById(ticketId)
  
  if (!ticket.value) {
    router.push('/tickets')
    return
  }

  logs.value = ticketLogRepo.getByTicketId(ticketId)
})

function getDeviceModel(deviceId: string): string {
  const device = deviceRepo.getById(deviceId)
  return device ? `${device.model} (${device.serialNo})` : '未知设备'
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

function simulateEngineerAction() {
  if (!ticket.value) return

  const actions = [
    { action: '开始处理', content: '工程师已开始处理此工单，正在排查问题原因。', nextStatus: '处理中' as const },
    { action: '问题排查', content: '已完成初步排查，确认为设备硬件故障，需要更换相关部件。', nextStatus: '处理中' as const },
    { action: '问题解决', content: '已完成设备维修，问题已解决。设备已恢复正常运行。', nextStatus: '已解决' as const }
  ]

  const currentStatus = ticket.value.status
  let actionIndex = 0
  
  if (currentStatus === '待处理') {
    actionIndex = 0
  } else if (currentStatus === '处理中') {
    actionIndex = logs.value.length >= 2 ? 2 : 1
  }

  const selectedAction = actions[actionIndex]

  // 创建日志
  const newLog = ticketLogRepo.create({
    ticketId: ticket.value.ticketId,
    action: selectedAction.action,
    content: selectedAction.content,
    operator: '工程师-张工',
    createdAt: new Date().toISOString()
  })
  logs.value.push(newLog)

  // 更新工单状态
  const updates: Partial<Ticket> = {
    status: selectedAction.nextStatus,
    assignee: '工程师-张工'
  }

  if (selectedAction.nextStatus === '已解决') {
    updates.finalSolutionSummary = selectedAction.content
    updates.closedAt = new Date().toISOString()
  }

  ticketRepo.update(ticket.value.ticketId, updates)
  ticket.value = { ...ticket.value, ...updates } as Ticket

  showToast(`已${selectedAction.action}`)
}

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

.value.priority.低 {
  color: #52c41a;
}

.value.priority.中 {
  color: #faad14;
}

.value.priority.高 {
  color: #ff7875;
}

.value.priority.紧急 {
  color: #ff4d4f;
}

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
  padding: 16px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.btn-action {
  width: 100%;
  padding: 14px;
  background: #18a058;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-action:hover {
  background: #159050;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(24, 160, 88, 0.3);
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
