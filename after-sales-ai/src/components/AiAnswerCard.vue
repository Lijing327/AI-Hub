<template>
  <div class="ai-answer-card">
    <div class="card-header">
      <div class="header-left">
        <span class="ai-icon">🤖</span>
        <span class="category">{{ meta.issueCategory }}</span>
        <span v-if="meta.alarmCode" class="alarm-code">{{ meta.alarmCode }}</span>
      </div>
      <span class="confidence">置信度: {{ Math.round(meta.confidence * 100) }}%</span>
    </div>

    <div class="card-body">
      <!-- 问题列表：第一个为最有可能，仅显示标题；选择后再展开完整回答 -->
      <div class="section" v-if="relatedArticles && relatedArticles.length > 0">
        <div class="section-title">请选择要咨询的问题 ({{ relatedArticles.length }}条)</div>
        <div class="related-articles">
          <div
            v-for="(article, index) in relatedArticles"
            :key="article.id"
            class="related-article title-only"
            :class="{ 'is-selected': answerExpanded, 'is-first': index === 0 }"
            @click="handleSelectQuestion(article, index)"
          >
            <div class="article-title">
              <span v-if="index === 0" class="tag-most-likely">最有可能</span>
              {{ article.title || article.questionText }}
            </div>
          </div>
        </div>
      </div>

      <!-- 用户选择问题后再展示：可能原因、排查步骤、解决方案 -->
      <template v-if="answerExpanded">
        <div v-if="loadingDetail" class="section loading-detail">正在加载该问题详情…</div>
        <template v-else>
          <!-- 可能原因 -->
          <div class="section">
            <div class="section-title">可能原因</div>
            <ul class="causes-list">
              <li v-for="(cause, index) in displayTopCauses" :key="index">{{ cause }}</li>
            </ul>
          </div>

          <!-- 排查步骤 -->
          <div class="section">
            <div class="section-title">排查步骤</div>
            <div class="steps-list">
              <div v-for="(step, index) in displaySteps" :key="index" class="step-item">
              <div class="step-number">{{ index + 1 }}</div>
              <div class="step-content">
                <div class="step-title">{{ step.title }}</div>
                <div class="step-action">操作：{{ step.action }}</div>
                <div class="step-expect">预期：{{ step.expect }}</div>
                <div class="step-next">下一步：{{ step.next }}</div>
              </div>
            </div>
          </div>
        </div>

        <!-- 解决方案 -->
        <div class="section">
          <div class="section-title">解决方案</div>
          <div class="solution-item">
            <div class="solution-label">临时处理：</div>
            <div class="solution-text">{{ solution.temporary }}</div>
          </div>
          <div class="solution-item">
            <div class="solution-label">根本解决：</div>
            <div class="solution-text">{{ solution.final }}</div>
          </div>
        </div>

        <!-- 参考资料：文件或文件夹（来自知识库附件 + 正文「参考xxx」解析） -->
        <div class="section" v-if="technicalResources && technicalResources.length > 0">
          <div class="section-title">参考资料</div>
          <div class="resources-list">
            <component
              v-for="resource in technicalResources"
              :key="`${resource.id}-${resource.name}`"
              :is="resource.url ? 'a' : 'div'"
              :href="resource.url || undefined"
              :target="resource.url ? '_blank' : undefined"
              :class="['resource-item', `resource-${resource.type}`, { 'is-folder': resource.type === 'directory' }]"
            >
              <span class="resource-icon">{{ getResourceIcon(resource.type) }}</span>
              <div class="resource-info">
                <div class="resource-name">{{ resource.name }}</div>
                <div class="resource-meta">
                  <span class="resource-type">{{ getResourceTypeName(resource.type) }}</span>
                  <span v-if="resource.size" class="resource-size">{{ formatFileSize(resource.size) }}</span>
                  <span v-if="resource.duration" class="resource-duration">{{ formatDuration(resource.duration) }}</span>
                </div>
              </div>
              <span class="resource-action">{{ resource.type === 'directory' ? '打开' : '查看' }}</span>
            </component>
          </div>
        </div>
        </template>
      </template>

      <!-- 安全提示 -->
      <div v-if="meta.safetyTip" class="safety-tip">
        {{ meta.safetyTip }}
      </div>

      <!-- 参考知识 -->
      <!-- <div class="section" v-if="meta.citedDocs.length > 0">
        <div class="section-title">参考知识</div>
        <div class="cited-docs">
          <div v-for="doc in meta.citedDocs" :key="doc.kbId" class="cited-doc">
            <div class="doc-title">{{ doc.title }}</div>
            <div class="doc-excerpt">{{ doc.excerpt }}</div>
          </div>
        </div>
      </div> -->

    </div>

    <div class="card-footer" v-if="!readonly">
      <button class="btn btn-primary" @click="handleCreateTicket">生成工单</button>
      <div class="feedback-buttons">
        <button class="btn btn-success" @click="handleFeedback(true)">已解决</button>
        <button class="btn btn-warning" @click="handleFeedback(false)">未解决</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import type { AIResponseMeta, RelatedArticle, TechnicalResource } from '@/models/types'

