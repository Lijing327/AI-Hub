<template>
  <div class="tickets-page">
    <div class="header">
      <button class="btn-back" @click="goBack">←</button>
      <h2>我的工单</h2>
      <div></div>
    </div>

    <div class="filter-bar">
      <select v-model="selectedStatus" class="status-filter" @change="loadTickets">
        <option value="">全部状态</option>
        <option value="pending">待处理</option>
        <option value="processing">处理中</option>
        <option value="resolved">已解决</option>
        <option value="closed">已关闭</option>
      </select>
      <input v-model="keyword" type="text" placeholder="搜索标题/描述..." class="search-input" @keyup.enter="loadTickets" />
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
            <span class="value priority" :class="'p-' + ticket.priority">{{ priorityToCn(ticket.priority) }}</span>
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
import { getTicketList, type TicketListItem } from '@/api/tickets'

const router = useRouter()

const tickets = ref<TicketListItem[]>([])
const loading = ref(false)
const selectedStatus = ref<string>('')
const keyword = ref('')
const pageIndex = ref(1)
const pageSize = 20
const totalCount = ref(0)

const totalPages = computed(() => Math.ceil(totalCount.value / pageSize) || 1)

onMounted(() => {
  loadTickets()
})

async function loadTickets() {
  loading.value = true
  try {
    const res = await getTicketList({
      status: selectedStatus.value || undefined,
      pageIndex: pageIndex.value,
      pageSize,
      keyword: keyword.value.trim() || undefined
    })
    tickets.value = res.items
    totalCount.value = res.totalCount
  } catch (err) {
    console.error('加载工单列表失败:', err)
    tickets.value = []
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

function formatTime(timeStr: string): string {
  const date = new Date(timeStr)
  return date.toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

function viewTicket(ticketId: string) {
  router.push(`/ticket/${ticketId}`)
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
  router.push('/chat')
}
</script>

<style scoped>
.tickets-page {
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

.filter-bar {
  padding: 12px 16px;
  background: #fff;
  border-bottom: 1px solid #e0e0e0;
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.status-filter {
  width: 120px;
  padding: 10px;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  font-size: 14px;
  background: #fff;
}

.search-input {
  flex: 1;
  min-width: 120px;
  padding: 10px 12px;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  font-size: 14px;
}

.btn-search {
  padding: 10px 16px;
  background: #18a058;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
}

.ticket-list {
  padding: 16px;
}

.ticket-item {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: all 0.3s;
}

.ticket-item:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
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
}

.ticket-info {
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}

.info-row {
  font-size: 13px;
  margin-bottom: 6px;
}

.info-row:last-child {
  margin-bottom: 0;
}

.label {
  color: #666;
}

.value {
  color: #333;
}

.value.priority {
  font-weight: 500;
}

.value.priority.p-low { color: #52c41a; }
.value.priority.p-medium { color: #faad14; }
.value.priority.p-high { color: #ff7875; }
.value.priority.p-urgent { color: #ff4d4f; }

.loading-state {
  text-align: center;
  padding: 24px;
  color: #999;
}

.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 16px;
  background: #fff;
}

.pagination button {
  padding: 8px 16px;
  border: 1px solid #d9d9d9;
  background: #fff;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.pagination button:disabled {
  color: #ccc;
  cursor: not-allowed;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #999;
}
</style>
