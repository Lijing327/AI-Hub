# 部署指南

## 📋 部署前准备

### ⚠️ 重要提示

**数据库已连接生产环境（172.16.15.9），部署时无需修改数据库配置！**

只需要：
1. ✅ 部署后端服务到服务器
2. ✅ 部署前端应用到服务器
3. ✅ 配置文件访问URL（BaseUrl）
4. ✅ 配置CORS允许的前端域名
5. ✅ 配置前端API地址（如果前后端不同域名）

### 1. 服务器环境要求

- **操作系统**: Windows Server 2016+ 或 Linux (Ubuntu 20.04+)
- **.NET 运行时**: .NET 8.0 Runtime 或 SDK
- **数据库**: ✅ **已配置，无需修改**（172.16.15.9）
- **Web服务器**: IIS (Windows) 或 Nginx (Linux) 作为反向代理（可选）

### 2. 文件存储位置说明

**是的，文件会存储在部署后端服务的相应位置。**

上传的图片、视频、PDF文件会存储在：
```
{后端服务部署目录}/wwwroot/uploads/
```

例如：
- Windows: `C:\inetpub\wwwroot\ai-hub-service\wwwroot\uploads\`
- Linux: `/var/www/ai-hub-service/wwwroot/uploads/`

**重要提示**：
- 确保该目录有写权限
- 建议定期备份该目录
- 生产环境建议使用对象存储（OSS/MinIO）替代本地存储

---

## 🔧 部署配置修改

### ⚠️ 重要说明

**数据库已连接生产环境，无需修改数据库配置！**

当前开发环境已连接正式数据库（`172.16.15.9`），部署时只需要：
1. 修改文件访问URL（BaseUrl）
2. 配置CORS允许的前端域名
3. 前端API地址配置

### 1. 修改生产环境配置文件

编辑 `ai-hub-service/appsettings.Production.json`：

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
      "https://your-frontend-domain.com",
      "http://your-frontend-domain.com"
    ]
  },
  "EnableSwagger": false,
  "Logging": {
    "LogLevel": {
      "Default": "Information",
      "Microsoft.AspNetCore": "Warning"
    }
  },
  "AllowedHosts": "*"
}
```

**需要修改的配置项**：

| 配置项 | 说明 | 是否需要修改 | 示例 |
|--------|------|------------|------|
| `ConnectionStrings:DefaultConnection` | 数据库连接字符串 | ❌ **不需要**（已连接生产数据库） | 保持原样 |
| `FileStorage:BaseUrl` | 文件访问的基础URL | ✅ **需要** | `https://api.your-domain.com/uploads` |
| `CORS:AllowedOrigins` | 允许的前端域名 | ✅ **需要** | `["https://your-frontend-domain.com"]` |
| `EnableSwagger` | 是否启用Swagger（生产环境建议false） | ✅ **建议** | `false` |

### 2. 前端配置修改

#### 情况一：前后端部署在同一域名下（推荐）

如果前端和后端部署在同一个域名下（例如都通过Nginx/IIS），**无需修改**，代码已自动支持。

#### 情况二：前后端部署在不同域名

如果前端和后端部署在不同域名，需要创建 `.env.production` 文件：

```bash
cd knowledgebase-frontend
cp .env.production.example .env.production
```

编辑 `.env.production`：

```env
VITE_API_BASE_URL=https://api.your-domain.com/api
```

**生产环境构建**：
```bash
cd knowledgebase-frontend
npm run build
# 构建产物在 dist/ 目录
```

---

## 🚀 部署步骤

### Windows Server + IIS 部署

#### 1. 发布后端服务

```powershell
cd ai-hub-service
dotnet publish -c Release -o C:\inetpub\wwwroot\ai-hub-service
```

#### 2. 配置IIS

1. 在IIS管理器中创建新网站
2. 网站物理路径指向：`C:\inetpub\wwwroot\ai-hub-service`
3. 绑定域名和端口（如：`api.your-domain.com:80`）
4. 设置应用程序池为"无托管代码"
5. 确保应用程序池有读写权限

#### 3. 设置环境变量

在IIS应用程序池中设置：
- `ASPNETCORE_ENVIRONMENT=Production`

#### 4. 配置文件权限

确保以下目录有写权限：
- `wwwroot/uploads/` - 文件上传目录
- `logs/` - 日志目录（如果有）

```powershell
# 给IIS应用程序池用户添加写权限
icacls "C:\inetpub\wwwroot\ai-hub-service\wwwroot\uploads" /grant "IIS AppPool\YourAppPoolName:(OI)(CI)F"
```

#### 5. 部署前端

将 `knowledgebase-frontend/dist/` 目录内容部署到：
- 另一个IIS网站（前端）
- 或使用Nginx作为静态文件服务器

---

### Linux + Nginx 部署

