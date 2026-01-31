<template>
  <div class="conversation-list">
    <div class="page-header">
      <h1>AI 对话审计</h1>
      <p class="subtitle">查看和审计所有 AI 对话记录</p>
    </div>

    <!-- 筛选条件 -->
    <div class="filter-section">
      <div class="filter-row">
        <div class="filter-item">
          <label>时间范围</label>
          <input type="date" v-model="filters.startFrom" />
          <span class="separator">至</span>
          <input type="date" v-model="filters.startTo" />
        </div>
        <div class="filter-item">
          <label>渠道</label>
          <select v-model="filters.channel">
            <option value="">全部</option>
            <option value="web">Web</option>
            <option value="H5">H5</option>
            <option value="app">App</option>
            <option value="wechat">微信</option>
          </select>
        </div>
        <div class="filter-item">
          <label>意图类型</label>
          <select v-model="filters.intentType">
            <option value="">全部</option>
            <option value="chat">闲聊</option>
            <option value="capability">能力咨询</option>
            <option value="solution">故障解决</option>
          </select>
        </div>
        <div class="filter-item">
          <label>是否兜底</label>
          <select v-model="filters.hasFallback">
            <option value="">全部</option>
            <option value="true">是</option>
            <option value="false">否</option>
          </select>
        </div>
        <button class="btn-search" @click="loadData">搜索</button>
        <button class="btn-reset" @click="resetFilters">重置</button>
      </div>
    </div>

    <!-- 数据表格 -->
    <div class="table-section">
      <table class="data-table">
        <thead>
          <tr>
            <th>开始时间</th>
            <th>用户</th>
            <th>渠道</th>
            <th>轮次</th>
            <th>主要意图</th>
            <th>是否兜底</th>
            <th>平均耗时</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="8" class="loading-cell">加载中...</td>
          </tr>
          <tr v-else-if="conversations.length === 0">
            <td colspan="8" class="empty-cell">暂无数据</td>
          </tr>
          <tr v-for="item in conversations" :key="item.conversationId">
            <td>{{ formatDateTime(item.startedAt) }}</td>
            <td>{{ item.userId || '-' }}</td>
            <td>
              <span :class="['channel-tag', `channel-${item.channel}`]">
                {{ item.channel }}
              </span>
            </td>
            <td>{{ item.messageCount }}</td>
            <td>
              <span :class="['intent-tag', `intent-${item.mainIntent}`]">
                {{ formatIntent(item.mainIntent) }}
              </span>
            </td>
            <td>
              <span :class="['fallback-tag', item.hasFallback ? 'fallback-yes' : 'fallback-no']">
                {{ item.hasFallback ? '是' : '否' }}
              </span>
            </td>
            <td>{{ item.avgResponseTimeMs ? `${item.avgResponseTimeMs}ms` : '-' }}</td>
            <td>
              <button class="btn-detail" @click="viewDetail(item.conversationId)">
                查看详情
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 分页 -->
    <div class="pagination" v-if="totalPages > 1">
      <button :disabled="currentPage <= 1" @click="goToPage(currentPage - 1)">上一页</button>
      <span class="page-info">第 {{ currentPage }} / {{ totalPages }} 页，共 {{ totalCount }} 条</span>
      <button :disabled="currentPage >= totalPages" @click="goToPage(currentPage + 1)">下一页</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getConversationList, type ConversationListItem } from '@/api/audit'

const router = useRouter()

// 状态
const loading = ref(false)
const conversations = ref<ConversationListItem[]>([])
const totalCount = ref(0)
const totalPages = ref(0)
const currentPage = ref(1)
const pageSize = 20

// 筛选条件
const filters = ref({
  startFrom: '',
  startTo: '',
  channel: '',
  intentType: '',
  hasFallback: ''
})

// 加载数据
async function loadData() {
  loading.value = true
  try {
    const result = await getConversationList({
      startFrom: filters.value.startFrom || undefined,
      startTo: filters.value.startTo || undefined,
      channel: filters.value.channel || undefined,
      intentType: filters.value.intentType || undefined,
      hasFallback: filters.value.hasFallback ? filters.value.hasFallback === 'true' : undefined,
      page: currentPage.value,
      pageSize: pageSize
    })
    conversations.value = result.items
    totalCount.value = result.totalCount
    totalPages.value = result.totalPages
  } catch (error) {
    console.error('加载数据失败:', error)
    alert('加载数据失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

// 重置筛选
function resetFilters() {
  filters.value = {
    startFrom: '',
    startTo: '',
    channel: '',
    intentType: '',
    hasFallback: ''
  }
  currentPage.value = 1
  loadData()
}

// 分页
function goToPage(page: number) {
  currentPage.value = page
  loadData()
}

// 查看详情
function viewDetail(conversationId: string) {
  router.push(`/audit/conversation/${conversationId}`)
}

// 格式化
function formatDateTime(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function formatIntent(intent?: string): string {
  const map: Record<string, string> = {
    chat: '闲聊',
    capability: '能力咨询',
    solution: '故障解决'
  }
  return intent ? (map[intent] || intent) : '-'
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.conversation-list {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h1 {
  font-size: 24px;
  font-weight: 600;
  color: #333;
  margin: 0 0 8px 0;
}

.subtitle {
  color: #666;
  font-size: 14px;
  margin: 0;
}

.filter-section {
  background: #fff;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.filter-row {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  align-items: flex-end;
}

.filter-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.filter-item label {
  font-size: 13px;
  color: #666;
}

.filter-item input,
.filter-item select {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  min-width: 120px;
}

.separator {
  margin: 0 8px;
  color: #999;
}

.btn-search,
.btn-reset {
  padding: 8px 20px;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-search {
  background: #18a058;
  color: #fff;
}

.btn-search:hover {
  background: #159050;
}

.btn-reset {
  background: #f5f5f5;
  color: #666;
}

.btn-reset:hover {
  background: #e8e8e8;
}

.table-section {
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th,
.data-table td {
  padding: 12px 16px;
  text-align: left;
  border-bottom: 1px solid #f0f0f0;
}

.data-table th {
  background: #fafafa;
  font-weight: 500;
  color: #333;
  font-size: 13px;
}

.data-table td {
  font-size: 14px;
  color: #333;
}

.loading-cell,
.empty-cell {
  text-align: center;
  padding: 40px;
  color: #999;
}

.channel-tag,
.intent-tag,
.fallback-tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.channel-web { background: #e6f7ff; color: #1890ff; }
.channel-H5 { background: #fff7e6; color: #fa8c16; }
.channel-app { background: #f6ffed; color: #52c41a; }
.channel-wechat { background: #d9f7be; color: #389e0d; }

.intent-chat { background: #f0f5ff; color: #2f54eb; }
.intent-solution { background: #fff2e8; color: #fa541c; }

.fallback-yes { background: #fff1f0; color: #f5222d; }
.fallback-no { background: #f6ffed; color: #52c41a; }

.btn-detail {
  padding: 4px 12px;
  background: #1890ff;
  color: #fff;
  border: none;
  border-radius: 4px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-detail:hover {
  background: #40a9ff;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  margin-top: 16px;
  padding: 16px;
}

.pagination button {
  padding: 8px 16px;
  background: #fff;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.pagination button:hover:not(:disabled) {
  border-color: #1890ff;
  color: #1890ff;
}

.pagination button:disabled {
  background: #f5f5f5;
  color: #999;
  cursor: not-allowed;
}

.page-info {
  color: #666;
  font-size: 14px;
}
</style>