/** 选中「其他问题」时按需拉取的详情，用于覆盖首条「最有可能」的展示 */
export interface SelectedArticleDetail {
  topCauses: string[]
  steps: Array<{ title?: string; action?: string; expect?: string; next?: string }>
  solution: { temporary: string; final: string }
  technicalResources: TechnicalResource[]
}

interface Props {
  meta: AIResponseMeta
  solution: {
    temporary: string
    final: string
  }
  relatedArticles?: RelatedArticle[] // 其他可能匹配的知识条目
  technicalResources?: TechnicalResource[] // 技术资料（附件）
  /** 点击其他问题时拉取的详情，有则展开区用其 topCauses/steps，solution 与 technicalResources 由父组件通过 solution/technicalResources 传入 */
  selectedDetail?: SelectedArticleDetail | null
  /** 是否正在拉取选中问题详情 */
  loadingDetail?: boolean
  readonly?: boolean // 只读模式，用于会话详情页
}

const props = withDefaults(defineProps<Props>(), {
  readonly: false
})

const emit = defineEmits<{
  createTicket: []
  feedback: [isResolved: boolean]
  selectRelatedQuestion: [article: RelatedArticle]
}>()

// 是否已展开完整回答（用户选择问题后才展开；只读模式如会话详情默认展开）
const answerExpanded = ref(false)
watch(() => props.readonly, (readonly) => { if (readonly) answerExpanded.value = true }, { immediate: true })

// 展开区展示：选中「其他问题」时用 selectedDetail，否则用首条 meta
const displayTopCauses = computed(() => props.selectedDetail?.topCauses ?? props.meta.topCauses ?? [])
const displaySteps = computed(() => props.selectedDetail?.steps ?? props.meta.steps ?? [])

function handleCreateTicket() {
  emit('createTicket')
}

function handleFeedback(isResolved: boolean) {
  emit('feedback', isResolved)
}

function handleSelectQuestion(article: RelatedArticle, _index: number) {
  if (props.readonly) return
  // 展开完整回答（可能原因、排查步骤、解决方案等）；父组件根据是否首条决定直接展示或拉取详情
  answerExpanded.value = true
  emit('selectRelatedQuestion', article)
}

function handleSelectRelatedQuestion(article: RelatedArticle) {
  handleSelectQuestion(article, -1)
}

// 获取资源类型图标（含文件夹）
function getResourceIcon(type: string): string {
  const icons: Record<string, string> = {
    image: '🖼️',
    video: '🎬',
    document: '📄',
    pdf: '📑',
    directory: '📁',
    other: '📎'
  }
  return icons[type] || icons.other
}

// 获取资源类型名称（含文件夹）
function getResourceTypeName(type: string): string {
  const names: Record<string, string> = {
    image: '图片',
    video: '视频',
    document: '文档',
    pdf: 'PDF',
    directory: '文件夹',
    other: '文件'
  }
  return names[type] || names.other
}

// 格式化文件大小
function formatFileSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

// 格式化时长
function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}
</script>

