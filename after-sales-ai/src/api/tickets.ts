/**
 * 工单 API（用户端）
 */
import api from '@/utils/api'

/** 创建工单 Meta 对象（与后端 TicketMeta 对应） */
export interface CreateTicketMeta {
  issueCategory?: string
  alarmCode?: string
  citedDocs?: string[]
  extra?: Record<string, unknown>
}

/** 创建工单请求体（后端支持 Meta 对象或 metaJson 字符串） */
export interface CreateTicketRequest {
  title: string
  description?: string
  priority?: 'low' | 'medium' | 'high' | 'urgent'
  deviceId?: string
  deviceMn?: string
  customerId?: string
  sessionId?: string
  triggerMessageId?: string
  source?: string
  meta?: CreateTicketMeta
  /** 扩展元数据 JSON 字符串（部分后端实现使用此字段） */
  metaJson?: string
}

/** 工单列表项 */
export interface TicketListItem {
  ticketId: string
  ticketNo: string
  title: string
  status: string
  priority: string
  source: string
  deviceMn?: string
  assigneeName?: string
  createdBy: string
  createdAt: string
}

/** 工单列表响应 */
export interface TicketListResponse {
  items: TicketListItem[]
  totalCount: number
  pageIndex: number
  pageSize: number
}

/** 工单详情 */
export interface TicketDetail {
  ticketId: string
  ticketNo: string
  tenantId?: string
  title: string
  description?: string
  status: string
  priority: string
  source: string
  deviceId?: string
  deviceMn?: string
  customerId?: string
  sessionId?: string
  triggerMessageId?: string
  assigneeId?: string
  assigneeName?: string
  createdBy: string
  createdAt: string
  updatedAt?: string
  closedAt?: string
  finalSolutionSummary?: string
  metaJson?: string
  logs?: TicketLogItem[]
}

/** 工单日志项 */
export interface TicketLogItem {
  logId: number
  ticketId: string
  action: string
  content?: string
  operatorId?: string
  operatorName?: string
  nextStatus?: string
  createdAt: string
}

/** 创建工单 */
export async function createTicket(data: CreateTicketRequest): Promise<TicketDetail> {
  const response = await api.post<TicketDetail>('tickets', data)
  return response.data
}

/** 获取工单列表 */
export async function getTicketList(params: {
  status?: string
  pageIndex?: number
  pageSize?: number
  keyword?: string
}): Promise<TicketListResponse> {
  const response = await api.get<TicketListResponse>('tickets', { params })
  return response.data
}

/** 获取工单详情 */
export async function getTicketDetail(id: string): Promise<TicketDetail> {
  const response = await api.get<TicketDetail>(`tickets/${id}`)
  return response.data
}

/** 获取工单日志 */
export async function getTicketLogs(id: string): Promise<TicketLogItem[]> {
  const response = await api.get<TicketLogItem[]>(`tickets/${id}/logs`)
  return response.data
}

/** 添加工单备注 */
export async function addTicketLog(id: string, data: { content: string; operatorName?: string }): Promise<void> {
  await api.post(`tickets/${id}/logs`, data)
}
