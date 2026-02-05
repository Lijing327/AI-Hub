/**
 * 数据结构类型定义
 */

// 客户信息
export interface Customer {
  customerId: string
  name: string
  contactName: string
  phone: string
  region: string
  createdAt: string
}

// 设备信息
export interface Device {
  deviceId: string
  customerId: string
  model: string
  serialNo: string
  controllerType: string
  installDate: string
  status: '正常' | '故障' | '维护中'
}

// 聊天会话
export interface ChatSession {
  sessionId: string
  customerId: string
  deviceId: string
  channel: string
  startTime: string
  endTime?: string
  issueCategory?: string
  alarmCode?: string
  resolvedStatus: '未反馈' | '已解决' | '未解决'
  escalatedToTicket: boolean
  summary?: string
}

// 聊天消息
export interface ChatMessage {
  messageId: string
  sessionId: string
  role: 'user' | 'assistant' | 'system'
  content: string
  attachments?: string[]
  createdAt: string
}

// AI 响应元数据
export interface AIResponseMeta {
  metaId: string
  sessionId: string
  relatedMessageId: string
  confidence: number
  topCauses: string[]
  steps: {
    title: string
    action: string
    expect: string
    next: string
  }[]
  safetyFlag: boolean
  citedDocs: {
    kbId: string
    title: string
    excerpt: string
  }[]
  solution: {
    temporary: string
    final: string
  }
  alarmCode?: string
  issueCategory: string
  relatedArticles?: RelatedArticle[] // 其他可能匹配的知识条目
  technicalResources?: TechnicalResource[] // 技术资料（附件）
  /** 展示模式：conversation=仅对话气泡；handoff=转人工引导；troubleshooting=故障排查卡片 */
  replyMode?: 'conversation' | 'troubleshooting' | 'handoff'
  /** 安全提示文案 */
  safetyTip?: string
}

// 工单
export interface Ticket {
  ticketId: string
  customerId: string
  deviceId: string
  sessionId: string
  title: string
  description: string
  status: '待处理' | '处理中' | '已解决' | '已关闭'
  priority: '低' | '中' | '高' | '紧急'
  assignee?: string
  createdAt: string
  closedAt?: string
  finalSolutionSummary?: string
}

// 工单日志
export interface TicketLog {
  logId: string
  ticketId: string
  action: string
  content: string
  operator: string
  createdAt: string
}

// 反馈
export interface Feedback {
  feedbackId: string
  sessionId: string
  ticketId?: string
  score?: number
  isResolved?: boolean
  comment?: string
  createdAt: string
}

// 知识库样本
export interface KbSample {
  kbId: string
  title: string
  modelTags: string[]
  docType: string
  excerpt: string
}

// 演示问题
export interface DemoQuestion {
  text: string
  deviceModelHint?: string
  alarmCode?: string
}

// AI 响应结果
export interface AIResponse {
  issueCategory: string
  alarmCode?: string
  confidence: number
  topCauses: string[]
  steps: {
    title: string
    action: string
    expect: string
    next: string
  }[]
  solution: {
    temporary: string
    final: string
  }
  safetyTip: string
  citedDocs: {
    kbId: string
    title: string
    excerpt: string
  }[]
  shouldEscalate: boolean
  shortAnswerText: string
  relatedArticles?: RelatedArticle[] // 其他可能匹配的知识条目
  technicalResources?: TechnicalResource[] // 技术资料（附件）
  /** 展示模式：conversation=仅对话气泡，不展示故障排查结构 */
  replyMode?: 'conversation' | 'troubleshooting'
}

// 相关文章（用于显示其他可能匹配的问题）
export interface RelatedArticle {
  id: number
  title: string
  questionText?: string
  excerpt?: string
}

// 技术资料（命中知识条目的附件：图片、视频、文档等）
export interface TechnicalResource {
  id: number
  name: string      // 文件名
  type: string      // image/video/document/other
  url: string       // 访问地址
  size?: number     // 文件大小（字节）
  duration?: number // 视频时长（秒）
}
