<template>
  <div class="conversation-detail">
    <!-- 返回按钮 -->
    <div class="back-bar">
      <button class="btn-back" @click="goBack">← 返回列表</button>
    </div>

    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="!conversation" class="error">会话不存在或加载失败</div>
    
    <template v-else>
      <!-- 会话基本信息 -->
      <div class="info-card">
        <h2>会话信息</h2>
        <div class="info-grid">
          <div class="info-item">
            <label>会话 ID</label>
            <span class="value">{{ conversation.conversationId }}</span>
          </div>
          <div class="info-item">
            <label>用户</label>
            <span class="value">{{ conversation.userId || '匿名用户' }}</span>
          </div>
          <div class="info-item">
            <label>渠道</label>
            <span :class="['channel-tag', `channel-${conversation.channel}`]">
              {{ conversation.channel }}
            </span>
          </div>
          <div class="info-item">
            <label>开始时间</label>
            <span class="value">{{ formatDateTime(conversation.startedAt) }}</span>
          </div>
          <div class="info-item">
            <label>结束时间</label>
            <span class="value">{{ conversation.endedAt ? formatDateTime(conversation.endedAt) : '进行中' }}</span>
          </div>
          <div class="info-item">
            <label>消息数</label>
            <span class="value">{{ conversation.messages.length }}</span>
          </div>
        </div>
      </div>

      <!-- 对话回放 -->
      <div class="main-content">
        <!-- 左侧：消息时间线 -->
        <div class="message-timeline">
          <h3>对话记录</h3>
          <div class="messages">
            <div
              v-for="msg in conversation.messages"
              :key="msg.messageId"
              :class="['message-item', `role-${msg.role}`, { selected: selectedMessageId === msg.messageId }]"
              @click="selectMessage(msg.messageId)"
            >
              <div class="message-header">
                <span class="role-tag">{{ msg.role === 'user' ? '用户' : msg.role === 'assistant' ? 'AI' : '系统' }}</span>
                <span class="time">{{ formatTime(msg.createdAt) }}</span>
              </div>
              <div class="message-content">{{ msg.content }}</div>
            </div>
          </div>
        </div>

        <!-- 右侧：选中消息的详情 -->
        <div class="detail-panel">
          <template v-if="selectedMessage">
            <h3>消息详情</h3>
            
            <!-- 决策信息 -->
            <div class="detail-section" v-if="selectedMessage.decision">
              <h4>AI 决策</h4>
              <div class="detail-grid">
                <div class="detail-item">
                  <label>意图类型</label>
                  <span :class="['intent-tag', `intent-${selectedMessage.decision.intentType}`]">
                    {{ formatIntent(selectedMessage.decision.intentType) }}
                  </span>
                </div>
                <div class="detail-item">
                  <label>置信度</label>
                  <span class="value">
                    <span class="confidence-bar" :style="{ width: `${selectedMessage.decision.confidence * 100}%` }"></span>
                    {{ (selectedMessage.decision.confidence * 100).toFixed(1) }}%
                  </span>
                </div>
                <div class="detail-item">
                  <label>模型</label>
                  <span class="value">{{ selectedMessage.decision.modelName || '-' }}</span>
                </div>
                <div class="detail-item">
                  <label>Prompt 版本</label>
                  <span class="value">{{ selectedMessage.decision.promptVersion || '-' }}</span>
                </div>
                <div class="detail-item">
                  <label>使用知识库</label>
                  <span :class="selectedMessage.decision.useKnowledge ? 'yes' : 'no'">
                    {{ selectedMessage.decision.useKnowledge ? '是' : '否' }}
                  </span>
                </div>
                <div class="detail-item" v-if="selectedMessage.decision.fallbackReason">
                  <label>兜底原因</label>
                  <span class="fallback-reason">{{ selectedMessage.decision.fallbackReason }}</span>
                </div>
                <div class="detail-item" v-if="selectedMessage.decision.tokensIn">
                  <label>Token 消耗</label>
                  <span class="value">
                    输入: {{ selectedMessage.decision.tokensIn }} / 输出: {{ selectedMessage.decision.tokensOut || 0 }}
                  </span>
                </div>
              </div>
            </div>

            <!-- 检索结果 -->
            <div class="detail-section" v-if="selectedMessage.retrievals && selectedMessage.retrievals.length > 0">
              <h4>命中文档 (Top {{ selectedMessage.retrievals.length }})</h4>
              <div class="retrieval-list">
                <div 
                  v-for="ret in selectedMessage.retrievals" 
                  :key="ret.docId"
                  class="retrieval-item"
                >
                  <div class="rank">#{{ ret.rank }}</div>
                  <div class="doc-info">
                    <div class="doc-title">{{ ret.docTitle || `文档 ${ret.docId}` }}</div>
                    <div class="doc-id">ID: {{ ret.docId }}</div>
                  </div>
                  <div class="score">
                    <span class="score-bar" :style="{ width: `${ret.score * 100}%` }"></span>
                    {{ (ret.score * 100).toFixed(1) }}%
                  </div>
                </div>
              </div>
            </div>

            <!-- 响应信息 -->
            <div class="detail-section" v-if="selectedMessage.response">
              <h4>响应信息</h4>
              <div class="detail-grid">
                <div class="detail-item">
                  <label>响应状态</label>
                  <span :class="selectedMessage.response.isSuccess ? 'success' : 'error'">
                    {{ selectedMessage.response.isSuccess ? '成功' : '失败' }}
                  </span>
                </div>
                <div class="detail-item">
                  <label>响应耗时</label>
                  <span class="value">{{ selectedMessage.response.responseTimeMs }}ms</span>
                </div>
                <div class="detail-item" v-if="selectedMessage.response.errorType">
                  <label>错误类型</label>
                  <span class="error-type">{{ selectedMessage.response.errorType }}</span>
                </div>
                <div class="detail-item full-width" v-if="selectedMessage.response.errorDetail">
                  <label>错误详情</label>
                  <pre class="error-detail">{{ selectedMessage.response.errorDetail }}</pre>
                </div>
              </div>
            </div>

            <!-- 无详情 -->
            <div class="no-details" v-if="!selectedMessage.decision && !selectedMessage.response && (!selectedMessage.retrievals || selectedMessage.retrievals.length === 0)">
              <p>该消息暂无详细记录</p>
            </div>
          </template>
          
          <div class="select-hint" v-else>
            <p>点击左侧消息查看详情</p>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getConversationDetail, type ConversationDetail, type MessageDetail } from '@/api/audit'

