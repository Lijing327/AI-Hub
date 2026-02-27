/**
 * 通用 API 服务
 */
import axios from 'axios'
import { apiConfig } from '@/config/api'

// 创建 axios 实例
const api = axios.create({
  baseURL: apiConfig.baseURL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器：添加认证头
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }

    // 添加租户 ID 头
    const tenantId = localStorage.getItem('tenant_id') || 'default'
    config.headers['X-Tenant-Id'] = tenantId

    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器：处理错误
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // token 过期或无效，跳转到登录页
      localStorage.removeItem('token')
      window.location.hash = '/login'
    }
    return Promise.reject(error)
  }
)

export default api