#### 1. 发布后端服务

```bash
cd ai-hub-service
dotnet publish -c Release -o /var/www/ai-hub-service
```

#### 2. 创建systemd服务

创建 `/etc/systemd/system/ai-hub-service.service`：

```ini
[Unit]
Description=AI Hub Service
After=network.target

[Service]
Type=notify
WorkingDirectory=/var/www/ai-hub-service
ExecStart=/usr/bin/dotnet /var/www/ai-hub-service/ai-hub-service.dll
Restart=always
RestartSec=10
KillSignal=SIGINT
SyslogIdentifier=ai-hub-service
User=www-data
Environment=ASPNETCORE_ENVIRONMENT=Production
Environment=ASPNETCORE_URLS=http://localhost:5000

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl enable ai-hub-service
sudo systemctl start ai-hub-service
sudo systemctl status ai-hub-service
```

#### 3. 配置Nginx反向代理

创建 `/etc/nginx/sites-available/ai-hub-api`：

```nginx
server {
    listen 80;
    server_name api.your-domain.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection keep-alive;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # 静态文件直接由Nginx提供
    location /uploads {
        alias /var/www/ai-hub-service/wwwroot/uploads;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

启用配置：
```bash
sudo ln -s /etc/nginx/sites-available/ai-hub-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### 4. 设置文件权限

```bash
sudo chown -R www-data:www-data /var/www/ai-hub-service
sudo chmod -R 755 /var/www/ai-hub-service
sudo chmod -R 775 /var/www/ai-hub-service/wwwroot/uploads
```

#### 5. 部署前端

```bash
# 构建前端
cd knowledgebase-frontend
npm run build

# 部署到Nginx
sudo cp -r dist/* /var/www/html/
```

---

## 📁 文件存储位置总结

### 开发环境
```
d:\00-Project\AI\AI-Hub\ai-hub-service\wwwroot\uploads\
```

### 生产环境（Windows）
```
C:\inetpub\wwwroot\ai-hub-service\wwwroot\uploads\
```

### 生产环境（Linux）
```
/var/www/ai-hub-service/wwwroot/uploads/
```

**访问URL**：
- 开发：`http://localhost:5000/uploads/{文件名}`
- 生产：`https://api.your-domain.com/uploads/{文件名}`

---

## ⚠️ 重要注意事项

### 1. 文件存储建议

**当前方案（本地存储）**：
- ✅ 简单易用
- ❌ 不适合多服务器部署
- ❌ 需要手动备份
- ❌ 服务器磁盘空间限制

**推荐方案（生产环境）**：
- 使用对象存储服务（OSS/MinIO）
- 支持分布式部署
- 自动备份和容灾
- 可扩展性强

### 2. 安全配置

- [ ] 配置HTTPS证书
- [ ] 限制文件上传大小（当前50MB）
- [ ] 验证文件类型和内容
- [ ] 配置防火墙规则
- [ ] 定期备份数据库和文件

### 3. 性能优化

- [ ] 配置CDN加速静态文件访问
- [ ] 启用Gzip压缩
- [ ] 配置缓存策略
- [ ] 数据库连接池优化

### 4. 监控和日志

- [ ] 配置应用日志
- [ ] 监控服务器资源使用
- [ ] 设置告警机制
- [ ] 定期检查磁盘空间

---

## 🔄 更新部署

### 后端更新

```bash
# 停止服务
sudo systemctl stop ai-hub-service  # Linux
# 或 IIS中停止应用程序池

# 备份当前版本
cp -r /var/www/ai-hub-service /var/www/ai-hub-service.backup

# 发布新版本
dotnet publish -c Release -o /var/www/ai-hub-service

# 恢复配置文件
cp /var/www/ai-hub-service.backup/appsettings.Production.json /var/www/ai-hub-service/

# 启动服务
sudo systemctl start ai-hub-service
```

### 前端更新

```bash
cd knowledgebase-frontend
npm run build
# 将 dist/ 目录内容部署到Web服务器
```

---

## 📞 故障排查

### 常见问题

1. **文件上传失败**
   - 检查 `wwwroot/uploads` 目录权限
   - 检查磁盘空间
   - 查看应用日志

2. **无法访问上传的文件**
   - 检查静态文件服务配置
   - 检查Nginx/IIS配置
   - 检查文件URL是否正确

3. **数据库连接失败**
   - 检查连接字符串
   - 检查数据库服务器网络
   - 检查防火墙规则

---

## 📚 相关文档

- [.NET 部署文档](https://docs.microsoft.com/aspnet/core/host-and-deploy/)
- [IIS 部署指南](https://docs.microsoft.com/aspnet/core/host-and-deploy/iis/)
- [Linux 部署指南](https://docs.microsoft.com/aspnet/core/host-and-deploy/linux-nginx)
