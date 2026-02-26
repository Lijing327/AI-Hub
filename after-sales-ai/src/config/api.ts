/**
 * API 配置，base 由 VITE_API_BASE 决定
 */
const base = import.meta.env.VITE_API_BASE ?? ''
export const apiConfig = {
  baseURL: base ? `${base}/api` : '/api',
  timeout: 10000
}
