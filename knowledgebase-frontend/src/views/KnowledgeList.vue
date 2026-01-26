<template>
  <div class="knowledge-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>知识条目列表</span>
          <div>
            <el-button type="success" @click="showImportDialog = true" style="margin-right: 10px">
              <el-icon><Upload /></el-icon>
              导入 Excel
            </el-button>
            <el-button type="primary" @click="handleCreate">
              <el-icon><Plus /></el-icon>
              新建知识条目
            </el-button>
          </div>
        </div>
      </template>

      <!-- 搜索和过滤 -->
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="关键词">
          <el-input
            v-model="searchForm.keyword"
            placeholder="搜索标题/问题/解决方案"
            clearable
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="全部" clearable>
            <el-option label="草稿" value="draft" />
            <el-option label="已发布" value="published" />
            <el-option label="已归档" value="archived" />
          </el-select>
        </el-form-item>
        <el-form-item label="标签">
          <el-input
            v-model="searchForm.tag"
            placeholder="标签"
            clearable
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 表格 -->
      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="tags" label="标签" width="150" show-overflow-tooltip />
        <el-table-column prop="createdBy" label="创建人" width="120" />
        <el-table-column prop="createdAt" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.createdAt) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleDetail(row.id)">详情</el-button>
            <el-button link type="primary" @click="handleEdit(row.id)">编辑</el-button>
            <el-button
              link
              type="success"
              v-if="row.status !== 'published'"
              @click="handlePublish(row.id)"
            >
              发布
            </el-button>
            <el-button link type="danger" @click="handleDelete(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination">
        <el-pagination
          v-model:current-page="pagination.pageIndex"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <!-- Excel 导入对话框 -->
    <el-dialog
      v-model="showImportDialog"
      title="导入 Excel"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-upload
        ref="uploadRef"
        :auto-upload="false"
        :on-change="handleFileChange"
        :file-list="fileList"
        accept=".xlsx"
        :limit="1"
        drag
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">
          将 Excel 文件拖到此处，或<em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            只能上传 .xlsx 格式的 Excel 文件
            <br />
            Excel 文件需包含以下列：设备型号、故障现象（必需），报警信息、原因分析、处理方法（可选）
          </div>
        </template>
      </el-upload>

      <div v-if="importResult" class="import-result" style="margin-top: 20px">
        <el-alert
          :type="importResult.failure_count > 0 ? 'warning' : 'success'"
          :title="`导入完成：成功 ${importResult.success_count} 条，失败 ${importResult.failure_count} 条`"
          :closable="false"
          show-icon
        />
        <div v-if="importResult.failures && importResult.failures.length > 0" style="margin-top: 10px">
          <el-collapse>
            <el-collapse-item title="查看失败详情" name="failures">
              <div v-for="(failure, index) in importResult.failures" :key="index" style="margin-bottom: 8px">
                <el-text type="danger">第 {{ failure.row_index }} 行：{{ failure.reason }}</el-text>
              </div>
            </el-collapse-item>
          </el-collapse>
        </div>
        <div v-if="importResult.article_ids && importResult.article_ids.length > 0" style="margin-top: 10px">
          <el-button type="primary" @click="handleBatchPublish">批量发布已导入的知识</el-button>
        </div>
      </div>

      <template #footer>
        <el-button @click="handleCancelImport">取消</el-button>
        <el-button type="primary" @click="handleImport" :loading="importing" :disabled="!selectedFile">
          开始导入
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Upload, UploadFilled } from '@element-plus/icons-vue'
import { knowledgeApi } from '../api/knowledge'
import { apiConfig } from '../config/api'
import type { KnowledgeItemDto, SearchKnowledgeItemDto } from '../types/knowledge'
import type { UploadFile, UploadFiles } from 'element-plus'

const router = useRouter()

const loading = ref(false)
const tableData = ref<KnowledgeItemDto[]>([])
const searchForm = ref<SearchKnowledgeItemDto>({
  keyword: '',
  status: '',
  tag: '',
  pageIndex: 1,
  pageSize: 20
})
const pagination = ref({
  pageIndex: 1,
  pageSize: 20,
  total: 0
})

