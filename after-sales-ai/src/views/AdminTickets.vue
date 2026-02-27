<template>
  <div class="admin-tickets-page">
    <div class="header">
      <button class="btn-back" @click="goBack">←</button>
      <h2>工单管理</h2>
      <div></div>
    </div>

    <div class="tabs-bar">
      <button
        v-for="tab in tabs"
        :key="tab.value"
        class="tab-btn"
        :class="{ active: selectedStatus === tab.value }"
        @click="selectTab(tab.value)"
      >
        {{ tab.label }}
      </button>
    </div>

    <div class="filter-bar">
      <input
        v-model="keyword"
        type="text"
        placeholder="搜索标题/描述..."
        class="search-input"
        @keyup.enter="loadTickets"
      />
      <button class="btn-search" @click="loadTickets">搜索</button>
    </div>

    <div class="ticket-list">
      <div
        v-for="ticket in tickets"
        :key="ticket.ticketId"
        class="ticket-item"
        @click="viewTicket(ticket.ticketId)"
      >
        <div class="ticket-header">
          <div class="ticket-title">{{ ticket.title }}</div>
          <TicketStatusTag :status="statusToCn(ticket.status)" />
        </div>
        <div class="ticket-info">
          <div class="info-row">
            <span class="label">工单号：</span>
            <span class="value">{{ ticket.ticketNo }}</span>
          </div>
          <div class="info-row">
            <span class="label">优先级：</span>
            <span class="value priority" :class="getPriorityClass(ticket.priority)">
              {{ getPriorityText(ticket.priority) }}
            </span>
          </div>
          <div class="info-row">
            <span class="label">负责人：</span>
            <span class="value">{{ ticket.assigneeName || '未分配' }}</span>
          </div>
          <div class="info-row">
            <span class="label">创建时间：</span>
            <span class="value">{{ formatTime(ticket.createdAt) }}</span>
          </div>
        </div>
      </div>

      <div v-if="loading" class="loading-state">加载中...</div>
      <div v-else-if="tickets.length === 0" class="empty-state">
        <p>暂无工单</p>
      </div>
    </div>

    <div v-if="totalCount > 0" class="pagination">
      <button @click="prevPage" :disabled="pageIndex <= 1">上一页</button>
      <span class="page-info">{{ pageIndex }} / {{ totalPages }}</span>
      <button @click="nextPage" :disabled="pageIndex >= totalPages">下一页</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import TicketStatusTag from '@/components/TicketStatusTag.vue'
import api from '@/utils/api'

const router = useRouter()

interface TicketListDto {
  ticketId: string
  ticketNo: string
  title: string
  status: string
  priority: string
  source: string
  deviceMn?: string
  assigneeName?: string
  createdBy: string
  createdAt: string
}

interface ApiResponse<T> {
  items: T[]
  totalCount: number
  pageIndex: number
  pageSize: number
}

const tabs = [
  { value: 'pending', label: '待处理' },
  { value: 'processing', label: '处理中' },
  { value: 'resolved', label: '已解决' },
  { value: 'closed', label: '已关闭' }
]

const tickets = ref<TicketListDto[]>([])
const loading = ref(false)
const selectedStatus = ref<string>('pending')
const keyword = ref<string>('')
const pageIndex = ref(1)
const pageSize = 20
const totalCount = ref(0)

const totalPages = computed(() => Math.ceil(totalCount.value / pageSize) || 1)

onMounted(() => {
  loadTickets()
})

function selectTab(value: string) {
  selectedStatus.value = value
  pageIndex.value = 1
  loadTickets()
}

async function loadTickets() {
  loading.value = true
  try {
    const response = await api.get<ApiResponse<TicketListDto>>('admin/tickets', {
      params: {
        pageIndex: pageIndex.value,
        pageSize,
        status: selectedStatus.value || undefined,
        keyword: keyword.value.trim() || undefined
      }
    })
    tickets.value = response.data.items
    totalCount.value = response.data.totalCount
  } catch (error: unknown) {
    console.error('加载工单列表失败:', error)
    const err = error as { response?: { data?: { message?: string } } }
    alert(err?.response?.data?.message || '加载失败')
    tickets.value = []
  } finally {
    loading.value = false
  }
}

function statusToCn(s: string): string {
  const map: Record<string, string> = { pending: '待处理', processing: '处理中', resolved: '已解决', closed: '已关闭' }
  return map[s] || s
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
  const map: Record<string, string> = {
    low: '低',
    medium: '中',
    high: '高',
    urgent: '紧急'
  }
  return map[priority] || priority
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

function viewTicket(ticketId: string) {
  router.push(`/admin/ticket/${ticketId}`)
}

function prevPage() {
  if (pageIndex.value > 1) {
    pageIndex.value--
    loadTickets()
  }
}

function nextPage() {
  if (pageIndex.value < totalPages.value) {
    pageIndex.value++
    loadTickets()
  }
}

function goBack() {
  router.push('/admin')
}
</script>

<style scoped>
.admin-tickets-page {
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
  font-size: 20px;
  font-weight: 600;
  color: #333;
}

.tabs-bar {
  display: flex;
  gap: 8px;
  padding: 12px 24px;
  background: #fff;
  border-bottom: 1px solid #e0e0e0;
}

.tab-btn {
  padding: 8px 16px;
  border: 1px solid #d9d9d9;
  background: #fff;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
}

.tab-btn.active {
  background: #1890ff;
  color: #fff;
  border-color: #1890ff;
}

.filter-bar {
  padding: 12px 24px;
  background: #fff;
  border-bottom: 1px solid #e0e0e0;
  display: flex;
  gap: 12px;
  align-items: center;
}

.search-input {
  flex: 1;
  max-width: 300px;
  padding: 10px 12px;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  font-size: 14px;
}

.search-input:focus {
  outline: none;
  border-color: #1890ff;
}

.btn-search {
  padding: 10px 16px;
  background: #1890ff;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
}

.loading-state {
  text-align: center;
  padding: 24px;
  color: #999;
}

.ticket-list {
  padding: 24px;
}

.ticket-item {
  background: #fff;
  border-radius: 8px;
  padding: 16px 20px;
  margin-bottom: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  cursor: pointer;
  transition: all 0.2s;
  border-left: 4px solid transparent;
}

.ticket-item:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
  transform: translateY(-1px);
  border-left-color: #1890ff;
}

.ticket-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.ticket-title {
  flex: 1;
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin-right: 12px;
}

.ticket-info {
  padding-top: 10px;
  border-top: 1px solid #f0f0f0;
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}

.info-row {
  font-size: 13px;
  color: #666;
}

.label {
  color: #999;
  margin-right: 4px;
}

.value {
  color: #333;
}

.value.priority {
  font-weight: 500;
}

.value.priority.low { color: #52c41a; }
.value.priority.medium { color: #faad14; }
.value.priority.high { color: #ff7875; }
.value.priority.urgent { color: #ff4d4f; }

.empty-state {
  text-align: center;
  padding: 80px 20px;
  color: #999;
  font-size: 16px;
}

.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 20px;
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid #e0e0e0;
}

.pagination button {
  padding: 8px 16px;
  border: 1px solid #d9d9d9;
  background: #fff;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.pagination button:hover:not(:disabled) {
  color: #1890ff;
  border-color: #1890ff;
}

.pagination button:disabled {
  color: #ccc;
  border-color: #d9d9d9;
  cursor: not-allowed;
}

.page-info {
  font-size: 14px;
  color: #666;
}
</style>
