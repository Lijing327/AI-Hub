/**
 * API 配置
 */
export const apiConfig = {
  // API 基础地址
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  
  // 默认租户 ID（暂时不处理登录，使用默认值）
  defaultTenant: import.meta.env.VITE_DEFAULT_TENANT || 'default',
  
  // 请求超时时间
  timeout: 10000
}