// 加载数据
const loadData = async () => {
  loading.value = true
  try {
    const params = {
      ...searchForm.value,
      pageIndex: pagination.value.pageIndex,
      pageSize: pagination.value.pageSize
    }
    const result = await knowledgeApi.search(params)
    tableData.value = result.items
    pagination.value.total = result.totalCount
  } catch (error: any) {
    ElMessage.error('加载数据失败: ' + (error.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

// 搜索
const handleSearch = () => {
  pagination.value.pageIndex = 1
  loadData()
}

// 重置
const handleReset = () => {
  searchForm.value = {
    keyword: '',
    status: '',
    tag: '',
    pageIndex: 1,
    pageSize: 20
  }
  pagination.value.pageIndex = 1
  loadData()
}

// 分页
const handlePageChange = (page: number) => {
  pagination.value.pageIndex = page
  loadData()
}

const handleSizeChange = (size: number) => {
  pagination.value.pageSize = size
  pagination.value.pageIndex = 1
  loadData()
}

// 操作
const handleCreate = () => {
  router.push('/knowledge/create')
}

const handleDetail = (id: number) => {
  router.push(`/knowledge/detail/${id}`)
}

const handleEdit = (id: number) => {
  router.push(`/knowledge/edit/${id}`)
}

const handlePublish = async (id: number) => {
  try {
    await ElMessageBox.confirm('确定要发布该知识条目吗？', '提示', {
      type: 'warning'
    })
    await knowledgeApi.publish(id)
    ElMessage.success('发布成功')
    loadData()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('发布失败: ' + (error.message || '未知错误'))
    }
  }
}

const handleDelete = async (id: number) => {
  try {
    await ElMessageBox.confirm('确定要删除该知识条目吗？', '提示', {
      type: 'warning'
    })
    await knowledgeApi.delete(id)
    ElMessage.success('删除成功')
    loadData()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败: ' + (error.message || '未知错误'))
    }
  }
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

// Excel 导入相关
const showImportDialog = ref(false)
const uploadRef = ref()
const fileList = ref<UploadFile[]>([])
const selectedFile = ref<File | null>(null)
const importing = ref(false)
const importResult = ref<any>(null)

const handleFileChange = (file: UploadFile, files: UploadFiles) => {
  selectedFile.value = file.raw as File
  importResult.value = null
}

const handleImport = async () => {
  if (!selectedFile.value) {
    ElMessage.warning('请先选择 Excel 文件')
    return
  }

  if (!selectedFile.value.name.endsWith('.xlsx')) {
    ElMessage.error('只能上传 .xlsx 格式的 Excel 文件')
    return
  }

  importing.value = true
  importResult.value = null

  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)

    const response = await fetch(`${apiConfig.pythonApiBaseUrl}/import/excel`, {
      method: 'POST',
      body: formData
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || '导入失败')
    }

    const result = await response.json()
    importResult.value = result

    if (result.success_count > 0) {
      ElMessage.success(`成功导入 ${result.success_count} 条知识条目`)
      // 刷新列表
      loadData()
    } else {
      ElMessage.warning('没有成功导入任何知识条目')
    }
  } catch (error: any) {
    ElMessage.error('导入失败: ' + (error.message || '未知错误'))
  } finally {
    importing.value = false
  }
}

const handleCancelImport = () => {
  showImportDialog.value = false
  fileList.value = []
  selectedFile.value = null
  importResult.value = null
  uploadRef.value?.clearFiles()
}

const handleBatchPublish = async () => {
  if (!importResult.value || !importResult.value.article_ids || importResult.value.article_ids.length === 0) {
    ElMessage.warning('没有可发布的知识条目')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要批量发布 ${importResult.value.article_ids.length} 条知识条目吗？`,
      '批量发布',
      {
        type: 'warning'
      }
    )

    const response = await fetch('/api/ai/kb/articles/publish/batch', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Tenant-Id': apiConfig.defaultTenant,
        'X-Internal-Token': apiConfig.internalToken
      },
      body: JSON.stringify({
        articleIds: importResult.value.article_ids
      })
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.message || '批量发布失败')
    }

    const result = await response.json()
    ElMessage.success(`成功发布 ${result.successCount} 条知识条目`)
    
    // 刷新列表
    loadData()
    handleCancelImport()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('批量发布失败: ' + (error.message || '未知错误'))
    }
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.knowledge-list {
  max-width: 1400px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.search-form {
  margin-bottom: 20px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