const route = useRoute()
const router = useRouter()

// 状态
const loading = ref(true)
const conversation = ref<ConversationDetail | null>(null)
const selectedMessageId = ref<string | null>(null)

// 选中的消息
const selectedMessage = computed<MessageDetail | null>(() => {
  if (!conversation.value || !selectedMessageId.value) return null
  return conversation.value.messages.find(m => m.messageId === selectedMessageId.value) || null
})

// 加载数据
async function loadData() {
  const conversationId = route.params.id as string
  if (!conversationId) {
    router.push('/audit')
    return
  }

  loading.value = true
  try {
    conversation.value = await getConversationDetail(conversationId)
    // 默认选中第一条消息
    if (conversation.value.messages.length > 0) {
      selectedMessageId.value = conversation.value.messages[0].messageId
    }
  } catch (error) {
    console.error('加载会话详情失败:', error)
    conversation.value = null
  } finally {
    loading.value = false
  }
}

// 选择消息
function selectMessage(messageId: string) {
  selectedMessageId.value = messageId
}

// 返回
function goBack() {
  router.push('/audit')
}

// 格式化
function formatDateTime(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

function formatTime(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

function formatIntent(intent: string): string {
  const map: Record<string, string> = {
    chat: '闲聊',
    capability: '能力咨询',
    solution: '故障解决'
  }
  return map[intent] || intent
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.conversation-detail {
  padding: 24px;
  max-width: 1600px;
  margin: 0 auto;
}

.back-bar {
  margin-bottom: 16px;
}

.btn-back {
  padding: 8px 16px;
  background: #fff;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.btn-back:hover {
  border-color: #1890ff;
  color: #1890ff;
}

.loading,
.error {
  text-align: center;
  padding: 60px;
  color: #999;
  font-size: 16px;
}

.info-card {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.info-card h2 {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin: 0 0 16px 0;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-item label {
  font-size: 12px;
  color: #999;
}

.info-item .value {
  font-size: 14px;
  color: #333;
}

.channel-tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.channel-web { background: #e6f7ff; color: #1890ff; }
.channel-H5 { background: #fff7e6; color: #fa8c16; }
.channel-app { background: #f6ffed; color: #52c41a; }
.channel-wechat { background: #d9f7be; color: #389e0d; }

.main-content {
  display: grid;
  grid-template-columns: 1fr 400px;
  gap: 16px;
}

.message-timeline {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.message-timeline h3 {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin: 0 0 16px 0;
}

.messages {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 600px;
  overflow-y: auto;
}

.message-item {
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  border: 2px solid transparent;
}

.message-item.role-user {
  background: #f0f5ff;
}

.message-item.role-assistant {
  background: #f6ffed;
}

.message-item.role-system {
  background: #f5f5f5;
}

.message-item:hover {
  border-color: #1890ff;
}

.message-item.selected {
  border-color: #1890ff;
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.2);
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.role-tag {
  font-size: 12px;
  font-weight: 500;
  padding: 2px 8px;
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.05);
}

.time {
  font-size: 12px;
  color: #999;
}

.message-content {
  font-size: 14px;
  color: #333;
  line-height: 1.6;
  word-break: break-word;
}

.detail-panel {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  max-height: 700px;
  overflow-y: auto;
}

.detail-panel h3 {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin: 0 0 16px 0;
}

.detail-section {
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f0f0f0;
}

.detail-section:last-child {
  border-bottom: none;
  margin-bottom: 0;
}

.detail-section h4 {
  font-size: 14px;
  font-weight: 600;
  color: #333;
  margin: 0 0 12px 0;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.detail-item.full-width {
  grid-column: 1 / -1;
}

.detail-item label {
  font-size: 12px;
  color: #999;
}

.detail-item .value {
  font-size: 14px;
  color: #333;
}

.intent-tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.intent-chat { background: #f0f5ff; color: #2f54eb; }
.intent-solution { background: #fff2e8; color: #fa541c; }

.confidence-bar,
.score-bar {
  display: inline-block;
  height: 4px;
  background: #18a058;
  border-radius: 2px;
  margin-right: 8px;
}

.yes { color: #52c41a; }
.no { color: #999; }
.success { color: #52c41a; }
.error { color: #f5222d; }

.fallback-reason {
  color: #fa8c16;
  background: #fff7e6;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.error-type {
  color: #f5222d;
  background: #fff1f0;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.error-detail {
  background: #fff1f0;
  padding: 8px;
  border-radius: 4px;
  font-size: 12px;
  color: #f5222d;
  overflow-x: auto;
  margin: 0;
}

.retrieval-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.retrieval-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px;
  background: #fafafa;
  border-radius: 4px;
}

.retrieval-item .rank {
  font-weight: 600;
  color: #1890ff;
  min-width: 30px;
}

.retrieval-item .doc-info {
  flex: 1;
}

.retrieval-item .doc-title {
  font-size: 13px;
  color: #333;
}

.retrieval-item .doc-id {
  font-size: 11px;
  color: #999;
}

.retrieval-item .score {
  font-size: 12px;
  color: #52c41a;
  display: flex;
  align-items: center;
  min-width: 80px;
}

.select-hint,
.no-details {
  text-align: center;
  padding: 40px;
  color: #999;
}

@media (max-width: 1200px) {
  .main-content {
    grid-template-columns: 1fr;
  }
  
  .detail-panel {
    max-height: none;
  }
}
</style>
