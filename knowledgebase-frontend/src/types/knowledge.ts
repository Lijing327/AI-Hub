// 知识条目类型定义（对应后端 KnowledgeArticleDto）
export interface KnowledgeItemDto {
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
  assets?: AttachmentDto[] // 保持前端字段名为 attachments，后端返回 assets
}

export interface CreateKnowledgeItemDto {
  title: string
  questionText?: string
  causeText?: string
  solutionText?: string
  scopeJson?: string
  tags?: string
  tenantId?: string
  createdBy?: string
}

export interface UpdateKnowledgeItemDto {
  title: string
  questionText?: string
  causeText?: string
  solutionText?: string
  scopeJson?: string
  tags?: string
}

export interface SearchKnowledgeItemDto {
  keyword?: string
  status?: string
  tag?: string
  scopeJson?: string
  pageIndex?: number
  pageSize?: number
}

export interface PagedResultDto<T> {
  items: T[]
  totalCount: number
  pageIndex: number
  pageSize: number
  totalPages: number
}

// 附件类型定义（对应后端 AssetDto，保持API兼容性）
export interface AttachmentDto {
  id: number
  tenantId?: string
  articleId: number // 后端字段，前端仍使用 knowledgeItemId 映射
  knowledgeItemId?: number // 前端兼容字段，映射自 articleId
  assetType: string // 后端字段：image/video/pdf/other
  fileType?: string // 前端兼容字段，映射自 assetType
  fileName: string
  url: string // 后端字段（OSS/本地路径）
  fileUrl?: string // 前端兼容字段，映射自 url
  size: number // 后端字段
  fileSize?: number // 前端兼容字段，映射自 size
  duration?: number // 视频时长（秒，可选）
  createdAt: string
}
