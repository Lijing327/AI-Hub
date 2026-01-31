<template>
  <div class="audit-stats">
    <div class="page-header">
      <h1>AI 统计报表</h1>
      <p class="subtitle">对话效果统计分析，驱动知识库持续优化</p>
    </div>

    <!-- 时间筛选 -->
    <div class="filter-section">
      <div class="filter-row">
        <div class="filter-item">
          <label>统计时间范围</label>
          <input type="date" v-model="filters.startFrom" />
          <span class="separator">至</span>
          <input type="date" v-model="filters.startTo" />
        </div>
        <button class="btn-search" @click="loadAllData">查询</button>
        <button class="btn-reset" @click="resetFilters">本月</button>
      </div>
    </div>

    <!-- 概览卡片 -->
    <div class="overview-cards">
      <div class="stat-card">
        <div class="stat-value">{{ overview.totalConversations || 0 }}</div>
        <div class="stat-label">总会话数</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ overview.totalMessages || 0 }}</div>
        <div class="stat-label">总消息数</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ overview.avgResponseTimeMs || 0 }}ms</div>
        <div class="stat-label">平均响应时间</div>
      </div>
      <div class="stat-card">
        <div class="stat-value" :class="{ warning: (overview.successRate || 0) < 95 }">{{ overview.successRate || 0 }}%</div>
        <div class="stat-label">成功率</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ overview.knowledgeUsageRate || 0 }}%</div>
        <div class="stat-label">知识库使用率</div>
      </div>
      <div class="stat-card">
        <div class="stat-value" :class="{ danger: (overview.fallbackRate || 0) > 20 }">{{ overview.fallbackRate || 0 }}%</div>
        <div class="stat-label">兜底率</div>
      </div>
    </div>
    
    <!-- 无数据提示 -->
    <div class="no-data-hint" v-if="overview.totalConversations === 0">
      <p>📊 暂无统计数据</p>
      <p class="hint-text">当用户通过客服页面进行对话后，这里会自动显示统计信息。<br/>请先确保：</p>
      <ol class="hint-list">
        <li>已执行 <code>005_CreateAiAuditTables.sql</code> 创建审计表</li>
        <li>.NET 和 Python 服务都已启动</li>
        <li>Python 的 <code>.env</code> 中 <code>ENABLE_AUDIT_LOG=true</code></li>
        <li>用户在客服页面发送了消息</li>
      </ol>
    </div>

    <!-- 详细统计 -->
    <div class="stats-grid">
      <!-- Top 意图 -->
      <div class="stats-section">
        <h3>Top 意图分布</h3>
        <div class="chart-placeholder" v-if="!topIntents || topIntents.length === 0">暂无数据</div>
        <div class="bar-list" v-else>
          <div v-for="item in topIntents" :key="item.intentType || 'unknown'" class="bar-item">
            <div class="bar-label">{{ formatIntent(item.intentType) }}</div>
            <div class="bar-container">
              <div class="bar-fill" :style="{ width: `${item.percentage || 0}%` }"></div>
            </div>
            <div class="bar-value">{{ item.count || 0 }} ({{ item.percentage || 0 }}%)</div>
          </div>
        </div>
      </div>

      <!-- Top 命中文档 -->
      <div class="stats-section">
        <h3>Top 命中文档</h3>
        <div class="chart-placeholder" v-if="!topDocs || topDocs.length === 0">暂无数据</div>
        <table class="simple-table" v-else>
          <thead>
            <tr>
              <th>排名</th>
              <th>文档标题</th>
              <th>命中次数</th>
              <th>平均分</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(doc, index) in topDocs" :key="doc.docId || index">
              <td>{{ index + 1 }}</td>
              <td>{{ doc.docTitle || (doc.docId ? `ID: ${doc.docId}` : '未知文档') }}</td>
              <td>{{ doc.hitCount || 0 }}</td>
              <td>{{ formatScore(doc.avgScore) }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 无命中问题 -->
      <div class="stats-section full-width">
        <h3>无命中问题清单 <span class="hint">（用于驱动知识库补充）</span></h3>
        <div class="chart-placeholder" v-if="noMatchQuestions.length === 0">暂无无命中问题</div>
        <table class="simple-table" v-else>
          <thead>
            <tr>
              <th style="width: 150px;">时间</th>
              <th>用户问题</th>
              <th style="width: 120px;">兜底原因</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="q in noMatchQuestions" :key="q.messageId">
              <td>{{ formatDateTime(q.createdAt) }}</td>
              <td class="question-cell">{{ q.question }}</td>
              <td>
                <span class="fallback-tag">{{ formatFallbackReason(q.fallbackReason) }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import {
  getStatsOverview,
  getTopIntents,
  getTopDocs,
  getNoMatchQuestions,
  type StatsOverview,
  type IntentStat,
  type DocHitStat,
  type NoMatchQuestion
} from '@/api/audit'

// 状态
const overview = ref<StatsOverview>({
  totalConversations: 0,
  totalMessages: 0,
  fallbackRate: 0,
  lowConfidenceRate: 0,
  avgResponseTimeMs: 0,
  successRate: 0,
  knowledgeUsageRate: 0
})
const topIntents = ref<IntentStat[]>([])
const topDocs = ref<DocHitStat[]>([])
const noMatchQuestions = ref<NoMatchQuestion[]>([])

// 筛选条件（默认本月）
const filters = ref({
  startFrom: getFirstDayOfMonth(),
  startTo: getTodayDate()
})

// 工具函数
function getFirstDayOfMonth(): string {
  const now = new Date()
  return new Date(now.getFullYear(), now.getMonth(), 1).toISOString().split('T')[0]
}

function getTodayDate(): string {
  return new Date().toISOString().split('T')[0]
}

// 加载数据
async function loadAllData() {
  const query = {
    startFrom: filters.value.startFrom || undefined,
    startTo: filters.value.startTo || undefined
  }

  try {
    const [overviewData, intentsData, docsData, noMatchData] = await Promise.all([
      getStatsOverview(query),
      getTopIntents(query, 10),
      getTopDocs(query, 10),
      getNoMatchQuestions(query, 50)
    ])

    overview.value = overviewData
    topIntents.value = intentsData
    topDocs.value = docsData
    noMatchQuestions.value = noMatchData
  } catch (error) {
    console.error('加载统计数据失败:', error)
    alert('加载统计数据失败，请稍后重试')
  }
}

function resetFilters() {
  filters.value = {
    startFrom: getFirstDayOfMonth(),
    startTo: getTodayDate()
  }
  loadAllData()
}

// 格式化
function formatIntent(intent: string): string {
  const map: Record<string, string> = {
    chat: '闲聊',
    capability: '能力咨询',
    solution: '故障解决'
  }
  return map[intent] || intent
}

function formatFallbackReason(reason?: string): string {
  const map: Record<string, string> = {
    no_match: '无命中',
    low_confidence: '低置信度',
    model_error: '模型异常'
  }
  return reason ? (map[reason] || reason) : '-'
}

function formatDateTime(dateStr: string): string {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function formatScore(score: number | undefined | null): string {
  if (score === undefined || score === null || isNaN(score)) return '-'
  return `${(score * 100).toFixed(1)}%`
}

onMounted(() => {
  loadAllData()
})
</script>

<style scoped>
.audit-stats {
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
  align-items: center;
  gap: 8px;
}

.filter-item label {
  font-size: 13px;
  color: #666;
}

.filter-item input {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.separator {
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

.overview-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  text-align: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  color: #333;
  margin-bottom: 8px;
}

.stat-value.warning {
  color: #fa8c16;
}

.stat-value.danger {
  color: #f5222d;
}

.stat-label {
  font-size: 13px;
  color: #999;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.stats-section {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.stats-section.full-width {
  grid-column: 1 / -1;
}

.stats-section h3 {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin: 0 0 16px 0;
}

.stats-section h3 .hint {
  font-size: 12px;
  color: #999;
  font-weight: normal;
}

.chart-placeholder {
  text-align: center;
  padding: 40px;
  color: #999;
}

.bar-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.bar-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.bar-label {
  min-width: 80px;
  font-size: 13px;
  color: #333;
}

.bar-container {
  flex: 1;
  height: 20px;
  background: #f5f5f5;
  border-radius: 4px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #18a058, #36d399);
  border-radius: 4px;
  transition: width 0.3s;
}

.bar-value {
  min-width: 80px;
  font-size: 12px;
  color: #666;
  text-align: right;
}

.simple-table {
  width: 100%;
  border-collapse: collapse;
}

.simple-table th,
.simple-table td {
  padding: 10px 12px;
  text-align: left;
  border-bottom: 1px solid #f0f0f0;
  font-size: 13px;
}

.simple-table th {
  background: #fafafa;
  font-weight: 500;
  color: #333;
}

.simple-table td {
  color: #333;
}

.question-cell {
  max-width: 400px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.fallback-tag {
  display: inline-block;
  padding: 2px 8px;
  background: #fff7e6;
  color: #fa8c16;
  border-radius: 4px;
  font-size: 12px;
}

.no-data-hint {
  background: #fffbe6;
  border: 1px solid #ffe58f;
  border-radius: 8px;
  padding: 24px;
  margin-bottom: 24px;
  text-align: center;
}

.no-data-hint p {
  margin: 0 0 12px 0;
  font-size: 16px;
  color: #333;
}

.no-data-hint .hint-text {
  font-size: 14px;
  color: #666;
}

.no-data-hint .hint-list {
  text-align: left;
  display: inline-block;
  margin: 12px 0 0 0;
  padding-left: 20px;
  color: #666;
  font-size: 14px;
}

.no-data-hint .hint-list li {
  margin-bottom: 8px;
}

.no-data-hint code {
  background: #f5f5f5;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: monospace;
  font-size: 13px;
}

@media (max-width: 900px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>
