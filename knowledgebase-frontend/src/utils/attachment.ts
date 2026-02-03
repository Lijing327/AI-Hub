/**
 * 附件展示 URL 处理：开发环境走代理，生产环境将本地 URL 重写为远程附件地址
 */
import { apiConfig } from '../config/api'

/**
 * 将数据库中的附件 URL（可能为 localhost/uploads/...）转为前端实际可访问的地址
 */
export function getAttachmentDisplayUrl(fileUrl: string | undefined): string {
  if (!fileUrl) return ''

  // 开发环境：localhost:5000 转为相对路径走代理
  if (import.meta.env.DEV) {
    if (fileUrl.startsWith('http://localhost:5000/')) {
      return fileUrl.replace('http://localhost:5000', '')
    }
    if (fileUrl.startsWith('http://localhost:5000')) {
      return fileUrl.replace('http://localhost:5000', '')
    }
  }

  // 生产环境：若配置了远程附件地址，将本地/uploads 的 URL 重写为远程地址
  const base = apiConfig.attachmentBaseUrl?.trim()
  const remotePath = apiConfig.attachmentRemotePath?.replace(/\\/g, '/').replace(/\/+$/, '')
  const isLocalUrl = /localhost|:\d+\/uploads\//.test(fileUrl)
  if (base && remotePath && isLocalUrl) {
    const parts = fileUrl.replace(/#.*$/, '').split('/')
    const fileName = parts[parts.length - 1] ? decodeURIComponent(parts[parts.length - 1]) : ''
    if (fileName) {
      const encodedPath = remotePath.split('/').map((p: string) => encodeURIComponent(p)).join('/')
      const encodedName = encodeURIComponent(fileName)
      return `${base.replace(/\/+$/, '')}/uploads/${encodedPath}/${encodedName}`
    }
  }

  return fileUrl
}
