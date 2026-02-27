<template>
  <div class="ticket-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>工单列表</span>
        </div>
      </template>

      <el-radio-group v-model="selectedStatus" @change="onTabChange" class="status-tabs">
        <el-radio-button value="pending">待处理</el-radio-button>
        <el-radio-button value="processing">处理中</el-radio-button>
        <el-radio-button value="resolved">已解决</el-radio-button>
        <el-radio-button value="closed">已关闭</el-radio-button>
      </el-radio-group>

      <el-form :inline="true" class="search-form">
        <el-form-item>
          <el-input
            v-model="keyword"
            placeholder="搜索标题/描述"
            clearable
            @keyup.enter="loadTickets"
            style="width: 200px"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadTickets">搜索</el-button>
        </el-form-item>
      </el-form>

      <el-table :data="tickets" v-loading="loading" stripe @row-click="handleRowClick">
        <el-table-column prop="ticketNo" label="工单号" width="140" />
        <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.status)">{{ statusToCn(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="priority" label="优先级" width="90">
          <template #default="{ row }">
            <el-tag size="small" :type="getPriorityTagType(row.priority)">
              {{ priorityToCn(row.priority) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="assigneeName" label="负责人" width="100">
          <template #default="{ row }">{{ row.assigneeName || '未分配' }}</template>
        </el-table-column>
        <el-table-column prop="createdAt" label="创建时间" width="180">
          <template #default="{ row }">{{ formatTime(row.createdAt) }}</template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-if="totalCount > 0"
        v-model:current-page="pageIndex"
        :page-size="pageSize"
        :total="totalCount"
        layout="prev, pager, next"
        class="pagination"
        @current-change="loadTickets"
      />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ticketApi, type TicketListItem } from '@/api/tickets'

const router = useRouter()

const tickets = ref<TicketListItem[]>([])
const loading = ref(false)
const selectedStatus = ref('pending')
const keyword = ref('')
const pageIndex = ref(1)
const pageSize = ref(20)
const totalCount = ref(0)

onMounted(() => loadTickets())

function onTabChange() {
  pageIndex.value = 1
  loadTickets()
}

async function loadTickets() {
  loading.value = true
  try {
    const res = await ticketApi.list({
      status: selectedStatus.value,
      pageIndex: pageIndex.value,
      pageSize: pageSize.value,
      keyword: keyword.value.trim() || undefined
    })
    tickets.value = res.items
    totalCount.value = res.totalCount
  } catch (err) {
    console.error('加载工单失败:', err)
    tickets.value = []
    const e = err as { response?: { data?: { message?: string } } }
    ElMessage.error(e?.response?.data?.message || '加载失败')
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

function getStatusTagType(s: string): string {
  const map: Record<string, string> = { pending: 'warning', processing: 'primary', resolved: 'success', closed: 'info' }
  return map[s] || 'info'
}

function getPriorityTagType(p: string): string {
  const map: Record<string, string> = { low: 'success', medium: '', high: 'warning', urgent: 'danger' }
  return map[p] || ''
}

function formatTime(s: string): string {
  return new Date(s).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function handleRowClick(row: TicketListItem) {
  router.push(`/tickets/${row.ticketId}`)
}
</script>

<style scoped>
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.status-tabs {
  margin-bottom: 16px;
}

.search-form {
  margin-bottom: 16px;
}

.pagination {
  margin-top: 16px;
  justify-content: flex-end;
}

.el-table {
  cursor: pointer;
}
</style>
