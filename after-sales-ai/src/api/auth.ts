import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000'

// 创建axios实例
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器 - 自动添加token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器 - 处理token过期等
api.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    if (error.response?.status === 401) {
      // Token过期或无效，清除本地存储并跳转到登录页
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// 登录接口
export const login = async (data: { account: string; password: string }) => {
  const response = await api.post('/api/auth/login', data)
  return response
}

// 注册接口（手机号注册时 deviceMN 必填）
export const register = async (data: { account: string; password: string; deviceMN?: string }) => {
  const response = await api.post('/api/auth/register', data)
  return response
}

// 获取当前用户信息
export const getCurrentUser = async () => {
  const response = await api.get('/api/auth/me')
  return response
}

// 修改密码
export const changePassword = async (data: { currentPassword: string; newPassword: string }) => {
  const response = await api.post('/api/auth/change-password', data)
  return response
}

// 更新个人资料
export const updateProfile = async (data: { status?: string }) => {
  const response = await api.put('/api/auth/profile', data)
  return response
}

// 导出axios实例供其他地方使用
export const authService = {
  login,
  register,
  getCurrentUser
}

export default api