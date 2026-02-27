<template>
  <div class="ticket-detail-page">
    <div class="header">
      <button class="btn-back" @click="goBack">←</button>
      <h2>{{ ticket?.ticketNo }} - {{ ticket?.title }}</h2>
      <TicketStatusTag :status="ticket?.status || 'pending'" />
    </div>

    <div class="content" v-if="ticket">
      <!-- 基本信息 -->
      <div class="section">
        <h3 class="section-title">基本信息</h3>
        <div class="info-grid">
          <div class="info-item">
            <span class="label">工单号:</span>
            <span class="value">{{ ticket.ticketNo }}</span>
          </div>
          <div class="info-item">
            <span class="label">状态:</span>
            <span class="value status-{{ getStatusClass(ticket.status) }}">{{ getStatusText(ticket.status) }}</span>
          </div>
          <div class="info-item">
            <span class="label">优先级:</span>
            <span class="value priority-{{ getPriorityClass(ticket.priority) }}">
              {{ getPriorityText(ticket.priority) }}
            </span>
          </div>
          <div class="info-item">
            <span class="label">来源:</span>
            <span class="value">{{ getSourceText(ticket.source) }}</span>
          </div>
          <div class="info-item">
            <span class="label">负责人:</span>
            <span class="value">{{ ticket.assigneeName || '未分配' }}</span>
          </div>
          <div class="info-item">
            <span class="label">创建人:</span>
            <span class="value">{{ ticket.createdBy }}</span>
          </div>
          <div class="info-item">
            <span class="label">创建时间:</span>
            <span class="value">{{ formatTime(ticket.createdAt) }}</span>
          </div>
          <div class="info-item" v-if="ticket.updatedAt">
            <span class="label">更新时间:</span>
            <span class="value">{{ formatTime(ticket.updatedAt) }}</span>
          </div>
        </div>
      </div>

      <!-- 问题描述 -->
      <div class="section" v-if="ticket.description">
        <h3 class="section-title">问题描述</h3>
        <div class="description-content">{{ ticket.description }}</div>
      </div>

      <!-- AI 会话信息 -->
      <div class="section" v-if="ticket.sessionId && aiSession">
        <h3 class="section-title">AI 会话</h3>
        <div class="session-info">
          <div class="info-item">
            <span class="label">会话 ID:</span>
            <span class="value monospace">{{ ticket.sessionId }}</span>
          </div>
          <div class="info-item">
            <span class="label">会话时长:</span>
            <span class="value">{{ sessionDuration }}</span>
          </div>
        </div>
      </div>

      <!-- 最终解决方案 -->
      <div class="section" v-if="ticket.finalSolutionSummary">
        <h3 class="section-title">解决方案</h3>
        <div class="solution-content">{{ ticket.finalSolutionSummary }}</div>
      </div>

      <!-- 操作历史 -->
      <div class="section">
        <h3 class="section-title">操作记录</h3>
        <div class="logs-list">
          <div v-for="log in logs" :key="log.logId" class="log-item">
            <div class="log-header">
              <span class="log-action">{{ getActionText(log.action) }}</span>
              <span class="log-time">{{ formatTime(log.createdAt) }}</span>
            </div>
            <div class="log-content" v-if="log.content">{{ log.content }}</div>
            <div class="log-meta" v-if="log.operatorName">
              操作人：{{ log.operatorName }}
            </div>
          </div>
        </div>
      </div>

      <!-- 操作按钮区 -->
      <div class="actions-section">
        <template v-if="ticket.status === 'pending'">
          <button class="btn-primary" @click="showStartModal = true">开始处理</button>
        </template>

        <template v-if="ticket.status === 'processing'">
          <button class="btn-success" @click="showResolveModal = true">标记已解决</button>
          <button class="btn-secondary" @click="showCloseModal = true">关闭工单</button>
        </template>

        <template v-if="ticket.status === 'resolved'">
          <button class="btn-secondary" @click="showConvertKbModal = true">转为知识库</button>
          <button class="btn-secondary" @click="showCloseModal = true">关闭工单</button>
        </template>

        <template v-if="ticket.status === 'closed'">
          <span class="btn-disabled">已关闭</span>
        </template>
      </div>

      <!-- 添加工单备注 -->
      <div class="section">
        <h3 class="section-title">添加备注</h3>
        <textarea
          v-model="noteContent"
          placeholder="输入备注内容..."
          class="note-input"
          rows="3"
        ></textarea>
        <button class="btn-add-note" @click="addNote">提交</button>
      </div>
    </div>

    <!-- 开始处理弹窗 -->
    <div v-if="showStartModal" class="modal-overlay" @click.self="closeModals">
      <div class="modal">
        <h3>开始处理</h3>
        <div class="modal-form">
          <label>
            负责人:
            <input v-model="assigneeName" type="text" placeholder="请输入负责人姓名" />
          </label>
          <label>
            备注:
            <textarea v-model="startNote" placeholder="处理说明" rows="3"></textarea>
          </label>
        </div>
        <div class="modal-actions">
          <button class="btn-cancel" @click="closeModals">取消</button>
          <button class="btn-confirm" @click="submitStart">确认</button>
        </div>
      </div>
    </div>

    <!-- 解决工单弹窗 -->
    <div v-if="showResolveModal" class="modal-overlay" @click.self="closeModals">
      <div class="modal">
        <h3>标记已解决</h3>
        <div class="modal-form">
          <label class="required">
            解决方案摘要 (必填):
            <textarea v-model="resolveSummary" placeholder="请填写最终解决方案..." rows="5"></textarea>
          </label>
          <label>
            备注:
            <textarea v-model="resolveNote" placeholder="补充说明" rows="3"></textarea>
          </label>
        </div>
        <div class="modal-actions">
          <button class="btn-cancel" @click="closeModals">取消</button>
          <button class="btn-confirm" @click="submitResolve">确认</button>
        </div>
      </div>
    </div>

    <!-- 关闭工单弹窗 -->
    <div v-if="showCloseModal" class="modal-overlay" @click.self="closeModals">
      <div class="modal">
        <h3>关闭工单</h3>
        <div class="modal-form">
          <label>
            备注 (可选):
            <textarea v-model="closeNote" placeholder="关闭原因或补充说明" rows="3"></textarea>
          </label>
        </div>
        <div class="modal-actions">
          <button class="btn-cancel" @click="closeModals">取消</button>
          <button class="btn-confirm" @click="submitClose">确认</button>
        </div>
      </div>
    </div>

    <!-- 转为知识库弹窗 -->
    <div v-if="showConvertKbModal" class="modal-overlay" @click.self="closeModals">
      <div class="modal">
        <h3>转为知识库文章</h3>
        <p class="modal-hint">
          将基于工单的解决方案生成知识库文章，并自动触发向量入库。
        </p>
        <div class="modal-info">
          <p><strong>标题:</strong> [{{ ticket.ticketNo }}] {{ ticket.title }}</p>
          <p><strong>问题:</strong> {{ ticket.description || '无描述' }}</p>
          <p><strong>解决方案:</strong> {{ ticket.finalSolutionSummary?.substring(0, 100) }}...</p>
        </div>
        <div class="modal-actions">
          <button class="btn-cancel" @click="closeModals">取消</button>
          <button class="btn-confirm btn-warning" @click="submitConvertKb">确认转换</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import TicketStatusTag from '@/components/TicketStatusTag.vue'
