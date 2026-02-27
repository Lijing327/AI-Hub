/**
 * 工单管理 API（工程师端）
 */
import axios from 'axios'
import { apiConfig } from '@/config/api'

const getApiBaseUrl = () => {
  if (import.meta.env.PROD) {
    return apiConfig.baseURL || import.meta.env.VITE_API_BASE_URL || '/api'
  }
  return '/api'
}

const api = axios.create({
  baseURL: getApiBaseUrl(),
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' }
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  config.headers['X-Tenant-Id'] = apiConfig.defaultTenant || 'default'
  return config
})

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
    }
    return Promise.reject(err)
  }
)

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

export interface TicketListResponse {
  items: TicketListItem[]
  totalCount: number
  pageIndex: number
  pageSize: number
}

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

export interface TicketDetail {
  ticketId: string
  ticketNo: string
  title: string
  description?: string
  status: string
  priority: string
  source: string
  deviceMn?: string
  assigneeName?: string
  createdBy: string
  createdAt: string
  updatedAt?: string
  closedAt?: string
  finalSolutionSummary?: string
  sessionId?: string
  logs?: TicketLogItem[]
}

export const ticketApi = {
  list: (params: { status?: string; pageIndex?: number; pageSize?: number; keyword?: string; assigneeId?: string }) =>
    api.get<TicketListResponse>('admin/tickets', { params }).then((r) => r.data),

  getById: (id: string) => api.get<TicketDetail>(`admin/tickets/${id}`).then((r) => r.data),

  start: (id: string, data?: { assigneeName?: string; note?: string }) =>
    api.post<TicketDetail>(`admin/tickets/${id}/start`, data || {}).then((r) => r.data),

  resolve: (id: string, data: { finalSolutionSummary: string; note?: string }) =>
    api.post<TicketDetail>(`admin/tickets/${id}/resolve`, data).then((r) => r.data),

  close: (id: string, data?: { note?: string }) =>
    api.post<TicketDetail>(`admin/tickets/${id}/close`, data || {}).then((r) => r.data),

  addLog: (id: string, data: { content: string; operatorName?: string }) =>
    api.post(`admin/tickets/${id}/logs`, data),

  convertToKb: (id: string, data?: { triggerVectorIndex?: boolean }) =>
    api.post<{ message: string; articleId?: number; vectorSuccess?: boolean; vectorMessage?: string }>(
      `admin/tickets/${id}/convert-to-kb`,
      data ?? { triggerVectorIndex: true }
    ).then((r) => r.data)
}
