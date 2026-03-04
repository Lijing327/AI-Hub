<template>
  <div class="ticket-detail">
    <el-button type="default" @click="goBack" style="margin-bottom: 16px">
      <el-icon><ArrowLeft /></el-icon>
      返回
    </el-button>

    <template v-if="ticket">
      <el-card>
        <template #header>
          <div class="card-header">
            <span>{{ ticket.ticketNo }} - {{ ticket.title }}</span>
            <el-tag :type="getStatusTagType(ticket.status)">{{ statusToCn(ticket.status) }}</el-tag>
          </div>
        </template>

        <el-descriptions :column="2" border>
          <el-descriptions-item label="工单号">{{ ticket.ticketNo }}</el-descriptions-item>
          <el-descriptions-item label="状态">{{ statusToCn(ticket.status) }}</el-descriptions-item>
          <el-descriptions-item label="优先级">{{ priorityToCn(ticket.priority) }}</el-descriptions-item>
          <el-descriptions-item label="来源">{{ getSourceText(ticket.source) }}</el-descriptions-item>
          <el-descriptions-item label="负责人">{{ ticket.assigneeName || '未分配' }}</el-descriptions-item>
          <el-descriptions-item label="创建人">{{ ticket.createdBy }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ formatTime(ticket.createdAt) }}</el-descriptions-item>
          <el-descriptions-item label="更新时间" v-if="ticket.updatedAt">{{ formatTime(ticket.updatedAt) }}</el-descriptions-item>
        </el-descriptions>

        <el-divider />

        <div v-if="ticket.description">
          <h4>问题描述</h4>
          <div class="content-block">{{ ticket.description }}</div>
        </div>

        <div v-if="ticket.finalSolutionSummary">
          <h4>解决方案</h4>
          <div class="content-block solution">{{ ticket.finalSolutionSummary }}</div>
        </div>

        <h4>操作记录</h4>
        <div class="logs-list">
          <div v-for="log in logs" :key="log.logId" class="log-item">
            <div class="log-header">
              <span class="log-action">{{ getActionText(log.action) }}</span>
              <span class="log-time">{{ formatTime(log.createdAt) }}</span>
            </div>
            <div class="log-content" v-if="log.content">{{ log.content }}</div>
            <div class="log-meta" v-if="log.operatorName">操作人：{{ log.operatorName }}</div>
          </div>
        </div>

        <el-divider />

        <div class="actions-row">
          <template v-if="ticket.status === 'pending'">
            <el-button type="primary" @click="showStartDialog = true">开始处理</el-button>
          </template>
          <template v-if="ticket.status === 'processing'">
            <el-button type="success" @click="showResolveDialog = true">标记已解决</el-button>
            <el-button @click="showCloseDialog = true">关闭工单</el-button>
          </template>
          <template v-if="ticket.status === 'resolved'">
            <el-button type="warning" @click="showConvertKbDialog = true">转为知识库</el-button>
            <el-button @click="showCloseDialog = true">关闭工单</el-button>
          </template>
          <template v-if="ticket.status === 'closed'">
            <el-tag type="info">已关闭</el-tag>
          </template>
        </div>

        <el-divider />

        <h4>添加备注</h4>
        <el-input v-model="noteContent" type="textarea" :rows="3" placeholder="输入备注内容..." />
        <el-button type="primary" @click="addNote" :disabled="!noteContent.trim()" style="margin-top: 8px">
          提交
        </el-button>
      </el-card>
    </template>

    <el-card v-else-if="loading">
      <el-skeleton :rows="5" animated />
    </el-card>
    <el-empty v-else description="工单不存在" />

    <!-- 开始处理弹窗 -->
    <el-dialog v-model="showStartDialog" title="开始处理" width="500px" @close="closeDialogs">
      <el-form label-width="80px">
        <el-form-item label="负责人">
          <el-input v-model="assigneeName" placeholder="请输入负责人姓名" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="startNote" type="textarea" :rows="3" placeholder="处理说明" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showStartDialog = false">取消</el-button>
        <el-button type="primary" @click="submitStart">确认</el-button>
      </template>
    </el-dialog>

    <!-- 标记已解决弹窗 -->
    <el-dialog v-model="showResolveDialog" title="标记已解决" width="500px" @close="closeDialogs">
      <el-form label-width="120px">
        <el-form-item label="解决方案摘要" required>
          <el-input v-model="resolveSummary" type="textarea" :rows="5" placeholder="请填写最终解决方案（必填）" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="resolveNote" type="textarea" :rows="3" placeholder="补充说明" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showResolveDialog = false">取消</el-button>
        <el-button type="primary" @click="submitResolve">确认</el-button>
      </template>
    </el-dialog>

    <!-- 关闭工单弹窗 -->
    <el-dialog v-model="showCloseDialog" title="关闭工单" width="500px" @close="closeDialogs">
      <el-form label-width="80px">
        <el-form-item label="备注">
          <el-input v-model="closeNote" type="textarea" :rows="3" placeholder="关闭原因或补充说明（可选）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCloseDialog = false">取消</el-button>
        <el-button type="primary" @click="submitClose">确认</el-button>
      </template>
    </el-dialog>

    <!-- 转为知识库弹窗（可编辑，与知识条目结构一致） -->
    <el-dialog v-model="showConvertKbDialog" title="转为知识库文章" width="620px" @open="initConvertForm" @close="closeDialogs">
      <p class="dialog-hint">将基于工单的解决方案生成知识库文章，并自动触发向量入库。转换前可编辑以下内容，与知识条目结构一致。</p>
      <el-form v-if="ticket" label-width="90px" class="convert-form">
        <el-form-item label="标题">
          <el-input v-model="convertForm.title" placeholder="知识库文章标题" maxlength="500" show-word-limit />
        </el-form-item>
        <el-form-item label="问题描述">
          <el-input v-model="convertForm.questionText" type="textarea" :rows="3" placeholder="用户问题/现象描述" />
        </el-form-item>
        <el-form-item label="原因分析">
          <el-input v-model="convertForm.causeText" type="textarea" :rows="3" placeholder="可能原因 1、2、3…" />
        </el-form-item>
        <el-form-item label="解决方案" required>
          <el-input v-model="convertForm.solutionText" type="textarea" :rows="5" placeholder="最终解决方案（必填）" />
        </el-form-item>
        <el-form-item label="适用范围">
          <el-input v-model="convertForm.scopeJson" type="textarea" :rows="2" placeholder='JSON 格式，如 {"设备系列":"YH400/YH500"} 或 {"device_mn":"设备编号"}' />
        </el-form-item>
        <el-form-item label="标签">
          <el-input v-model="convertForm.tags" type="textarea" :rows="2" placeholder="多个标签用逗号分隔，如：造型机, 油温过高, YH400" />
        </el-form-item>
        <el-form-item label="附件">
          <el-upload
            ref="convertUploadRef"
            v-model:file-list="convertFileList"
            :auto-upload="false"
            :limit="10"
            :on-exceed="handleConvertUploadExceed"
            list-type="picture-card"
            accept="image/*,video/*,application/pdf"
          >
            <el-icon><Plus /></el-icon>
          </el-upload>
          <div class="upload-tip">支持图片、视频、PDF，单个不超过 50MB，最多 10 个</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showConvertKbDialog = false">取消</el-button>
        <el-button type="warning" @click="submitConvertKb" :disabled="!convertForm.solutionText?.trim()">确认转换</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, Plus } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { ticketApi, type TicketDetail as TicketDetailType, type TicketLogItem } from '@/api/tickets'
