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
          <el-input 
            v-model="form.title" 
            placeholder="【设备/系统】出现【现象】（附加关键信息）例如：【造型机】启动后无法进入自动模式" 
            maxlength="500"
            show-word-limit
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :icon="Plus" @click="insertTemplate">
            插入标准模板
          </el-button>
          <span class="template-tip">点击后自动填充标准模板骨架（不覆盖已有内容）</span>
        </el-form-item>

        <el-form-item label="问题描述" prop="questionText">
          <el-input
            v-model="form.questionText"
            type="textarea"
            :rows="6"
            placeholder="【发生场景】在什么情况下出现（启动时/运行中/停机后/切换模式时）&#10;【具体表现】设备/系统具体表现出的异常现象&#10;【报警信息】是否有报警码、提示信息、界面截图（如有请写明）&#10;【影响范围】是否影响生产/是否可以临时运行"
          />
        </el-form-item>

        <el-form-item label="原因分析" prop="causeText">
          <el-input
            v-model="form.causeText"
            type="textarea"
            :rows="5"
            placeholder="原因 1：&#10;原因 2：&#10;原因 3：&#10;&#10;提示：每一条原因是一个完整判断，按概率从高到低排列"
          />
        </el-form-item>

        <el-form-item label="解决方案" prop="solutionText">
          <el-input
            v-model="form.solutionText"
            type="textarea"
            :rows="8"
            placeholder="步骤 1：&#10;步骤 2：&#10;步骤 3：&#10;&#10;提示：强制要求一步一行，每个检查动作后可配图片/视频"
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
                placeholder="字段名（如：设备型号、系统版本、控制系统）"
                class="scope-key"
                style="width: 200px; margin-right: 10px"
              />
              <el-input
                v-model="item.value"
                placeholder="字段值（如：XXX-100、V2.3、西门子S7-1200）"
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
              提示：结构化填写，便于后期筛选。例如：设备型号=XXX-100，系统版本=V2.3，控制系统=西门子S7-1200
            </div>
          </div>
        </el-form-item>

        <el-form-item label="标签" prop="tags">
          <el-input
            v-model="form.tags"
            type="textarea"
            :rows="2"
            placeholder="多个标签用逗号或回车分隔，例如：造型机, 自动模式, 安全门, 无报警&#10;推荐：设备类型、现象类型、关键部件、报警码（3-6个）"
            @blur="normalizeTags"
          />
          <div class="tags-tip">
            已输入标签：<el-tag v-for="tag in tagList" :key="tag" size="small" style="margin-right: 5px;">{{ tag }}</el-tag>
            <span v-if="tagList.length === 0" style="color: #909399;">（无）</span>
          </div>
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
          <el-button type="success" @click="handlePublish" :loading="submitting" :disabled="!isEdit">
            发布
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
import { ElMessage, ElMessageBox, ElUpload, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Delete } from '@element-plus/icons-vue'
import { knowledgeApi, attachmentApi } from '../api/knowledge'
import type { CreateKnowledgeItemDto, UpdateKnowledgeItemDto, AttachmentDto } from '../types/knowledge'

const router = useRouter()
const route = useRoute()

const formRef = ref<FormInstance>()
// 模板中 el-upload 的 ref，用于上传组件引用（模板 ref="uploadRef" 绑定）
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

// 标签列表（计算属性）
const tagList = computed(() => {
  const tagsStr = form.tags ?? ''
  if (!tagsStr.trim()) return []
  return tagsStr
    .split(/[,\n\r]+/)
    .map(tag => tag.trim())
    .filter(tag => tag.length > 0)
    .filter((tag, index, arr) => arr.indexOf(tag) === index) // 去重
})

// 规范化标签（去重、去空格）
const normalizeTags = () => {
  const tagsStr = form.tags ?? ''
  if (!tagsStr.trim()) {
    form.tags = ''
    return
  }

  const tags = tagsStr
    .split(/[,\n\r]+/)
    .map(tag => tag.trim())
    .filter(tag => tag.length > 0)
    .filter((tag, index, arr) => arr.indexOf(tag) === index) // 去重
  
  form.tags = tags.join(', ')
}

