/**
 * API 配置
 */
export const apiConfig = {
  // .NET 后端地址
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  
  // 请求超时（毫秒）
  timeout: 15000,
  
  // Python 服务地址（开发环境通过代理，生产环境需要配置）
  pythonApiBaseUrl: import.meta.env.VITE_PYTHON_API_BASE_URL || '/python-api',
  
  // .NET 后端内部 API Token（生产环境应该从环境变量读取）
  internalToken: import.meta.env.VITE_INTERNAL_TOKEN || 'test-token-123',
  
  // 默认租户 ID
  defaultTenant: import.meta.env.VITE_DEFAULT_TENANT || 'default'
}
