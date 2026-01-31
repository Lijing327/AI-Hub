/**
 * 知识库 API 服务
 */
import axios from 'axios'
import { apiConfig } from '@/config/api'

// 创建 axios 实例
const api = axios.create({
  baseURL: apiConfig.baseURL,
  timeout: apiConfig.timeout,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器：添加租户ID（暂时使用默认值）
api.interceptors.request.use((config) => {
  // 暂时不处理登录，使用默认租户ID
  config.headers['X-Tenant-Id'] = apiConfig.defaultTenant
  return config
})

// 后端知识条目 DTO
export interface KnowledgeArticleDto {
  id: number
  tenantId?: string
  title: string
  questionText?: string
  causeText?: string
  solutionText?: string
  scopeJson?: string
  tags?: string
  status: string
  version: number
  createdBy?: string
  createdAt: string
  updatedAt?: string
  publishedAt?: string
  deletedAt?: string
  assets?: AssetDto[]
}

// 资产 DTO
export interface AssetDto {
  id: number
  articleId: number
  assetType: string
  url: string
  fileName: string
  size?: number
  mimeType?: string
}

// 搜索请求参数
export interface SearchKnowledgeArticleDto {
  keyword?: string
  status?: string
  tag?: string
  scopeJson?: string
  pageIndex?: number
  pageSize?: number
}

// 分页结果
export interface PagedResultDto<T> {
  items: T[]
  totalCount: number
  pageIndex: number
  pageSize: number
  totalPages: number
}

/**
 * 搜索知识条目
 */
export async function searchKnowledgeArticles(
  params: SearchKnowledgeArticleDto
): Promise<PagedResultDto<KnowledgeArticleDto>> {
  console.log('API请求参数:', params)
  try {
    const response = await api.get<PagedResultDto<KnowledgeArticleDto>>(
      '/knowledgeitems/search',
      { params }
    )
    console.log('API响应:', {
      totalCount: response.data.totalCount,
      itemsCount: response.data.items.length,
      pageIndex: response.data.pageIndex,
      pageSize: response.data.pageSize
    })
    return response.data
  } catch (error: any) {
    console.error('搜索知识库失败:', error)
    console.error('请求参数:', params)
    console.error('错误详情:', error.response?.data || error.message)
    throw error
  }
}

/**
 * 根据ID获取知识条目
 */
export async function getKnowledgeArticleById(
  id: number
): Promise<KnowledgeArticleDto> {
  const response = await api.get<KnowledgeArticleDto>(`/knowledgeitems/${id}`)
  return response.data
}

/**
 * 智能客服搜索和回答（通过Python服务）
 */
export interface ChatRequest {
  question: string
  device_id?: string
  tenant_id?: string
  // 审计相关：会话 ID（首次不传则自动创建，后续消息带上）
  conversation_id?: string
  user_id?: string
  channel?: string
}

// 技术资料项（附件）
export interface TechnicalResourceDto {
  id: number
  name: string  // 文件名
  type: string  // image/video/document/other
  url: string   // 访问地址
  size?: number // 文件大小（字节）
  duration?: number // 视频时长（秒）
}

export interface ChatResponse {
  issue_category: string
  alarm_code?: string
  confidence: number
  top_causes: string[]
  steps: Array<{
    title: string
    action: string
    expect: string
    next: string
  }>
  solution: {
    temporary: string
    final: string
  }
  safety_tip: string
  cited_docs: Array<{
    kbId: string
    title: string
    excerpt: string
  }>
  should_escalate: boolean
  short_answer_text: string
  related_articles?: Array<{
    id: number
    title: string
    questionText?: string
    excerpt?: string
  }>
  /** 技术资料（命中知识条目的附件：图片、视频、文档等） */
  technical_resources?: TechnicalResourceDto[]
  /** 展示模式：conversation=仅对话气泡，不展示故障排查结构；未设置或 troubleshooting=完整结构 */
  reply_mode?: 'conversation' | 'troubleshooting'
  /** 会话 ID（首次请求时自动创建，后续请求应带上） */
  conversation_id?: string
  /** 本条 assistant 消息 ID */
  message_id?: string
}

/**
 * 调用Python服务进行智能搜索和回答
 */
export async function chatSearch(request: ChatRequest): Promise<ChatResponse> {
  console.log('调用Python服务搜索:', request)
  
  // Python服务地址（通过代理）
  const pythonApiBaseUrl = import.meta.env.VITE_PYTHON_API_BASE_URL || '/python-api'
  
  try {
    const response = await axios.post<ChatResponse>(
      `${pythonApiBaseUrl}/api/chat/search`,
      request,
      {
        timeout: 15000,
        headers: {
          'Content-Type': 'application/json'
        }
      }
    )
    console.log('Python服务响应:', response.data)
    return response.data
  } catch (error: any) {
    console.error('Python服务调用失败:', error)
    console.error('请求参数:', request)
    console.error('错误详情:', error.response?.data || error.message)
    throw error
  }
}
