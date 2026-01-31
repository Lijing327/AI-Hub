/**
 * AI 审计 API 服务
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

// 请求拦截器
api.interceptors.request.use((config) => {
  config.headers['X-Tenant-Id'] = apiConfig.defaultTenant
  return config
})

// ========== 类型定义 ==========

/** 会话列表查询参数 */
export interface ConversationListQuery {
  tenantId?: string
  userId?: string
  channel?: string
  intentType?: string
  hasFallback?: boolean
  startFrom?: string
  startTo?: string
  page?: number
  pageSize?: number
}

/** 会话列表项 */
export interface ConversationListItem {
  conversationId: string
  tenantId: string
  userId?: string
  channel: string
  startedAt: string
  endedAt?: string
  messageCount: number
  mainIntent?: string
  hasFallback: boolean
  avgResponseTimeMs?: number
}

/** 会话列表响应 */
export interface ConversationListResponse {
  items: ConversationListItem[]
  totalCount: number
  page: number
  pageSize: number
  totalPages: number
}

/** 决策详情 */
export interface DecisionDetail {
  intentType: string
  confidence: number
  modelName?: string
  promptVersion?: string
  useKnowledge: boolean
  fallbackReason?: string
  tokensIn?: number
  tokensOut?: number
}

/** 检索详情 */
export interface RetrievalDetail {
  docId: string
  docTitle?: string
  score: number
  rank: number
}

/** 响应详情 */
export interface ResponseDetail {
  finalAnswer?: string
  responseTimeMs: number
  isSuccess: boolean
  errorType?: string
  errorDetail?: string
}

/** 消息详情 */
export interface MessageDetail {
  messageId: string
  role: string
  content: string
  createdAt: string
  decision?: DecisionDetail
  retrievals?: RetrievalDetail[]
  response?: ResponseDetail
}

/** 会话详情 */
export interface ConversationDetail {
  conversationId: string
  tenantId: string
  userId?: string
  channel: string
  startedAt: string
  endedAt?: string
  metaJson?: string
  messages: MessageDetail[]
}

// ========== API 方法 ==========

/**
 * 获取会话列表
 */
export async function getConversationList(
  query: ConversationListQuery
): Promise<ConversationListResponse> {
  const params = new URLSearchParams()
  
  if (query.tenantId) params.append('TenantId', query.tenantId)
  if (query.userId) params.append('UserId', query.userId)
  if (query.channel) params.append('Channel', query.channel)
  if (query.intentType) params.append('IntentType', query.intentType)
  if (query.hasFallback !== undefined) params.append('HasFallback', String(query.hasFallback))
  if (query.startFrom) params.append('StartFrom', query.startFrom)
  if (query.startTo) params.append('StartTo', query.startTo)
  if (query.page) params.append('Page', String(query.page))
  if (query.pageSize) params.append('PageSize', String(query.pageSize))

  const response = await api.get<ConversationListResponse>(
    `/ai-audit/conversations?${params.toString()}`
  )
  return response.data
}

/**
 * 获取会话详情
 */
export async function getConversationDetail(
  conversationId: string
): Promise<ConversationDetail> {
  const response = await api.get<ConversationDetail>(
    `/ai-audit/conversations/${conversationId}`
  )
  return response.data
}

// ========== 统计 API ==========

/** 统计查询参数 */
export interface StatsQuery {
  tenantId?: string
  startFrom?: string
  startTo?: string
}

/** 统计概览 */
export interface StatsOverview {
  totalConversations: number
  totalMessages: number
  fallbackRate: number
  lowConfidenceRate: number
  avgResponseTimeMs: number
  successRate: number
  knowledgeUsageRate: number
}

/** 意图统计项 */
export interface IntentStat {
  intentType: string
  count: number
  percentage: number
}

/** 文档命中统计项 */
export interface DocHitStat {
  docId: string
  docTitle?: string
  hitCount: number
  avgScore: number
}

/** 无命中问题 */
export interface NoMatchQuestion {
  messageId: string
  question: string
  createdAt: string
  fallbackReason?: string
}

/**
 * 获取统计概览
 */
export async function getStatsOverview(query: StatsQuery): Promise<StatsOverview> {
  const params = new URLSearchParams()
  if (query.tenantId) params.append('TenantId', query.tenantId)
  if (query.startFrom) params.append('StartFrom', query.startFrom)
  if (query.startTo) params.append('StartTo', query.startTo)
  
  const response = await api.get<StatsOverview>(`/ai-audit/stats/overview?${params.toString()}`)
  return response.data
}

/**
 * 获取 Top 意图统计
 */
export async function getTopIntents(query: StatsQuery, top: number = 10): Promise<IntentStat[]> {
  const params = new URLSearchParams()
  if (query.tenantId) params.append('TenantId', query.tenantId)
  if (query.startFrom) params.append('StartFrom', query.startFrom)
  if (query.startTo) params.append('StartTo', query.startTo)
  params.append('top', String(top))
  
  const response = await api.get<IntentStat[]>(`/ai-audit/stats/top-intents?${params.toString()}`)
  return response.data
}

/**
 * 获取 Top 命中文档统计
 */
export async function getTopDocs(query: StatsQuery, top: number = 10): Promise<DocHitStat[]> {
  const params = new URLSearchParams()
  if (query.tenantId) params.append('TenantId', query.tenantId)
  if (query.startFrom) params.append('StartFrom', query.startFrom)
  if (query.startTo) params.append('StartTo', query.startTo)
  params.append('top', String(top))
  
  const response = await api.get<DocHitStat[]>(`/ai-audit/stats/top-docs?${params.toString()}`)
  return response.data
}

/**
 * 获取无命中问题列表
 */
export async function getNoMatchQuestions(query: StatsQuery, top: number = 50): Promise<NoMatchQuestion[]> {
  const params = new URLSearchParams()
  if (query.tenantId) params.append('TenantId', query.tenantId)
  if (query.startFrom) params.append('StartFrom', query.startFrom)
  if (query.startTo) params.append('StartTo', query.startTo)
  params.append('top', String(top))
  
  const response = await api.get<NoMatchQuestion[]>(`/ai-audit/stats/no-match?${params.toString()}`)
  return response.data
}
