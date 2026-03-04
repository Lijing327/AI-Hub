/**
 * API 配置，与 after-sales-ai 一致：dev 用相对路径走代理，build 用 .env.production 中的完整地址
 * VITE_API_BASE：.NET 后端根地址（如 https://www.yonghongjituan.com:6713），空则用相对路径 /api
 * VITE_API_BASE_URL：可选，直接覆盖 baseURL（优先级高于 VITE_API_BASE）
 */
const apiBase = import.meta.env.VITE_API_BASE ?? ''
const explicitBaseUrl = import.meta.env.VITE_API_BASE_URL ?? ''

export const apiConfig = {
  // .NET 后端地址：显式 > VITE_API_BASE + /api > 相对路径 /api
  baseURL: explicitBaseUrl || (apiBase ? `${apiBase}/api` : '/api'),
  
  // 请求超时（毫秒）
  timeout: 15000,
  
  // Python 服务地址（与 after-sales-ai 一致：VITE_PYTHON_BASE 或 VITE_PYTHON_API_BASE_URL，空则用相对路径）
  pythonApiBaseUrl: import.meta.env.VITE_PYTHON_API_BASE_URL || (import.meta.env.VITE_PYTHON_BASE ? `${import.meta.env.VITE_PYTHON_BASE}/python-api` : '') || '/python-api',
  
  // .NET 后端内部 API Token（生产环境应该从环境变量读取）
  internalToken: import.meta.env.VITE_INTERNAL_TOKEN || 'test-token-123',
  
  // 默认租户 ID
  defaultTenant: import.meta.env.VITE_DEFAULT_TENANT || 'default',

  // 附件访问地址（生产环境：数据库可能存的是本地 URL，展示时重写为远程地址）
  attachmentBaseUrl: import.meta.env.VITE_ATTACHMENT_BASE_URL || '',
  attachmentRemotePath: import.meta.env.VITE_ATTACHMENT_REMOTE_PATH || ''
}
