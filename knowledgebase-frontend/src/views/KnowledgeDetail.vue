<template>
  <div class="knowledge-detail" v-loading="loading">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>知识条目详情</span>
          <div>
            <el-button @click="handleEdit">编辑</el-button>
            <el-button
              type="success"
              v-if="item && item.status !== 'published'"
              @click="handlePublish"
            >
              发布
            </el-button>
            <el-button @click="handleBack">返回</el-button>
          </div>
        </div>
      </template>

      <div v-if="item" class="detail-content">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="ID">{{ item.id }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(item.status)">
              {{ getStatusText(item.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="标题" :span="2">
            {{ item.title }}
          </el-descriptions-item>
          <el-descriptions-item label="创建人">{{ item.createdBy || '-' }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">
            {{ formatDate(item.createdAt) }}
          </el-descriptions-item>
          <el-descriptions-item label="更新时间">
            {{ item.updatedAt ? formatDate(item.updatedAt) : '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="发布时间">
            {{ item.publishedAt ? formatDate(item.publishedAt) : '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="标签" :span="2">
            {{ item.tags || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="适用范围" :span="2">
            <div v-if="item.scopeJson" class="scope-display">
              <el-tag
                v-for="(value, key) in parseScopeJson(item.scopeJson)"
                :key="key"
                style="margin-right: 8px; margin-bottom: 5px"
              >
                {{ key }}: {{ value }}
              </el-tag>
            </div>
            <span v-else>-</span>
          </el-descriptions-item>
        </el-descriptions>

        <el-divider />

        <div class="content-section">
          <h3>问题描述</h3>
          <div class="content-text">{{ item.questionText || '-' }}</div>
        </div>

        <div class="content-section">
          <h3>原因分析</h3>
          <div class="content-text">{{ item.causeText || '-' }}</div>
        </div>

        <div class="content-section">
          <h3>解决方案</h3>
          <div class="content-text">{{ item.solutionText || '-' }}</div>
        </div>

        <el-divider />

        <div class="content-section">
          <h3>附件</h3>
          <div v-if="item.assets && item.assets.length > 0" class="attachments">
            <div
              v-for="att in item.assets"
              :key="att.id"
              class="attachment-item"
            >
              <el-link :href="getFileUrl(att.fileUrl || att.url)" target="_blank" type="primary">
                <el-icon><Document /></el-icon>
                {{ att.fileName }}
              </el-link>
              <span class="file-info">
                ({{ att.fileType }} / {{ formatFileSize(att.fileSize || att.size) }})
              </span>
              <!-- 图片预览 -->
              <div v-if="att.fileType === 'image' || att.assetType === 'image'" class="image-preview">
                <el-image
                  :src="getFileUrl(att.fileUrl || att.url)"
                  :preview-src-list="getImagePreviewList(item.assets)"
                  fit="cover"
                  style="width: 200px; height: 200px; margin-top: 10px;"
                  :lazy="true"
                  loading="lazy"
                  @error="handleImageError"
                >
                  <template #error>
                    <div class="image-error">
                      <el-icon><Picture /></el-icon>
                      <span>图片加载失败</span>
                      <div style="font-size: 12px; margin-top: 4px; word-break: break-all;">
                        {{ getFileUrl(att.fileUrl || att.url) || att.fileUrl || att.url || 'URL为空' }}
                      </div>
                    </div>
                  </template>
                </el-image>
              </div>
            </div>
          </div>
          <div v-else class="no-attachments">暂无附件</div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Document, Picture } from '@element-plus/icons-vue'
import { knowledgeApi } from '../api/knowledge'
import { getAttachmentDisplayUrl } from '../utils/attachment'
import type { KnowledgeItemDto, AttachmentDto } from '../types/knowledge'

const router = useRouter()
const route = useRoute()

const loading = ref(false)
const item = ref<KnowledgeItemDto | null>(null)

// 加载数据
const loadData = async () => {
  loading.value = true
  try {
    const id = Number(route.params.id)
    item.value = await knowledgeApi.getById(id)
  } catch (error: any) {
    ElMessage.error('加载数据失败: ' + (error.message || '未知错误'))
    router.back()
  } finally {
    loading.value = false
  }
}

// 编辑
const handleEdit = () => {
  if (item.value) {
    router.push(`/knowledge/edit/${item.value.id}`)
  }
}

// 发布
const handlePublish = async () => {
  if (!item.value) return

  try {
    await ElMessageBox.confirm('确定要发布该知识条目吗？', '提示', {
      type: 'warning'
    })
    await knowledgeApi.publish(item.value.id)
    ElMessage.success('发布成功')
    loadData()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('发布失败: ' + (error.message || '未知错误'))
    }
  }
}

// 返回
const handleBack = () => {
  router.back()
}

// 工具方法
const getStatusType = (status: string) => {
  const map: Record<string, string> = {
    draft: 'info',
    published: 'success',
    archived: 'warning'
  }
  return map[status] || 'info'
}

const getStatusText = (status: string) => {
  const map: Record<string, string> = {
    draft: '草稿',
    published: '已发布',
    archived: '已归档'
  }
  return map[status] || status
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString('zh-CN')
}

// 解析适用范围 JSON 为对象
const parseScopeJson = (jsonStr: string | null | undefined): Record<string, string> => {
  if (!jsonStr || jsonStr.trim() === '') {
    return {}
  }
  try {
    return JSON.parse(jsonStr)
  } catch {
    return {}
  }
}

const formatFileSize = (bytes: number) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
}

const getFileUrl = getAttachmentDisplayUrl

// 获取所有图片的预览列表
const getImagePreviewList = (attachments: AttachmentDto[] | undefined): string[] => {
  if (!attachments) return []
  return attachments
    .filter(att => att.fileType === 'image' || att.assetType === 'image')
    .map(att => getFileUrl(att.fileUrl || att.url))
    .filter(url => url) // 过滤掉空URL
}

// 图片加载错误处理
const handleImageError = (_error: unknown) => {
  const assets = item.value?.assets
  const imageAsset = assets?.find((a: AttachmentDto) => a.fileType === 'image' || a.assetType === 'image')
  console.error('图片加载失败')
  console.error('原始URL:', imageAsset?.fileUrl ?? imageAsset?.url)
  console.error('处理后的URL:', imageAsset ? getFileUrl(imageAsset.fileUrl ?? imageAsset.url) : 'N/A')
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.knowledge-detail {
  max-width: 1200px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.detail-content {
  padding: 20px 0;
}

.content-section {
  margin-bottom: 30px;
}

.content-section h3 {
  margin-bottom: 10px;
  color: #409eff;
}

.content-text {
  white-space: pre-wrap;
  line-height: 1.8;
  color: #606266;
  padding: 15px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.attachments {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.attachment-item {
  padding: 10px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
}

.file-info {
  margin-left: 10px;
  color: #909399;
  font-size: 12px;
}

.image-preview {
  margin-top: 10px;
}

.image-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  color: #909399;
  font-size: 14px;
}

.image-error .el-icon {
  font-size: 48px;
  margin-bottom: 8px;
}

.no-attachments {
  color: #909399;
  font-style: italic;
}

pre {
  margin: 0;
  padding: 10px;
  background-color: #f5f7fa;
  border-radius: 4px;
  overflow-x: auto;
}

.scope-display {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
}
</style>
