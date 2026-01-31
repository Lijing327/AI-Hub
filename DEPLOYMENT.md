# AI-Hub 知识库系统 - 部署指南

## 一、系统架构

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   前端 (Vue3)    │────▶│  .NET 后端服务   │────▶│   SQL Server     │
│  /learning/      │     │   端口: 5000     │     │  172.16.15.9     │
└──────────────────┘     └──────────────────┘     └──────────────────┘
         │                        │
         ▼                        ▼
┌──────────────────┐     ┌──────────────────┐
│  Python AI 服务  │     │   附件存储目录   │
│   端口: 8000     │     │  (需运维提供)    │
└──────────────────┘     └──────────────────┘
```

## 二、部署包内容

```
部署包/
├── frontend/                    # 前端静态文件
│   └── dist/                    # npm run build 生成
├── dotnet-service/              # .NET 后端
│   └── publish/                 # dotnet publish 生成
├── python-service/              # Python AI 服务
│   └── ai-hub-ai/               # 整个目录
└── database/                    # 数据库脚本
    └── Migrations/              # SQL 迁移脚本
```

## 三、服务器环境要求

| 依赖 | 版本 | 说明 |
|------|------|------|
| .NET Runtime | 8.0+ | `dotnet --version` |
| Python | 3.10+ | `python --version` |
| ODBC Driver | 17/18 | SQL Server 驱动 |
| Nginx | 任意 | 反向代理 |

## 四、部署步骤

### 4.1 数据库初始化（如未执行过）

```bash
# 按顺序执行 SQL 脚本
sqlcmd -S 172.16.15.9 -U sa -P "密码" -i 001_InitialCreate.sql
sqlcmd -S 172.16.15.9 -U sa -P "密码" -i 002_RefactorToNewSchema.sql
sqlcmd -S 172.16.15.9 -U sa -P "密码" -i 003_AddSoftDeleteFields.sql
sqlcmd -S 172.16.15.9 -U sa -P "密码" -i 004_AddChunkUniqueIndex.sql
sqlcmd -S 172.16.15.9 -U sa -P "密码" -i 005_CreateAiAuditTables.sql
```

### 4.2 前端部署

1. 将 `dist/` 目录内容上传到服务器静态文件目录
2. Nginx 配置见下方

### 4.3 .NET 后端部署

```bash
# 1. 上传 publish/ 目录到服务器

# 2. 修改 appsettings.Production.json 中的附件路径
#    "AttachmentStorage.BasePath": "服务器附件目录绝对路径"

# 3. 启动服务
cd /path/to/publish
export ASPNETCORE_ENVIRONMENT=Production
dotnet ai-hub-service.dll --urls "http://0.0.0.0:5000"
```

### 4.4 Python 服务部署

```bash
# 1. 上传 ai-hub-ai/ 目录到服务器

# 2. 创建虚拟环境并安装依赖
cd /path/to/ai-hub-ai
python -m venv .venv
source .venv/bin/activate  # Linux
# .venv\Scripts\activate   # Windows
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.production .env
# 修改 .env 中的 ATTACHMENT_BASE_PATH 为服务器附件目录

# 4. 启动服务
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 五、Nginx 配置

```nginx
server {
    listen 4013 ssl;
    server_name www.yonghongjituan.com;

    ssl_certificate     /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # 前端静态文件
    location /learning/ {
        alias /var/www/ai-hub/dist/;
        index index.html;
        try_files $uri $uri/ /learning/index.html;
    }

    # .NET 后端 API
    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 附件文件
    location /uploads/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
    }

    # Python AI 服务
    location /python-api/ {
        rewrite ^/python-api/(.*) /$1 break;
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        client_max_body_size 100M;
    }
}
```

## 六、需要运维提供/配置的信息

| 项目 | 说明 |
|------|------|
| **附件目录绝对路径** | 用于存放图片/视频/文档附件，需要 .NET 服务有读取权限 |
| **SSL 证书路径** | Nginx HTTPS 配置 |

**获取附件目录后，需修改：**
1. `appsettings.Production.json` → `AttachmentStorage.BasePath`
2. `.env` (Python) → `ATTACHMENT_BASE_PATH`

## 七、健康检查

| 服务 | URL | 预期 |
|------|-----|------|
| 前端 | https://www.yonghongjituan.com:4013/learning/ | 显示页面 |
| 后端 API | https://www.yonghongjituan.com:4013/api/knowledgearticles | JSON 响应 |
| Python | https://www.yonghongjituan.com:4013/python-api/health | `{"status":"ok"}` |

## 八、进程管理（建议使用 systemd）

### .NET 服务

```ini
# /etc/systemd/system/ai-hub-dotnet.service
[Unit]
Description=AI-Hub .NET Service
After=network.target

[Service]
WorkingDirectory=/opt/ai-hub/dotnet-service
Environment=ASPNETCORE_ENVIRONMENT=Production
ExecStart=/usr/bin/dotnet ai-hub-service.dll --urls "http://0.0.0.0:5000"
Restart=always
RestartSec=10
User=www-data

[Install]
WantedBy=multi-user.target
```

### Python 服务

```ini
# /etc/systemd/system/ai-hub-python.service
[Unit]
Description=AI-Hub Python Service
After=network.target

[Service]
WorkingDirectory=/opt/ai-hub/python-service
ExecStart=/opt/ai-hub/python-service/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10
User=www-data

[Install]
WantedBy=multi-user.target
```

启动命令：
```bash
systemctl daemon-reload
systemctl enable ai-hub-dotnet ai-hub-python
systemctl start ai-hub-dotnet ai-hub-python
```

## 九、常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| 页面空白 | 后端未启动或 Nginx 未配置 API 代理 | 检查后端启动日志，检查 Nginx 配置 |
| 附件无法显示 | BasePath 路径错误或无权限 | 检查路径和权限 |
| Python 调用 .NET 返回 401 | Token 不一致 | 确保两边 InternalToken 相同 |
| Excel 导入失败 | ODBC 驱动未安装 | 安装 ODBC Driver 17 for SQL Server |

## 十、联系方式

如有问题，请联系开发人员。
