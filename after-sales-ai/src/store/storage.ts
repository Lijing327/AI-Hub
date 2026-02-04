/**
 * localStorage 封装
 */

const STORAGE_PREFIX = 'after_ai_v1'
const VERSION_KEY = `${STORAGE_PREFIX}_version`
const CURRENT_VERSION = '1.0.0'

// 存储键名
const KEYS = {
  customers: `${STORAGE_PREFIX}_customers`,
  devices: `${STORAGE_PREFIX}_devices`,
  sessions: `${STORAGE_PREFIX}_sessions`,
  messages: `${STORAGE_PREFIX}_messages`,
  tickets: `${STORAGE_PREFIX}_tickets`,
  ticketLogs: `${STORAGE_PREFIX}_ticketLogs`,
  feedbacks: `${STORAGE_PREFIX}_feedbacks`,
  aiMetas: `${STORAGE_PREFIX}_aiMetas`
}

/**
 * 获取存储的数据
 */
function getItem<T>(key: string): T | null {
  try {
    const item = localStorage.getItem(key)
    return item ? JSON.parse(item) : null
  } catch (error) {
    console.error(`读取 localStorage [${key}] 失败:`, error)
    return null
  }
}

/**
 * 设置存储的数据
 */
function setItem<T>(key: string, value: T): void {
  try {
    localStorage.setItem(key, JSON.stringify(value))
  } catch (error) {
    console.error(`写入 localStorage [${key}] 失败:`, error)
  }
}

/**
 * 追加数据到数组
 */
function appendItem<T>(key: string, item: T): void {
  const array = getItem<T[]>(key) || []
  array.push(item)
  setItem(key, array)
}

/**
 * 更新数组中的某个项
 */
function updateItemInArray<T extends { [key: string]: any }>(
  key: string,
  idKey: string,
  id: string,
  updates: Partial<T>
): boolean {
  const array = getItem<T[]>(key) || []
  const index = array.findIndex((item) => item[idKey] === id)
  if (index === -1) return false
  array[index] = { ...array[index], ...updates }
  setItem(key, array)
  return true
}

/**
 * 初始化存储（首次进入时）
 */
export async function initIfNeeded(): Promise<void> {
  const version = localStorage.getItem(VERSION_KEY)
  if (version === CURRENT_VERSION) {
    // 已初始化，检查是否有数据
    const customers = getItem<any[]>(KEYS.customers)
    if (customers && Array.isArray(customers) && customers.length > 0) {
      return // 已有数据，不覆盖
    }
  }

  // 导入 mock 数据
  try {
    const customersModule = await import('@/mock/customers.json')
    setItem(KEYS.customers, customersModule.default)
    
    const devicesModule = await import('@/mock/devices.json')
    setItem(KEYS.devices, devicesModule.default)
  } catch (error) {
    console.error('初始化 mock 数据失败:', error)
  }

  // 初始化其他数据为空数组（如果不存在）
  if (!getItem(KEYS.sessions)) setItem(KEYS.sessions, [])
  if (!getItem(KEYS.messages)) setItem(KEYS.messages, [])
  if (!getItem(KEYS.tickets)) setItem(KEYS.tickets, [])
  if (!getItem(KEYS.ticketLogs)) setItem(KEYS.ticketLogs, [])
  if (!getItem(KEYS.feedbacks)) setItem(KEYS.feedbacks, [])
  if (!getItem(KEYS.aiMetas)) setItem(KEYS.aiMetas, [])

  localStorage.setItem(VERSION_KEY, CURRENT_VERSION)
}

/**
 * 清空所有演示数据
 */
export async function clearAllData(): Promise<void> {
  Object.values(KEYS).forEach((key) => {
    localStorage.removeItem(key)
  })
  localStorage.removeItem(VERSION_KEY)
  await initIfNeeded()
}

/**
 * 导出所有数据为 JSON
 */
export function exportAllAsJson(): string {
  const data = {
    version: CURRENT_VERSION,
    exportTime: new Date().toISOString(),
    customers: getItem(KEYS.customers) || [],
    devices: getItem(KEYS.devices) || [],
    sessions: getItem(KEYS.sessions) || [],
    messages: getItem(KEYS.messages) || [],
    tickets: getItem(KEYS.tickets) || [],
    ticketLogs: getItem(KEYS.ticketLogs) || [],
    feedbacks: getItem(KEYS.feedbacks) || [],
    aiMetas: getItem(KEYS.aiMetas) || []
  }
  return JSON.stringify(data, null, 2)
}

// 会话相关
export const sessionStorage = {
  getAll: (): any[] => getItem<any[]>(KEYS.sessions) || [],
  add: (session: any) => appendItem(KEYS.sessions, session),
  update: (sessionId: string, updates: any) => updateItemInArray(KEYS.sessions, 'sessionId', sessionId, updates),
  getById: (sessionId: string) => {
    const sessions = getItem<any[]>(KEYS.sessions) || []
    return sessions.find((s) => s.sessionId === sessionId) || null
  }
}

// 消息相关
export const messageStorage = {
  getBySessionId: (sessionId: string) => {
    const messages = getItem<any[]>(KEYS.messages) || []
    return messages.filter((m) => m.sessionId === sessionId).sort((a, b) => 
      new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime()
    )
  },
  add: (message: any) => appendItem(KEYS.messages, message)
}

// 工单相关
export const ticketStorage = {
  getAll: () => getItem<any[]>(KEYS.tickets) || [],
  add: (ticket: any) => appendItem(KEYS.tickets, ticket),
  update: (ticketId: string, updates: any) => updateItemInArray(KEYS.tickets, 'ticketId', ticketId, updates),
  getById: (ticketId: string) => {
    const tickets = getItem<any[]>(KEYS.tickets) || []
    return tickets.find((t) => t.ticketId === ticketId) || null
  }
}

// 工单日志相关
export const ticketLogStorage = {
  getByTicketId: (ticketId: string) => {
    const logs = getItem<any[]>(KEYS.ticketLogs) || []
    return logs.filter((l) => l.ticketId === ticketId).sort((a, b) =>
      new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime()
    )
  },
  add: (log: any) => appendItem(KEYS.ticketLogs, log)
}

// 反馈相关
export const feedbackStorage = {
  add: (feedback: any) => appendItem(KEYS.feedbacks, feedback)
}

// AI 元数据相关
export const aiMetaStorage = {
  getBySessionId: (sessionId: string) => {
    const metas = getItem<any[]>(KEYS.aiMetas) || []
    return metas.filter((m) => m.sessionId === sessionId)
  },
  getByMessageId: (messageId: string) => {
    const metas = getItem<any[]>(KEYS.aiMetas) || []
    return metas.find((m) => m.relatedMessageId === messageId) || null
  },
  add: (meta: any) => appendItem(KEYS.aiMetas, meta)
}

// 客户相关
export const customerStorage = {
  getAll: () => getItem<any[]>(KEYS.customers) || [],
  getById: (customerId: string) => {
    const customers = getItem<any[]>(KEYS.customers) || []
    return customers.find((c) => c.customerId === customerId) || null
  }
}

// 设备相关
export const deviceStorage = {
  getAll: () => getItem<any[]>(KEYS.devices) || [],
  getById: (deviceId: string) => {
    const devices = getItem<any[]>(KEYS.devices) || []
    return devices.find((d) => d.deviceId === deviceId) || null
  },
  getByCustomerId: (customerId: string) => {
    const devices = getItem<any[]>(KEYS.devices) || []
    return devices.filter((d) => d.customerId === customerId)
  }
}