import api from '@/utils/api'

const route = useRoute()
const router = useRouter()

interface TicketDetailDto {
  ticketId: string
  ticketNo: string
  title: string
  description?: string
  status: string
  priority: string
  source: string
  assigneeName?: string
  createdBy: string
  createdAt: string
  updatedAt?: string
  closedAt?: string
  finalSolutionSummary?: string
  sessionId?: string
  triggerMessageId?: string
  metaJson?: string
}

interface TicketLogDto {
  logId: number
  ticketId: string
  action: string
  content?: string
  operatorName?: string
  nextStatus?: string
  createdAt: string
}

const ticket = ref<TicketDetailDto | null>(null)
const logs = ref<TicketLogDto[]>([])
const aiSession = ref<any>(null)

// 模态框状态
const showStartModal = ref(false)
const showResolveModal = ref(false)
const showCloseModal = ref(false)
const showConvertKbModal = ref(false)

// 表单数据
const assigneeName = ref('')
const startNote = ref('')
const resolveSummary = ref('')
const resolveNote = ref('')
const closeNote = ref('')
const noteContent = ref('')

onMounted(async () => {
  await loadTicket()
})

async function loadTicket() {
  const id = route.params.id as string
  try {
    const detailRes = await api.get(`admin/tickets/${id}`)
    ticket.value = detailRes.data
    logs.value = detailRes.data?.logs || []
  } catch (error: unknown) {
    console.error('加载工单详情失败:', error)
    const err = error as { response?: { data?: { message?: string } } }
    alert(err?.response?.data?.message || '加载失败')
    router.push('/admin/tickets')
  }
}

