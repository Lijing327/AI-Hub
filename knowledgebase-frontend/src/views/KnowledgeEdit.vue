<template>
  <div class="knowledge-edit">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>{{ isEdit ? '编辑知识条目' : '新建知识条目' }}</span>
        </div>
      </template>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="120px"
        class="edit-form"
      >
        <el-form-item label="标题" prop="title">
          <el-input v-model="form.title" placeholder="请输入标题" />
        </el-form-item>

        <el-form-item label="问题描述" prop="questionText">
          <el-input
            v-model="form.questionText"
            type="textarea"
            :rows="4"
            placeholder="请输入问题描述"
          />
        </el-form-item>

        <el-form-item label="原因分析" prop="causeText">
          <el-input
            v-model="form.causeText"
            type="textarea"
            :rows="4"
            placeholder="请输入原因分析"
          />
        </el-form-item>

        <el-form-item label="解决方案" prop="solutionText">
          <el-input
            v-model="form.solutionText"
            type="textarea"
            :rows="6"
            placeholder="请输入解决方案"
          />
        </el-form-item>

        <el-form-item label="适用范围" prop="scopeJson">
          <div class="scope-input">
            <div
              v-for="(item, index) in scopeItems"
              :key="index"
              class="scope-item"
            >
              <el-input
                v-model="item.key"
                placeholder="字段名（如：地区、产品）"
                class="scope-key"
                style="width: 200px; margin-right: 10px"
              />
              <el-input
                v-model="item.value"
                placeholder="字段值（如：华东、产品A）"
                class="scope-value"
                style="width: 300px; margin-right: 10px"
              />
              <el-button
                type="danger"
                :icon="Delete"
                circle
                @click="removeScopeItem(index)"
                v-if="scopeItems.length > 1"
              />
            </div>
            <el-button
              type="primary"
              :icon="Plus"
              text
              @click="addScopeItem"
              style="margin-top: 10px"
            >
              添加字段
            </el-button>
            <div class="scope-tip">
              提示：可以添加多个字段，例如：地区=华东，产品=产品A
            </div>
          </div>
        </el-form-item>

        <el-form-item label="标签" prop="tags">
          <el-input
            v-model="form.tags"
            placeholder="多个标签用逗号分隔"
          />
        </el-form-item>

        <el-form-item label="附件">
          <el-upload
            ref="uploadRef"
            :action="uploadAction"
            :data="uploadData"
            :on-success="handleUploadSuccess"
            :on-remove="handleRemove"
            :file-list="fileList"
            :before-upload="beforeUpload"
            list-type="picture-card"
            :limit="10"
          >
            <el-icon><Plus /></el-icon>
          </el-upload>
          <div class="upload-tip">
            支持图片、视频、PDF文件，单个文件不超过50MB
          </div>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSubmit" :loading="submitting">
            保存
          </el-button>
          <el-button @click="handleCancel">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElUpload, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Delete } from '@element-plus/icons-vue'
import { knowledgeApi, attachmentApi } from '../api/knowledge'
import type { KnowledgeItemDto, CreateKnowledgeItemDto, UpdateKnowledgeItemDto } from '../types/knowledge'

const router = useRouter()
const route = useRoute()

const formRef = ref<FormInstance>()
const uploadRef = ref<InstanceType<typeof ElUpload>>()
const submitting = ref(false)
const knowledgeItemId = ref<number | null>(null)
const isEdit = computed(() => !!route.params.id)

const form = reactive<CreateKnowledgeItemDto & UpdateKnowledgeItemDto>({
  title: '',
  questionText: '',
  causeText: '',
  solutionText: '',
  scopeJson: '',
  tags: ''
})

// 适用范围键值对列表
interface ScopeItem {
  key: string
  value: string
}

const scopeItems = ref<ScopeItem[]>([{ key: '', value: '' }])

// 将 scopeItems 转换为 JSON 字符串
const updateScopeJson = () => {
  const scopeObj: Record<string, string> = {}
  scopeItems.value.forEach(item => {
    if (item.key && item.value) {
      scopeObj[item.key.trim()] = item.value.trim()
    }
  })
  form.scopeJson = Object.keys(scopeObj).length > 0 ? JSON.stringify(scopeObj) : ''
}

// 监听 scopeItems 变化，自动更新 scopeJson
watch(
  scopeItems,
  () => {
    updateScopeJson()
  },
  { deep: true }
)

// 添加适用范围字段
const addScopeItem = () => {
  scopeItems.value.push({ key: '', value: '' })
}

