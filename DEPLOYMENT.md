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

**`.env` 和 `.env.production` 什么时候用（条件）：**

| 条件 | 实际读取的文件 | 典型场景 |
|------|----------------|----------|
| 未设置环境变量 `APP_ENV`，或 `APP_ENV` ≠ `production` | **`.env`** | 本地开发、调试 |
| 已设置环境变量 `APP_ENV=production` | **`.env.production`** | 生产/预发部署 |

判断逻辑在 `app/core/config.py`：`os.getenv("APP_ENV") == "production"` 时用 `.env.production`，否则用 `.env`。生产环境建议：在服务器上维护 `.env.production`，启动前设置 `APP_ENV=production`（如 systemd 的 `Environment=APP_ENV=production` 或启动脚本里 `export APP_ENV=production`）。

```bash
# 1. 上传 ai-hub-ai/ 目录到服务器

# 2. 创建虚拟环境并安装依赖
cd /path/to/ai-hub-ai
python -m venv .venv
source .venv/bin/activate  # Linux
# .venv\Scripts\activate   # Windows
pip install -r requirements.txt

# 3. 配置环境变量（二选一）
# 方式 A：用 .env.production，启动时设 APP_ENV=production（见下方启动命令）
cp .env.production.example .env.production
# 编辑 .env.production：DOTNET_BASE_URL、INTERNAL_TOKEN、ATTACHMENT_BASE_PATH 等

# 方式 B：只用 .env（不设 APP_ENV 时默认读它）
cp .env.production.example .env
# 编辑 .env 填写生产配置

# 4. 启动服务（若用 .env.production，需先 export APP_ENV=production）
export APP_ENV=production   # 使用 .env.production 时必须
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 4.5 AI 对话审计与统计（为什么看不到记录/统计）

**功能是有的**：系统已实现「记录对话」和「统计报表」的完整链路。

- **记录**：用户通过**客服页面**（after-sales-ai 或接入 `POST /api/chat/search` 的页面）发消息时，Python 会调用 .NET 的 `internal/ai-audit` 接口，把会话、消息、决策、检索、响应写入数据库。
- **统计**：知识库管理前端（knowledgebase-frontend）的「AI 对话审计」「AI 统计报表」请求 .NET 的 `api/ai-audit` 接口，从上述审计表里查数据并展示。

**若对话列表/统计一直为空，请按下面检查：**

| 检查项 | 说明 |
|--------|------|
| 1. 审计表是否已建 | 必须执行过 `005_CreateAiAuditTables.sql`（与 .NET 使用同一数据库）。 |
| 2. Python 是否开启审计 | Python 的 `.env` 或 `.env.production` 中 `ENABLE_AUDIT_LOG=true`（默认 true）。 |
| 3. Python 能否调通 .NET | 配置 `DOTNET_BASE_URL`（.NET 实际地址）、`INTERNAL_TOKEN` 与 .NET 的 `InternalToken` 一致；Python 启动日志中会有「审计 API 创建会话」等日志。 |
| 4. 是否有真实对话 | 只有在**客服页面**发过消息才会产生记录；直接在知识库后台操作不会产生审计数据。 |

**快速自测**：在客服对话页发几条消息后，到知识库管理前端的「AI 对话审计」看是否出现会话；若有，统计报表也会随之有数据。

**时间显示不对**：审计时间在库中存的是 UTC。后端已统一按 UTC 返回（带 `Z`），前端会转成浏览器本地时间显示。若仍偏差 8 小时等，多半是之前未带 `Z` 被当成本地时间解析，重新拉列表即可；若服务器在中国，可确认 .NET 所在机器时区或 Nginx 所在机器时区无误。

**只记录了本地对话、服务器上对话没有**：说明服务器上的 Python 没有成功把审计数据写到 .NET（或写的不是同一套库）。请逐项确认：

| 项目 | 说明 |
|------|------|
| 同一数据库 | 服务器 .NET 连接的 SQL Server 必须已执行 `005_CreateAiAuditTables.sql`，且 Python 审计写的是同一台 .NET，数据才会进同一库。 |
| 服务器 Python 能访问 .NET | 在**部署 Python 的机器**上，`DOTNET_BASE_URL` 必须能访问到 .NET 服务。若 .NET 与 Python 同机，可用 `http://127.0.0.1:5000`；若不同机，填 .NET 的内网地址（如 `http://192.168.x.x:5000`），并保证防火墙/安全组放行。 |
| 生产环境未关审计 | 生产 `.env.production` 或运行时环境变量中 `ENABLE_AUDIT_LOG=true`，且不要覆盖为 `false`。 |
| 客服请求确实打到服务器 Python | 用户访问的客服页面（after-sales-ai）的接口地址必须是**服务器上的 Python**（如 Nginx 反向代理到 `http://127.0.0.1:8000`），否则对话只会记在本地或别的环境。 |

排查时可看服务器 Python 启动日志是否有「审计 API 创建会话」等；发一条客服消息后看是否有审计相关报错。

**使用域名访问客服（如 yonghongjituan.com:4013/cs/#/chat）没有增加新记录，而本地有**：说明请求已到服务器 Python，但审计未写入。按下面步骤做：