<style scoped>
.ai-answer-card {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  margin-bottom: 16px;
  overflow: hidden;
  animation: slideIn 0.3s;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.ai-icon {
  font-size: 20px;
}

.category {
  font-weight: 600;
  font-size: 15px;
}

.alarm-code {
  background: rgba(255, 255, 255, 0.3);
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.confidence {
  font-size: 12px;
  opacity: 0.9;
}

.card-body {
  padding: 16px;
}

.section {
  margin-bottom: 20px;
}

.section:last-child {
  margin-bottom: 0;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 2px solid #f0f0f0;
}

.causes-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.causes-list li {
  padding: 8px 12px;
  margin-bottom: 6px;
  background: #f8f9fa;
  border-radius: 6px;
  font-size: 14px;
  color: #555;
  position: relative;
  padding-left: 24px;
}

.causes-list li::before {
  content: '•';
  position: absolute;
  left: 12px;
  color: #18a058;
  font-weight: bold;
}

.steps-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.step-item {
  display: flex;
  gap: 12px;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 3px solid #18a058;
}

.step-number {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  background: #18a058;
  color: #fff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 12px;
}

.step-content {
  flex: 1;
}

.step-title {
  font-weight: 600;
  font-size: 14px;
  color: #333;
  margin-bottom: 6px;
}

.step-action,
.step-expect,
.step-next {
  font-size: 13px;
  color: #666;
  margin-bottom: 4px;
  line-height: 1.5;
}

.solution-item {
  margin-bottom: 12px;
  padding: 12px;
  background: #f0f9ff;
  border-radius: 8px;
}

.solution-label {
  font-weight: 600;
  font-size: 14px;
  color: #18a058;
  margin-bottom: 6px;
}

.solution-text {
  font-size: 14px;
  color: #555;
  line-height: 1.6;
}

.safety-tip {
  padding: 12px;
  background: #fff3cd;
  border-left: 4px solid #ffc107;
  border-radius: 6px;
  font-size: 13px;
  color: #856404;
  line-height: 1.6;
  margin-bottom: 20px;
}

.cited-docs {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.cited-doc {
  padding: 12px;
  background: #f8f9fa;
  border-radius: 6px;
  border-left: 3px solid #667eea;
}

.doc-title {
  font-weight: 600;
  font-size: 13px;
  color: #333;
  margin-bottom: 6px;
}

.doc-excerpt {
  font-size: 12px;
  color: #666;
  line-height: 1.5;
}

/* 专业资源样式 */
.resources-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.resource-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: linear-gradient(135deg, #f8f9ff 0%, #f0f4ff 100%);
  border-radius: 8px;
  border: 1px solid #e0e7ff;
  text-decoration: none;
  transition: all 0.3s ease;
  cursor: pointer;
}

.resource-item:hover {
  background: linear-gradient(135deg, #eef2ff 0%, #e0e7ff 100%);
  transform: translateX(4px);
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.15);
}

.resource-icon {
  font-size: 24px;
  flex-shrink: 0;
}

.resource-info {
  flex: 1;
  min-width: 0;
}

.resource-name {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.resource-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #888;
}

.resource-type {
  background: #e0e7ff;
  color: #667eea;
  padding: 2px 8px;
  border-radius: 4px;
}

.resource-directory .resource-type,
.resource-item.is-folder .resource-type {
  background: #e8f5e9;
  color: #18a058;
}

.resource-action {
  font-size: 13px;
  color: #667eea;
  font-weight: 500;
  padding: 6px 12px;
  background: rgba(102, 126, 234, 0.1);
  border-radius: 6px;
  flex-shrink: 0;
}

/* 资源类型特殊样式 */
.resource-image .resource-type {
  background: #e6f7ff;
  color: #1890ff;
}

.resource-video .resource-type {
  background: #fff2e8;
  color: #fa541c;
}

.resource-document .resource-type,
.resource-pdf .resource-type {
  background: #f6ffed;
  color: #52c41a;
}

.related-articles {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 12px;
}

.related-article {
  padding: 12px;
  background: #f0f9ff;
  border-radius: 6px;
  border-left: 3px solid #1890ff;
  cursor: pointer;
  transition: all 0.3s;
}

.related-article.title-only {
  padding: 10px 12px;
}

.related-article.title-only .article-title {
  margin-bottom: 0;
}

.related-article:hover {
  background: #e6f7ff;
  transform: translateX(4px);
}

.article-title {
  font-weight: 600;
  font-size: 14px;
  color: #1890ff;
  margin-bottom: 0;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.tag-most-likely {
  flex-shrink: 0;
  font-size: 11px;
  font-weight: 500;
  color: #18a058;
  background: #e8f5e9;
  padding: 2px 6px;
  border-radius: 4px;
}

.related-article.is-first {
  border-left-color: #18a058;
  background: #f0f9ff;
}

.article-excerpt,
.article-question {
  font-size: 12px;
  color: #666;
  line-height: 1.5;
}

.card-footer {
  padding: 12px 16px;
  background: #f8f9fa;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-primary {
  background: #18a058;
  color: #fff;
}

.btn-primary:hover {
  background: #159050;
}

.btn-success {
  background: #52c41a;
  color: #fff;
  flex: 1;
}

.btn-success:hover {
  background: #45a016;
}

.btn-warning {
  background: #faad14;
  color: #fff;
  flex: 1;
}

.btn-warning:hover {
  background: #d48806;
}

.feedback-buttons {
  display: flex;
  gap: 8px;
  flex: 1;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
