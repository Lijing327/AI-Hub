
// ========== 开发环境（本地 npm run dev，Vite 代理到 localhost:5000）==========
const apiBase = '/api'
const pythonApiBaseUrl = '/python-api'

// ========== 生产环境（.NET 6713，Python 6714）==========
// const apiBase = 'https://www.yonghongjituan.com:6713/api'
// const pythonApiBaseUrl = 'https://www.yonghongjituan.com:6714/python-api'

export const apiConfig = {
  baseURL: apiBase,
  timeout: 15000,
  pythonApiBaseUrl,
  internalToken: 'your-internal-token',
  defaultTenant: 'default',
  attachmentBaseUrl: '',
  attachmentRemotePath: ''
}
