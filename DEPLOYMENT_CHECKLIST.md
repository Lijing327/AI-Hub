# 部署检查清单

## ✅ 部署前检查

### 数据库配置
- [x] 数据库已连接生产环境（172.16.15.9）
- [x] 数据库连接字符串无需修改
- [ ] 确认数据库服务器可访问

### 后端配置
- [ ] 修改 `appsettings.Production.json` 中的 `FileStorage:BaseUrl`
- [ ] 修改 `appsettings.Production.json` 中的 `CORS:AllowedOrigins`
- [ ] 确认 `EnableSwagger` 设置为 `false`（生产环境）

### 前端配置
- [ ] 如果前后端不同域名，创建 `.env.production` 并配置 `VITE_API_BASE_URL`
- [ ] 如果前后端同域名，无需修改（已自动支持）

---

## 🚀 部署步骤

### 后端部署

1. [ ] 发布后端服务
   ```bash
   cd ai-hub-service
   dotnet publish -c Release -o {部署目录}
   ```

2. [ ] 复制生产环境配置文件
   ```bash
   cp appsettings.Production.json {部署目录}/appsettings.Production.json
   ```

3. [ ] 设置环境变量
   - Windows: `ASPNETCORE_ENVIRONMENT=Production`
   - Linux: 在 systemd 服务文件中设置

4. [ ] 配置 Web 服务器（IIS/Nginx）

5. [ ] 设置文件目录权限
   - `wwwroot/uploads/` 目录需要有写权限

### 前端部署

1. [ ] 构建前端
   ```bash
   cd knowledgebase-frontend
   npm install
   npm run build
   ```

2. [ ] 部署 `dist/` 目录到 Web 服务器

3. [ ] 配置 Web 服务器（IIS/Nginx）提供静态文件服务

---

## 🔍 部署后验证

### 后端验证
- [ ] 访问 `https://api.your-domain.com/swagger`（如果启用）
- [ ] 测试 API 接口：`GET /api/knowledgeitems/search`
- [ ] 检查日志，确认无错误

### 前端验证
- [ ] 访问前端页面，确认可以正常加载
- [ ] 测试搜索功能
- [ ] 测试创建/编辑知识条目
- [ ] 测试文件上传功能
- [ ] 检查浏览器控制台，确认无错误

### 文件上传验证
- [ ] 上传一个测试文件
- [ ] 确认文件保存在 `wwwroot/uploads/` 目录
- [ ] 通过URL访问上传的文件，确认可以正常访问

---

## ⚠️ 常见问题

### 问题1：前端无法连接后端API
- [ ] 检查CORS配置是否正确
- [ ] 检查前端API地址配置
- [ ] 检查网络连接和防火墙

### 问题2：文件上传失败
- [ ] 检查 `wwwroot/uploads` 目录权限
- [ ] 检查磁盘空间
- [ ] 查看后端日志

### 问题3：无法访问上传的文件
- [ ] 检查静态文件服务配置
- [ ] 检查文件URL是否正确
- [ ] 检查Web服务器配置

---

## 📝 配置示例

### appsettings.Production.json 示例

```json
{
  "ConnectionStrings": {
    "DefaultConnection": "Server=172.16.15.9;Database=ai_hub;User Id=sa;Password=pQdr2f@K3.Stp6Qs3hkP;TrustServerCertificate=true;"
  },
  "FileStorage": {
    "LocalPath": "wwwroot/uploads",
    "BaseUrl": "https://api.your-domain.com/uploads"
  },
  "CORS": {
    "AllowedOrigins": [
      "https://your-frontend-domain.com"
    ]
  },
  "EnableSwagger": false
}
```

### .env.production 示例（前后端不同域名时）

```env
VITE_API_BASE_URL=https://api.your-domain.com/api
```

---

## 📞 需要帮助？

如果遇到问题，请查看：
- [详细部署文档](./DEPLOYMENT.md)
- [故障排查指南](./TROUBLESHOOTING.md)
