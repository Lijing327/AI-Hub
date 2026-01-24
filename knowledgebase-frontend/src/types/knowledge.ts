// 知识条目类型定义
export interface KnowledgeItemDto {
  id: number
  title: string
  questionText?: string
  causeText?: string
  solutionText?: string
  scopeJson?: string
  tags?: string
  status: string
  version: number
  tenantId?: string
  createdBy?: string
  createdAt: string
  updatedAt?: string
  publishedAt?: string
  attachments?: AttachmentDto[]
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

export interface AttachmentDto {
  id: number
  knowledgeItemId: number
  fileName: string
  fileUrl: string
  fileType: string
  fileSize: number
  createdAt: string
}
