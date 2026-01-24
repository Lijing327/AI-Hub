import axios from 'axios'
import type { KnowledgeItemDto, CreateKnowledgeItemDto, UpdateKnowledgeItemDto, SearchKnowledgeItemDto, PagedResultDto } from '../types/knowledge'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000
})

// 知识条目API
export const knowledgeApi = {
  // 获取知识条目详情
  getById: (id: number): Promise<KnowledgeItemDto> => {
    return api.get(`/knowledgeitems/${id}`).then(res => res.data)
  },

  // 搜索知识条目
  search: (params: SearchKnowledgeItemDto): Promise<PagedResultDto<KnowledgeItemDto>> => {
    return api.get('/knowledgeitems/search', { params }).then(res => res.data)
  },

  // 创建知识条目
  create: (data: CreateKnowledgeItemDto): Promise<KnowledgeItemDto> => {
    return api.post('/knowledgeitems', data).then(res => res.data)
  },

  // 更新知识条目
  update: (id: number, data: UpdateKnowledgeItemDto): Promise<KnowledgeItemDto> => {
    return api.put(`/knowledgeitems/${id}`, data).then(res => res.data)
  },

  // 删除知识条目
  delete: (id: number): Promise<void> => {
    return api.delete(`/knowledgeitems/${id}`)
  },

  // 发布知识条目
  publish: (id: number): Promise<void> => {
    return api.post(`/knowledgeitems/${id}/publish`)
  }
}

// 附件API
export const attachmentApi = {
  // 上传附件
  upload: (knowledgeItemId: number, file: File): Promise<any> => {
    const formData = new FormData()
    formData.append('knowledgeItemId', knowledgeItemId.toString())
    formData.append('file', file)
    return api.post('/attachments/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    }).then(res => res.data)
  },

  // 删除附件
  delete: (id: number): Promise<void> => {
    return api.delete(`/attachments/${id}`)
  },

  // 获取知识条目的附件列表
  getByKnowledgeItemId: (knowledgeItemId: number): Promise<any[]> => {
    return api.get(`/attachments/knowledge-item/${knowledgeItemId}`).then(res => res.data)
  }
}