import { attachmentApi } from '@/api/knowledge'

const props = defineProps<{ id: string }>()
const route = useRoute()
const router = useRouter()

const ticket = ref<TicketDetailType | null>(null)
const logs = ref<TicketLogItem[]>([])
const loading = ref(true)
const noteContent = ref('')

const showStartDialog = ref(false)
const showResolveDialog = ref(false)
const showCloseDialog = ref(false)
const showConvertKbDialog = ref(false)

const assigneeName = ref('')
const startNote = ref('')
const resolveSummary = ref('')
const resolveNote = ref('')
const closeNote = ref('')

/** 转为知识库表单（可编辑，与知识条目结构一致） */
const convertForm = ref({
  title: '',
  questionText: '',
  causeText: '',
  solutionText: '',
  scopeJson: '',
  tags: ''
})

/** 转为知识库时选择的附件（转换成功后上传） */
const convertFileList = ref<{ uid: string; name: string; raw?: File }[]>([])
const convertUploadRef = ref()

const ticketId = computed(() => (props.id ?? route.params.id) as string)

onMounted(() => loadTicket())

async function loadTicket() {
  if (!ticketId.value) return
  loading.value = true
  try {
    const data = await ticketApi.getById(ticketId.value)
    ticket.value = data
    logs.value = data.logs || []
  } catch (err) {
    console.error('加载工单失败:', err)
    ticket.value = null
    ElMessage.error('加载失败')
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

function getSourceText(s: string): string {
  const map: Record<string, string> = { ai_chat: 'AI 对话', manual: '手动创建', api: 'API 创建' }
  return map[s] || s
}

function getActionText(a: string): string {
  const map: Record<string, string> = {
    create: '创建工单',
    start: '开始处理',
    resolve: '标记已解决',
    close: '关闭工单',
    comment: '添加备注',
    convert_to_kb: '转为知识库'
  }
  return map[a] || a
}

/** 打开转为知识库弹窗时，用工单数据初始化表单 */
function initConvertForm() {
  const t = ticket.value
  if (!t) return
  const meta = (t as { meta?: { issueCategory?: string; alarmCode?: string } }).meta
  const ic = meta?.issueCategory ?? ''
  const ac = meta?.alarmCode ?? ''
  const defaultTitle =
    ic || ac ? `[${t.ticketNo}] ${ic} - ${ac} - ${t.title}`.replace(/\s*-\s*$/, '').trim() : `[${t.ticketNo}] ${t.title}`
  const defaultCause =
    ic || ac
      ? `根据 AI 智能客服判断，问题分类为：${ic}${ac ? `\n报警代码：${ac}` : ''}`
      : '详见最终解决方案'
  const defaultScope =
    (t as { deviceMn?: string }).deviceMn
      ? JSON.stringify({ device_mn: (t as { deviceMn?: string }).deviceMn }, null, 2)
      : ''
  convertForm.value = {
    title: defaultTitle,
    questionText: t.description || '无详细描述',
    causeText: defaultCause,
    solutionText: t.finalSolutionSummary || '',
    scopeJson: defaultScope,
    tags: `工单，${t.ticketNo}，${ic || '未分类'}`
  }
  convertFileList.value = []
}

function handleConvertUploadExceed() {
  ElMessage.warning('最多上传 10 个附件')
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

function closeDialogs() {
  showStartDialog.value = false
  showResolveDialog.value = false
  showCloseDialog.value = false
  showConvertKbDialog.value = false
  convertFileList.value = []
}

async function submitStart() {
  try {
    await ticketApi.start(ticketId.value, { assigneeName: assigneeName.value, note: startNote.value })
    ElMessage.success('已开始处理')
    closeDialogs()
    await loadTicket()
  } catch (err: unknown) {
    const e = err as { response?: { data?: { error?: string; message?: string } } }
    ElMessage.error(e?.response?.data?.error || e?.response?.data?.message || '操作失败')
  }
}

async function submitResolve() {
  if (!resolveSummary.value.trim()) {
    ElMessage.warning('解决方案不能为空')
    return
  }
  try {
    await ticketApi.resolve(ticketId.value, {
      finalSolutionSummary: resolveSummary.value,
      note: resolveNote.value
    })
    ElMessage.success('已标记为已解决')
    closeDialogs()
    await loadTicket()
  } catch (err: unknown) {
    const e = err as { response?: { data?: { error?: string; message?: string } } }
    ElMessage.error(e?.response?.data?.error || e?.response?.data?.message || '操作失败')
  }
}

async function submitClose() {
  try {
    await ticketApi.close(ticketId.value, { note: closeNote.value })
    ElMessage.success('工单已关闭')
    closeDialogs()
    await loadTicket()
  } catch (err: unknown) {
    const e = err as { response?: { data?: { error?: string; message?: string } } }
    ElMessage.error(e?.response?.data?.error || e?.response?.data?.message || '操作失败')
  }
}

async function submitConvertKb() {
  if (!convertForm.value.solutionText?.trim()) {
    ElMessage.warning('请填写解决方案')
    return
  }
  const filesToUpload = convertFileList.value.filter((f) => f.raw).map((f) => f.raw as File)
  const hasInvalidFile = filesToUpload.some((f) => {
    const okType = f.type.startsWith('image/') || f.type.startsWith('video/') || f.type === 'application/pdf'
    const okSize = f.size / 1024 / 1024 < 50
    return !okType || !okSize
  })
  if (hasInvalidFile) {
    ElMessage.error('附件仅支持图片、视频、PDF，单个不超过 50MB')
    return
  }
  try {
    const res = await ticketApi.convertToKb(ticketId.value, {
      title: convertForm.value.title.trim() || undefined,
      questionText: convertForm.value.questionText.trim() || undefined,
      causeText: convertForm.value.causeText.trim() || undefined,
      solutionText: convertForm.value.solutionText.trim(),
      scopeJson: convertForm.value.scopeJson.trim() || undefined,
      tags: convertForm.value.tags.trim() || undefined
    })
    const articleId = res.articleId
    if (articleId != null && filesToUpload.length > 0) {
      for (const file of filesToUpload) {
        try {
          await attachmentApi.upload(articleId, file)
        } catch (upErr: unknown) {
          const e = upErr as { response?: { data?: string } }
          console.error('附件上传失败:', file.name, e)
          ElMessage.warning(`附件 ${file.name} 上传失败`)
        }
      }
    }
    const msg = res.vectorSuccess
      ? `${res.message || '已成功转为知识库文章'}\n向量入库：${res.vectorMessage || '成功'}`
      : `${res.message || '已转为知识库文章'}\n向量入库：${res.vectorMessage || '失败'}`
    ElMessage.success(msg)
    closeDialogs()
    await loadTicket()
  } catch (err: unknown) {
    const e = err as { response?: { data?: { error?: string; message?: string } } }
    ElMessage.error(e?.response?.data?.error || e?.response?.data?.message || '操作失败')
  }
}

async function addNote() {
  if (!noteContent.value.trim()) {
    ElMessage.warning('请输入备注内容')
    return
  }
  try {
    await ticketApi.addLog(ticketId.value, { content: noteContent.value })
    noteContent.value = ''
    ElMessage.success('备注已添加')
    await loadTicket()
  } catch (err) {
    ElMessage.error('添加备注失败')
  }
}

function goBack() {
  router.push('/tickets')
}
</script>

<style scoped>
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.content-block {
  padding: 12px;
  background: #f5f7fa;
  border-radius: 4px;
  margin-bottom: 16px;
  white-space: pre-wrap;
}

.content-block.solution {
  background: #f0f9eb;
  border: 1px solid #e1f3d8;
}

.logs-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.log-item {
  padding: 12px;
  background: #fafafa;
  border-radius: 4px;
  border-left: 3px solid #409eff;
}

.log-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.log-action {
  font-weight: 500;
}

.log-time {
  font-size: 12px;
  color: #909399;
}

.log-content {
  font-size: 14px;
  color: #606266;
  margin-bottom: 4px;
}

.log-meta {
  font-size: 12px;
  color: #909399;
}

.actions-row {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.convert-form {
  margin-top: 12px;
}

.convert-form :deep(.el-form-item) {
  margin-bottom: 16px;
}

.upload-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 6px;
}

.dialog-hint {
  color: #606266;
  margin-bottom: 16px;
}

.dialog-preview {
  padding: 12px;
  background: #f5f7fa;
  border-radius: 4px;
}

.dialog-preview p {
  margin: 8px 0;
  font-size: 14px;
}
</style>