// 删除适用范围字段
const removeScopeItem = (index: number) => {
  if (scopeItems.value.length > 1) {
    scopeItems.value.splice(index, 1)
  }
}

// 从 JSON 字符串解析为 scopeItems
const parseScopeJson = (jsonStr: string | null | undefined) => {
  if (!jsonStr || jsonStr.trim() === '') {
    scopeItems.value = [{ key: '', value: '' }]
    return
  }

  try {
    const obj = JSON.parse(jsonStr)
    const items: ScopeItem[] = []
    for (const key in obj) {
      if (obj.hasOwnProperty(key)) {
        items.push({ key: key, value: String(obj[key]) })
      }
    }
    scopeItems.value = items.length > 0 ? items : [{ key: '', value: '' }]
  } catch (e) {
    // 如果解析失败，保持默认值
    scopeItems.value = [{ key: '', value: '' }]
  }
}

const rules: FormRules = {
  title: [{ required: true, message: '请输入标题', trigger: 'blur' }]
}

const fileList = ref<any[]>([])
const uploadAction = computed(() => {
  if (!knowledgeItemId.value) return ''
  return `/api/attachments/upload`
})

const uploadData = computed(() => ({
  knowledgeItemId: knowledgeItemId.value
}))

// 加载数据
const loadData = async () => {
  if (!isEdit.value) return

  try {
    const id = Number(route.params.id)
    const item = await knowledgeApi.getById(id)
    knowledgeItemId.value = item.id
    form.title = item.title
    form.questionText = item.questionText || ''
    form.causeText = item.causeText || ''
    form.solutionText = item.solutionText || ''
    form.scopeJson = item.scopeJson || ''
    form.tags = item.tags || ''

    // 解析适用范围 JSON 为键值对列表
    parseScopeJson(item.scopeJson)

    // 加载附件
    if (item.attachments) {
      fileList.value = item.attachments.map(att => ({
        uid: att.id,
        name: att.fileName,
        url: att.fileUrl,
        response: { id: att.id }
      }))
    }
  } catch (error: any) {
    ElMessage.error('加载数据失败: ' + (error.message || '未知错误'))
    router.back()
  }
}

// 上传前验证
const beforeUpload = (file: File) => {
  if (!knowledgeItemId.value) {
    ElMessage.warning('请先保存知识条目，然后再上传附件')
    return false
  }

  const isValidType = ['image', 'video', 'application/pdf'].some(type =>
    file.type.startsWith(type)
  )
  const isLt50M = file.size / 1024 / 1024 < 50

  if (!isValidType) {
    ElMessage.error('只能上传图片、视频或PDF文件!')
    return false
  }
  if (!isLt50M) {
    ElMessage.error('文件大小不能超过50MB!')
    return false
  }
  return true
}

// 上传成功
const handleUploadSuccess = (response: any) => {
  ElMessage.success('上传成功')
  knowledgeItemId.value = response.knowledgeItemId
}

// 删除附件
const handleRemove = async (file: any) => {
  if (file.response?.id) {
    try {
      await attachmentApi.delete(file.response.id)
      ElMessage.success('删除成功')
    } catch (error: any) {
      ElMessage.error('删除失败: ' + (error.message || '未知错误'))
    }
  }
}

// 提交
const handleSubmit = async () => {
  if (!formRef.value) return

  // 提交前更新 scopeJson
  updateScopeJson()

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    submitting.value = true
    try {
      if (isEdit.value) {
        const id = Number(route.params.id)
        await knowledgeApi.update(id, form)
        ElMessage.success('更新成功')
        router.push('/knowledge')
      } else {
        // 新建时先创建知识条目
        const result = await knowledgeApi.create({
          ...form,
          createdBy: 'admin', // TODO: 从用户上下文获取
          tenantId: 'default' // TODO: 从用户上下文获取
        })
        knowledgeItemId.value = result.id
        ElMessage.success('创建成功，现在可以上传附件了')
        // 不跳转，让用户可以继续上传附件
      }
    } catch (error: any) {
      ElMessage.error('保存失败: ' + (error.message || '未知错误'))
    } finally {
      submitting.value = false
    }
  })
}

// 取消
const handleCancel = () => {
  router.back()
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.knowledge-edit {
  max-width: 1200px;
  margin: 0 auto;
}

.edit-form {
  max-width: 800px;
}

.upload-tip {
  color: #909399;
  font-size: 12px;
  margin-top: 5px;
}

.scope-input {
  width: 100%;
}

.scope-item {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}

.scope-tip {
  color: #909399;
  font-size: 12px;
  margin-top: 8px;
}
</style>
