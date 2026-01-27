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
