<template>
  <div class="ai-answer-card">
    <div class="card-header">
      <div class="header-left">
        <span class="ai-icon">🤖</span>
        <span class="category">{{ meta.issueCategory }}</span>
        <span v-if="meta.alarmCode" class="alarm-code">{{ meta.alarmCode }}</span>
      </div>
      <div class="confidence">置信度: {{ Math.round(meta.confidence * 100) }}%</div>
    </div>

    <div class="card-body">
      <!-- 可能原因 -->
      <div class="section">
        <div class="section-title">可能原因</div>
        <ul class="causes-list">
          <li v-for="(cause, index) in meta.topCauses" :key="index">{{ cause }}</li>
        </ul>
      </div>

      <!-- 排查步骤 -->
      <div class="section">
        <div class="section-title">排查步骤</div>
        <div class="steps-list">
          <div v-for="(step, index) in meta.steps" :key="index" class="step-item">
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

      <!-- 安全提示 -->
      <div class="safety-tip">
        {{ meta.safetyTip }}
      </div>

      <!-- 参考知识 -->
      <div class="section" v-if="meta.citedDocs.length > 0">
        <div class="section-title">参考知识</div>
        <div class="cited-docs">
          <div v-for="doc in meta.citedDocs" :key="doc.kbId" class="cited-doc">
            <div class="doc-title">{{ doc.title }}</div>
            <div class="doc-excerpt">{{ doc.excerpt }}</div>
          </div>
        </div>
      </div>
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
import { defineProps, defineEmits, withDefaults } from 'vue'
import type { AIResponseMeta } from '@/models/types'

interface Props {
  meta: AIResponseMeta
  solution: {
    temporary: string
    final: string
  }
  readonly?: boolean // 只读模式，用于会话详情页
}

const props = withDefaults(defineProps<Props>(), {
  readonly: false
})

const emit = defineEmits<{
  createTicket: []
  feedback: [isResolved: boolean]
}>()

function handleCreateTicket() {
  emit('createTicket')
}

function handleFeedback(isResolved: boolean) {
  emit('feedback', isResolved)
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
