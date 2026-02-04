/**
 * 仓储层：基于 storage 的数据操作封装
 */

import {
  sessionStorage,
  messageStorage,
  ticketStorage,
  ticketLogStorage,
  feedbackStorage,
  aiMetaStorage,
  customerStorage,
  deviceStorage
} from './storage'
import type {
  ChatSession,
  ChatMessage,
  Ticket,
  TicketLog,
  Feedback,
  AIResponseMeta,
  Customer,
  Device
} from '@/models/types'
import { nanoid } from 'nanoid'

// 会话仓储
export const sessionRepo = {
  getAll: (): ChatSession[] => sessionStorage.getAll(),
  getById: (sessionId: string): ChatSession | null => sessionStorage.getById(sessionId),
  create: (session: Omit<ChatSession, 'sessionId'>): ChatSession => {
    const newSession: ChatSession = {
      ...session,
      sessionId: nanoid()
    }
    sessionStorage.add(newSession)
    return newSession
  },
  update: (sessionId: string, updates: Partial<ChatSession>): boolean => {
    return sessionStorage.update(sessionId, updates)
  },
  getByDeviceId: (deviceId: string): ChatSession[] => {
    const sessions = sessionStorage.getAll() as ChatSession[]
    return sessions.filter((s) => s.deviceId === deviceId)
      .sort((a, b) => new Date(b.startTime).getTime() - new Date(a.startTime).getTime())
  }
}

// 消息仓储
export const messageRepo = {
  getBySessionId: (sessionId: string): ChatMessage[] => messageStorage.getBySessionId(sessionId),
  create: (message: Omit<ChatMessage, 'messageId'>): ChatMessage => {
    const newMessage: ChatMessage = {
      ...message,
      messageId: nanoid()
    }
    messageStorage.add(newMessage)
    return newMessage
  }
}

// 工单仓储
export const ticketRepo = {
  getAll: (): Ticket[] => ticketStorage.getAll(),
  getById: (ticketId: string): Ticket | null => ticketStorage.getById(ticketId),
  create: (ticket: Omit<Ticket, 'ticketId'>): Ticket => {
    const newTicket: Ticket = {
      ...ticket,
      ticketId: nanoid()
    }
    ticketStorage.add(newTicket)
    return newTicket
  },
  update: (ticketId: string, updates: Partial<Ticket>): boolean => {
    return ticketStorage.update(ticketId, updates)
  },
  getByDeviceId: (deviceId: string): Ticket[] => {
    const tickets = ticketStorage.getAll()
    return tickets.filter((t) => t.deviceId === deviceId)
      .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())
  }
}

// 工单日志仓储
export const ticketLogRepo = {
  getByTicketId: (ticketId: string): TicketLog[] => ticketLogStorage.getByTicketId(ticketId),
  create: (log: Omit<TicketLog, 'logId'>): TicketLog => {
    const newLog: TicketLog = {
      ...log,
      logId: nanoid()
    }
    ticketLogStorage.add(newLog)
    return newLog
  }
}

// 反馈仓储
export const feedbackRepo = {
  create: (feedback: Omit<Feedback, 'feedbackId'>): Feedback => {
    const newFeedback: Feedback = {
      ...feedback,
      feedbackId: nanoid()
    }
    feedbackStorage.add(newFeedback)
    return newFeedback
  }
}

// AI 元数据仓储
export const aiMetaRepo = {
  getBySessionId: (sessionId: string): AIResponseMeta[] => aiMetaStorage.getBySessionId(sessionId),
  getByMessageId: (messageId: string): AIResponseMeta | null => aiMetaStorage.getByMessageId(messageId),
  create: (meta: Omit<AIResponseMeta, 'metaId'>): AIResponseMeta => {
    const newMeta: AIResponseMeta = {
      ...meta,
      metaId: nanoid(),
      solution: meta.solution || { temporary: '', final: '' }
    }
    aiMetaStorage.add(newMeta)
    return newMeta
  }
}

// 客户仓储
export const customerRepo = {
  getAll: (): Customer[] => customerStorage.getAll(),
  getById: (customerId: string): Customer | null => customerStorage.getById(customerId)
}

// 设备仓储
export const deviceRepo = {
  getAll: (): Device[] => deviceStorage.getAll(),
  getById: (deviceId: string): Device | null => deviceStorage.getById(deviceId),
  getByCustomerId: (customerId: string): Device[] => deviceStorage.getByCustomerId(customerId)
}