1. **先做自检**  
   在服务器上或本机浏览器访问（把域名和端口换成你实际部署的）：
   ```text
   https://www.yonghongjituan.com:4013/python-api/audit-status
   ```
   或：
   ```text
   http://服务器IP:Python端口/audit-status
   ```
   看返回里的 `audit_enabled`、`reason`、`dotnet_reachable`：
   - `audit_enabled: false` 且 `reason: "token_missing"` → 在**服务器**上给 Python 配置 `INTERNAL_TOKEN`（与 .NET 的 `InternalToken` 一致），并重启 Python。
   - `audit_enabled: false` 且 `reason: "disabled_by_config"` → 在**服务器**上把 Python 的 `ENABLE_AUDIT_LOG=true`，并重启。
   - `audit_enabled: true` 但 `dotnet_reachable: false` → 在**部署 Python 的那台机器**上，把 `DOTNET_BASE_URL` 改成能访问到 .NET 的地址（同机用 `http://127.0.0.1:5000`，不同机用 .NET 内网地址），并保证该机到 .NET 端口通（防火墙/安全组放行），然后重启 Python。

2. **确认 Nginx 把客服请求转到本机 Python**  
   用户访问的是 `域名:4013/cs/`，客服前端会请求同域的 `/python-api/api/chat/search`。Nginx 里要有类似：
   ```nginx
   location /python-api/ {
       rewrite ^/python-api/(.*) /$1 break;
       proxy_pass http://127.0.0.1:8000;   # 本机 Python 端口
       ...
   }
   ```
   这样请求才会打到**本机** Python，审计才会用本机的 `DOTNET_BASE_URL` 写 .NET。

3. **确认生产构建里客服前端的 Python 地址是相对路径**  
   构建客服前端（after-sales-ai）时，若不设 `VITE_PYTHON_API_BASE_URL`，会默认用相对路径 `/python-api`，即请求会发到当前域名（如 4013 端口），由 Nginx 转发到 Python。若构建时写死了别的机器地址，就会打到别的环境，审计就不会进当前 .NET 库。

按上面做完后，再用域名发一条客服消息，然后看「AI 对话审计」是否出现新会话；同时看服务器 Python 日志里是否有「审计 API 创建会话」或相关报错。

**日志出现「创建会话失败: All connection attempts failed」**：说明 **Python 连不上当前配置的 DOTNET_BASE_URL**（你当前是 `http://localhost:5000`）。在服务器上，`localhost` 指**本机**，所以：

- **若 .NET 和 Python 部署在同一台服务器**：必须在该机上**同时运行 .NET 服务**（监听 5000 端口），并把 Python 的 `DOTNET_BASE_URL` 设为 `http://127.0.0.1:5000`。若该机没跑 .NET 或没监听 5000，就会出现 All connection attempts failed。
- **若 .NET 在另一台机器**：Python 所在机的 `localhost:5000` 上没有 .NET，必须把 `DOTNET_BASE_URL` 改成 **.NET 所在机器的地址**，例如 `http://192.168.x.x:5000` 或 `http://dotnet主机名:5000`，并保证 Python 所在机到该地址的 5000 端口网络通（防火墙/安全组放行）。

改完后重启 Python，再访问 `/python-api/audit-status` 看 `dotnet_reachable` 是否为 `true`，然后再用域名发一条消息测试。

**若 .NET 对外是 https://www.yonghongjituan.com:6713**（即 6713 端口由 Nginx 或 Kestrel 提供）：

- **Python 与 .NET 在同一台机**：.NET 通常在本机监听 5000，Nginx 把 6713 转到 5000。把 Python 的 `DOTNET_BASE_URL` 设为 **`http://127.0.0.1:5000`**，并确认本机已启动 .NET（监听 5000）。
- **Python 在另一台机**：Python 不能连 `localhost`，应把 `DOTNET_BASE_URL` 设为 **`https://www.yonghongjituan.com:6713`**，并保证 6713 的 Nginx 把 **`/internal/`** 也转发到 .NET（见下方案例），否则审计接口调不通。

## 五、Nginx 配置

**说明**：
- 4013 端口需同时提供前端、.NET API、Python 服务
- 若 `/api/auth/login`、`/swagger` 返回 404，说明 `/api/` 未正确转发到 .NET，需检查下方配置
- 若 .NET 在**其他端口**（如 6713），前端 `.env` 的 `VITE_API_BASE` 需改为对应端口

```nginx
server {
    listen 4013 ssl;
    server_name www.yonghongjituan.com;

    ssl_certificate     /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # .NET 后端 API（必须，否则 /api/auth/login 等会 404）
    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Swagger 文档（可选）
    location /swagger {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # 客服前端（after-sales-ai，base=/cs/，地址 https://域名:4013/cs/#/）
    location /cs/ {
        alias /var/www/cs/dist/;
        index index.html;
        try_files $uri $uri/ /cs/index.html;
    }

    # 知识库前端
    location /learning/ {
        alias /var/www/ai-hub/dist/;
        index index.html;
        try_files $uri $uri/ /learning/index.html;
    }

    # .NET 内部接口（Python 审计写会话/消息等，若 Python 通过本机或 6713 访问 .NET 则必须转发）
    location /internal/ {
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
| 审计自检（排查域名无记录） | https://www.yonghongjituan.com:4013/python-api/audit-status | `audit_enabled`、`dotnet_reachable` 等 |

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