function getStatusClass(status: string): string {
  const map: Record<string, string> = {
    pending: 'pending',
    processing: 'processing',
    resolved: 'resolved',
    closed: 'closed'
  }
  return map[status] || status
}

function getStatusText(status: string): string {
  const map: Record<string, string> = {
    pending: '待处理',
    processing: '处理中',
    resolved: '已解决',
    closed: '已关闭'
  }
  return map[status] || status
}

function getPriorityClass(priority: string): string {
  const map: Record<string, string> = {
    low: '低',
    medium: '中',
    high: '高',
    urgent: '紧急'
  }
  return map[priority] || priority
}

function getPriorityText(priority: string): string {
  return getPriorityClass(priority)
}

function getSourceText(source: string): string {
  const map: Record<string, string> = {
    ai_chat: 'AI 对话',
    manual: '手动创建',
    api: 'API 创建'
  }
  return map[source] || source
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

function closeModals() {
  showStartModal.value = false
  showResolveModal.value = false
  showCloseModal.value = false
  showConvertKbModal.value = false
}

async function submitStart() {
  try {
    const id = route.params.id as string
    const response = await api.post(`admin/tickets/${id}/start`, {
      assigneeName: assigneeName.value,
      note: startNote.value
    })
    ticket.value = response.data
    await loadTicket()
    closeModals()
    alert('已开始处理')
  } catch (error: any) {
    alert(error.response?.data?.error || error.response?.data?.message || '操作失败')
  }
}

async function submitResolve() {
  if (!resolveSummary.value.trim()) {
    alert('解决方案不能为空')
    return
  }
  try {
    const id = route.params.id as string
    const response = await api.post(`admin/tickets/${id}/resolve`, {
      finalSolutionSummary: resolveSummary.value,
      note: resolveNote.value
    })
    ticket.value = response.data
    await loadTicket()
    closeModals()
    alert('已标记为已解决')
  } catch (error: any) {
    alert(error.response?.data?.error || error.response?.data?.message || '操作失败')
  }
}

async function submitClose() {
  try {
    const id = route.params.id as string
    const response = await api.post(`admin/tickets/${id}/close`, {
      note: closeNote.value
    })
    ticket.value = response.data
    await loadTicket()
    closeModals()
    alert('工单已关闭')
  } catch (error: any) {
    alert(error.response?.data?.error || error.response?.data?.message || '操作失败')
  }
}

async function submitConvertKb() {
  try {
    const id = route.params.id as string
    const response = await api.post(`admin/tickets/${id}/convert-to-kb`, { triggerVectorIndex: true })
    const data = response.data as { message?: string; vectorSuccess?: boolean; vectorMessage?: string }
    const msg = data.vectorSuccess
      ? `${data.message || '已成功转为知识库文章'}\n向量入库：${data.vectorMessage || '成功'}`
      : `${data.message || '已转为知识库文章'}\n向量入库：${data.vectorMessage || '失败'}`
    alert(msg)
    await loadTicket()
    closeModals()
  } catch (error: unknown) {
    const err = error as { response?: { data?: { error?: string; message?: string } } }
    alert(err?.response?.data?.error || err?.response?.data?.message || '操作失败')
  }
}

async function addNote() {
  if (!noteContent.value.trim()) {
    alert('请输入备注内容')
    return
  }
  try {
    const id = route.params.id as string
    await api.post(`admin/tickets/${id}/logs`, {
      content: noteContent.value,
      operatorName: ''
    })
    noteContent.value = ''
    await loadTicket()
  } catch (error: any) {
    alert('添加备注失败')
  }
}

function goBack() {
  router.back()
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
  padding: 16px 24px;
  background: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  gap: 12px;
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
  color: #333;
  flex: 1;
  text-align: center;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.content {
  padding: 24px;
  max-width: 900px;
  margin: 0 auto;
}

.section {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.section-title {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: #333;
  border-left: 4px solid #1890ff;
  padding-left: 12px;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.label {
  font-size: 13px;
  color: #999;
}

.value {
  font-size: 15px;
  color: #333;
}

.value.monospace {
  font-family: monospace;
  word-break: break-all;
}

.value.status-pending {
  color: #faad14;
}

.value.status-processing {
  color: #1890ff;
}

.value.status-resolved {
  color: #52c41a;
}

.value.status-closed {
  color: #999;
}

.value.priority-low {
  color: #52c41a;
}

.value.priority-medium {
  color: #faad14;
}

.value.priority-high {
  color: #ff7875;
}

.value.priority-urgent {
  color: #ff4d4f;
}

.description-content {
  font-size: 15px;
  line-height: 1.6;
  color: #333;
  white-space: pre-wrap;
}

.solution-content {
  font-size: 15px;
  line-height: 1.6;
  color: #333;
  white-space: pre-wrap;
  background: #f6ffed;
  padding: 16px;
  border-radius: 6px;
  border: 1px solid #b7eb8f;
}

.session-info {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.logs-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.log-item {
  padding: 12px 16px;
  background: #fafafa;
  border-radius: 6px;
  border-left: 3px solid #d9d9d9;
}

.log-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.log-action {
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.log-time {
  font-size: 13px;
  color: #999;
}

.log-content {
  font-size: 14px;
  color: #666;
  margin-bottom: 6px;
}

.log-meta {
  font-size: 12px;
  color: #999;
}

.actions-section {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  padding: 20px;
  background: #fff;
  border-radius: 8px;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.btn-primary, .btn-success, .btn-secondary, .btn-disabled {
  padding: 12px 24px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  background: #1890ff;
  color: #fff;
}

.btn-primary:hover {
  background: #40a9ff;
}

.btn-success {
  background: #52c41a;
  color: #fff;
}

.btn-success:hover {
  background: #73d13d;
}

.btn-secondary {
  background: #f0f0f0;
  color: #333;
}

.btn-secondary:hover {
  background: #e0e0e0;
}

.btn-disabled {
  background: #f5f5f5;
  color: #ccc;
  cursor: not-allowed;
}

.note-input {
  width: 100%;
  padding: 12px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  font-size: 14px;
  resize: vertical;
  margin-bottom: 12px;
}

.note-input:focus {
  outline: none;
  border-color: #1890ff;
}

.btn-add-note {
  padding: 12px 24px;
  background: #1890ff;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
}

.btn-add-note:hover {
  background: #40a9ff;
}

/* 弹窗样式 */
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
  z-index: 1000;
}

.modal {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  width: 90%;
  max-width: 500px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

.modal h3 {
  margin: 0 0 20px 0;
  font-size: 18px;
  font-weight: 600;
}

.modal-hint {
  font-size: 14px;
  color: #666;
  margin-bottom: 16px;
}

.modal-info {
  padding: 16px;
  background: #f5f5f5;
  border-radius: 6px;
  margin-bottom: 16px;
}

.modal-info p {
  margin: 8px 0;
  font-size: 14px;
  color: #666;
}

.modal-info strong {
  color: #333;
}

.modal-form label {
  display: block;
  margin-bottom: 16px;
  font-size: 14px;
}

.modal-form label.required::before {
  content: '* ';
  color: #ff4d4f;
}

.modal-form input,
.modal-form textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  font-size: 14px;
  font-family: inherit;
  box-sizing: border-box;
}

.modal-form textarea {
  resize: vertical;
  min-height: 80px;
}

.modal-form input:focus,
.modal-form textarea:focus {
  outline: none;
  border-color: #1890ff;
}

.modal-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.btn-cancel {
  padding: 10px 20px;
  background: #f0f0f0;
  color: #333;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.btn-cancel:hover {
  background: #e0e0e0;
}

.btn-confirm {
  padding: 10px 20px;
  background: #1890ff;
  color: #fff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.btn-confirm:hover {
  background: #40a9ff;
}

.btn-warning {
  background: #faad14 !important;
}

.btn-warning:hover {
  background: #ffc53d !important;
}
</style>
