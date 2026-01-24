import axios from 'axios'
import type { KnowledgeItemDto, CreateKnowledgeItemDto, UpdateKnowledgeItemDto, SearchKnowledgeItemDto, PagedResultDto } from '../types/knowledge'

// 根据环境变量或当前域名自动判断API地址
const getApiBaseUrl = () => {
  // 生产环境：如果设置了环境变量，使用环境变量；否则根据当前域名推断
  if (import.meta.env.PROD) {
    const envApiUrl = import.meta.env.VITE_API_BASE_URL
    if (envApiUrl) {
      return envApiUrl
    }
    // 如果前端和后端在同一域名下，使用相对路径
    // 如果不在同一域名，需要配置 VITE_API_BASE_URL 环境变量
    return '/api'
  }
  // 开发环境：使用代理
  return '/api'
}

const api = axios.create({
  baseURL: getApiBaseUrl(),
  timeout: 10000
})

// 映射后端 AssetDto 到前端 AttachmentDto（保持兼容性）
const mapAssetToAttachment = (asset: any): any => {
  return {
    ...asset,
    knowledgeItemId: asset.articleId, // 映射 articleId -> knowledgeItemId
    fileType: asset.assetType, // 映射 assetType -> fileType
    fileUrl: asset.url, // 映射 url -> fileUrl
    fileSize: asset.size // 映射 size -> fileSize
  }
}

// 映射后端 KnowledgeArticleDto 到前端 KnowledgeItemDto（保持兼容性）
const mapArticleToItem = (article: any): KnowledgeItemDto => {
  return {
    ...article,
    attachments: article.assets?.map(mapAssetToAttachment) || article.attachments || []
  }
}

// 知识条目API
export const knowledgeApi = {
  // 获取知识条目详情
  getById: (id: number): Promise<KnowledgeItemDto> => {
    return api.get(`/knowledgeitems/${id}`).then(res => mapArticleToItem(res.data))
  },

  // 搜索知识条目
  search: (params: SearchKnowledgeItemDto): Promise<PagedResultDto<KnowledgeItemDto>> => {
    return api.get('/knowledgeitems/search', { params }).then(res => ({
      ...res.data,
      items: res.data.items.map(mapArticleToItem)
    }))
  },

  // 创建知识条目
  create: (data: CreateKnowledgeItemDto): Promise<KnowledgeItemDto> => {
    return api.post('/knowledgeitems', data).then(res => mapArticleToItem(res.data))
  },

  // 更新知识条目
  update: (id: number, data: UpdateKnowledgeItemDto): Promise<KnowledgeItemDto> => {
    return api.put(`/knowledgeitems/${id}`, data).then(res => mapArticleToItem(res.data))
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
    formData.append('knowledgeItemId', knowledgeItemId.toString()) // 后端会映射为 articleId
    formData.append('file', file)
    return api.post('/attachments/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    }).then(res => mapAssetToAttachment(res.data))
  },

  // 删除附件
  delete: (id: number): Promise<void> => {
    return api.delete(`/attachments/${id}`)
  },

  // 获取知识条目的附件列表
  getByKnowledgeItemId: (knowledgeItemId: number): Promise<any[]> => {
    return api.get(`/attachments/knowledge-item/${knowledgeItemId}`).then(res => 
      res.data.map(mapAssetToAttachment)
    )
  }
}
