/**
 * API 配置（智能客服无需租户，任何人打开即用）
 */
export const apiConfig = {
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 10000
}
