/**
 * AI 服务：从后端知识库获取数据并匹配问题
 * 现在通过Python服务进行搜索和AI回答，便于后续集成大模型
 * 
 * 审计功能：
 * - 首次调用不传 conversation_id，后端自动创建
 * - 后端返回 conversation_id，前端存储后续请求带上
 * - 支持完整的对话回放和审计
 */
import type { Device, AIResponse, TechnicalResource } from '@/models/types'
import { chatSearch, type ChatResponse } from '@/api/knowledge'

/** AI 响应（带审计字段） */
export interface AIResponseWithAudit extends AIResponse {
  relatedArticles?: Array<{ id: number; title: string; questionText?: string }>
  technicalResources?: TechnicalResource[] // 技术资料（附件）
  /** 会话 ID（存储后续请求带上） */
  conversationId?: string
  /** 本条消息 ID */
  messageId?: string
}

/**
 * 根据问题和设备信息生成 AI 回答
 * @param questionText 用户问题
 * @param device 设备信息
 * @param conversationId 会话 ID（首次不传，后续带上）
 * @param userId 用户 ID（可选）
 * @param channel 渠道（默认 web）
 */
export async function generateAIResponse(
  questionText: string,
  device: Device,
  conversationId?: string,
  userId?: string,
  channel: string = 'web'
): Promise<AIResponseWithAudit> {
  console.log('开始搜索知识库，问题:', questionText, '会话:', conversationId)
  
  // 调用Python服务进行智能搜索和回答
  // Python服务会调用.NET后端搜索知识库，并进行数据解析和格式化
  // 后续可以在这里集成AI大模型进行语义匹配和自然语言生成
  const chatResponse = await chatSearch({
    question: questionText,
    device_id: device.deviceId,
    conversation_id: conversationId,
    user_id: userId,
    channel: channel
  })

  console.log('Python服务返回:', chatResponse)

  // 将Python服务的响应转换为前端需要的格式
  return convertChatResponseToAIResponse(chatResponse)
}

/**
 * 将Python服务的响应转换为前端AI响应格式
 */
function convertChatResponseToAIResponse(chatResponse: ChatResponse): AIResponseWithAudit {
  return {
    issueCategory: chatResponse.issue_category,
    alarmCode: chatResponse.alarm_code,
    confidence: chatResponse.confidence,
    topCauses: chatResponse.top_causes,
    steps: chatResponse.steps,
    solution: chatResponse.solution,
    safetyTip: chatResponse.safety_tip,
    citedDocs: chatResponse.cited_docs,
    shouldEscalate: chatResponse.should_escalate,
    shortAnswerText: chatResponse.short_answer_text,
    relatedArticles: chatResponse.related_articles?.map(a => ({
      id: a.id,
      title: a.title,
      questionText: a.questionText
    })),
    // 技术资料（附件）
    technicalResources: chatResponse.technical_resources?.map(r => ({
      id: r.id,
      name: r.name,
      type: r.type,
      url: r.url,
      size: r.size,
      duration: r.duration
    })),
    replyMode: chatResponse.reply_mode,
    // 审计字段
    conversationId: chatResponse.conversation_id,
    messageId: chatResponse.message_id
  }
}