// 插入标准模板
const insertTemplate = async () => {
  // 检查是否有非空内容
  const hasContent =
    (form.questionText ?? '').trim() !== '' ||
    (form.causeText ?? '').trim() !== '' ||
    (form.solutionText ?? '').trim() !== '' ||
    scopeItems.value.some(item => item.key.trim() !== '' || item.value.trim() !== '') ||
    (form.tags ?? '').trim() !== ''

  if (hasContent) {
    try {
      await ElMessageBox.confirm(
        '检测到已有内容，插入模板可能会覆盖部分字段。是否继续？',
        '确认操作',
        {
          confirmButtonText: '继续',
          cancelButtonText: '取消',
          type: 'warning'
        }
      )
    } catch {
      return // 用户取消
    }
  }

  // 插入模板（不覆盖已有非空内容）
  if ((form.questionText ?? '').trim() === '') {
    form.questionText = '【发生场景】\n【具体表现】\n【报警信息】\n【影响范围】'
  }

  if ((form.causeText ?? '').trim() === '') {
    form.causeText = '原因 1：\n原因 2：\n原因 3：'
  }

  if ((form.solutionText ?? '').trim() === '') {
    form.solutionText = '步骤 1：\n步骤 2：\n步骤 3：'
  }

  // 适用范围：如果为空，添加常用字段
  if (scopeItems.value.length === 1 && scopeItems.value[0].key.trim() === '' && scopeItems.value[0].value.trim() === '') {
    scopeItems.value = [
      { key: '设备型号', value: '' },
      { key: '系统版本', value: '' },
      { key: '控制系统', value: '' }
    ]
  }

  if ((form.tags ?? '').trim() === '') {
    form.tags = ''
  }

  ElMessage.success('模板已插入，请根据实际情况填写')
}

// 发布前检查
const validateBeforePublish = (): string[] => {
  const warnings: string[] = []

  // 检查标题长度
  if (form.title.trim().length < 10) {
    warnings.push('标题过短（建议至少10个字符），可能影响检索效果')
  }

  // 检查解决步骤数量
  const solutionText = form.solutionText ?? ''
  if (solutionText.trim()) {
    // 匹配 "步骤 X：" 或 "步骤X：" 格式
    const stepMatches = solutionText.match(/步骤\s*\d+[：:]/gi)
    const stepCount = stepMatches ? stepMatches.length : 0
    if (stepCount < 3) {
      warnings.push(`解决步骤少于3条（当前${stepCount}条），建议至少3条以确保完整性`)
    }
  } else {
    warnings.push('解决步骤为空，建议填写至少3条步骤')
  }

  // 检查标签数量
  if (tagList.value.length < 3) {
    warnings.push(`标签少于3个（当前${tagList.value.length}个），建议3-6个以提高检索精度`)
  }

  return warnings
}

// 发布
const handlePublish = async () => {
  if (!isEdit.value) {
    ElMessage.warning('请先保存知识条目后再发布')
    return
  }

  if (!formRef.value) return

  // 提交前更新 scopeJson 和规范化标签
  updateScopeJson()
  normalizeTags()

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    // 发布前检查
    const warnings = validateBeforePublish()
    if (warnings.length > 0) {
      try {
        await ElMessageBox.confirm(
          '发布前检查发现以下建议：\n\n' + warnings.map((w, i) => `${i + 1}. ${w}`).join('\n') + '\n\n是否仍要发布？',
          '发布前提示',
          {
            confirmButtonText: '仍要发布',
            cancelButtonText: '取消',
            type: 'warning',
            dangerouslyUseHTMLString: false
          }
        )
      } catch {
        return // 用户取消
      }
    }

    submitting.value = true
    try {
      const id = Number(route.params.id)
      await knowledgeApi.publish(id)
      ElMessage.success('发布成功')
      router.push('/knowledge')
    } catch (error: any) {
      ElMessage.error('发布失败: ' + (error.message || '未知错误'))
    } finally {
      submitting.value = false
    }
  })
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

    // 加载附件（后端返回 assets）
    const assets = item.assets
    if (assets && assets.length > 0) {
      fileList.value = assets.map((att: AttachmentDto) => ({
        uid: att.id,
        name: att.fileName,
        url: att.fileUrl ?? att.url,
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

  // 提交前更新 scopeJson 和规范化标签
  updateScopeJson()
  normalizeTags()

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
  // uploadRef 由模板 ref="uploadRef" 使用，此处引用以消除 TS6133
  void uploadRef.value
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

.template-tip {
  color: #909399;
  font-size: 12px;
  margin-left: 10px;
}

.tags-tip {
  margin-top: 8px;
  font-size: 12px;
  color: #606266;
}
</style>
