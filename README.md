# 知识库录入与管理系统 MVP

## 项目简介

这是一个企业级知识库录入与管理系统的MVP版本，支持知识条目的创建、编辑、发布、搜索等功能，并预留了向量化接口用于后续的智能检索。

## 技术栈

- **前端**: Vue3 + TypeScript + Element Plus + Vite
- **后端**: .NET 8 WebAPI + Entity Framework Core
- **数据库**: SQL Server 2019+
- **文件存储**: 本地存储（兼容后续OSS/MinIO）

## 项目结构

```
.
├── ai-hub-service/             # 后端API项目
│   ├── Controllers/            # API控制器
│   ├── Data/                   # 数据库上下文
│   ├── DTOs/                   # 数据传输对象
│   ├── Models/                 # 实体模型
│   ├── Services/               # 业务服务层
│   └── Database/               # 数据库脚本
├── knowledgebase-frontend/     # 前端项目
│   ├── src/
│   │   ├── api/                # API接口
│   │   ├── router/             # 路由配置
│   │   ├── types/              # TypeScript类型定义
│   │   └── views/              # 页面组件
│   └── package.json
└── README.md
```

## 功能特性

### 1. 知识条目管理
- ✅ 创建、编辑、删除知识条目
- ✅ 支持标题、问题描述、原因分析、解决方案等字段
- ✅ 支持适用范围（JSON格式）和标签
- ✅ 状态管理：草稿(draft)、已发布(published)、已归档(archived)

### 2. 附件管理
- ✅ 支持图片、视频、PDF文件上传
- ✅ 附件与知识条目绑定
- ✅ 文件本地存储，返回可访问URL
- ✅ 附件预览和下载

### 3. 发布功能
- ✅ 发布时自动生成知识块（chunk）
- ✅ 将question/cause/solution合并后切分
- ✅ 预留向量化服务接口（IndexService.UpsertEmbeddings）

### 4. 搜索与过滤
- ✅ 关键词搜索（标题/问题/解决方案）
- ✅ 按状态过滤
- ✅ 按标签过滤
- ✅ 按适用范围过滤（简单匹配）
- ✅ 分页支持

### 5. 前端页面
- ✅ 知识列表页：搜索+过滤+表格+操作
- ✅ 知识编辑页：结构化输入+附件上传
- ✅ 知识详情页：展示+附件预览

## 快速开始

### 环境要求

- .NET 8 SDK
- Node.js 18+
- SQL Server 2019+ 或 SQL Server Express
- Visual Studio 2022 或 VS Code（推荐）

### 后端启动步骤

1. **配置数据库连接**

   数据库连接字符串已配置在 `ai-hub-service/appsettings.json` 中，连接到AI能力统一数据中枢 `ai_hub`：

   ```json
   {
     "ConnectionStrings": {
       "DefaultConnection": "Server=172.16.15.9;Database=ai_hub;User Id=sa;Password=pQdr2f@K3.Stp6Qs3hkP;TrustServerCertificate=true;"
     }
   }
   ```

   > **数据库说明**：`ai_hub` 是公司所有 AI 能力的统一数据中枢，负责存储 AI 知识、向量、切片、对话及智能体相关数据，与业务系统解耦。执行SQL脚本时会自动创建该数据库。

2. **创建数据库和表**

   在SQL Server Management Studio (SSMS) 中连接到 `172.16.15.9` 服务器，执行 `ai-hub-service/Database/Migrations/001_InitialCreate.sql` 脚本。脚本会自动创建 `ai_hub` 数据库和所有表结构。

   或使用sqlcmd：

   ```bash
   sqlcmd -S 172.16.15.9 -U sa -P "pQdr2f@K3.Stp6Qs3hkP" -i ai-hub-service/Database/Migrations/001_InitialCreate.sql
   ```

3. **运行后端项目**

   ```bash
   cd ai-hub-service
   dotnet restore
   dotnet run
   ```

   后端API将在 `http://localhost:5000` 启动。

   Swagger文档地址：`http://localhost:5000/swagger`

### 前端启动步骤

1. **安装依赖**

   ```bash
   cd knowledgebase-frontend
   npm install
   ```

2. **启动开发服务器**

   ```bash
   npm run dev
   ```

   前端应用将在 `http://localhost:5173` 启动。

## 配置说明

### 后端配置（appsettings.json）

```json
{
  "ConnectionStrings": {
    "DefaultConnection": "Server=172.16.15.9;Database=ai_hub;User Id=sa;Password=pQdr2f@K3.Stp6Qs3hkP;TrustServerCertificate=true;"
  },
  "FileStorage": {
    "LocalPath": "wwwroot/uploads",        // 文件存储本地路径
    "BaseUrl": "http://localhost:5000/uploads"  // 文件访问基础URL
  }
}
```

### 前端配置

前端通过Vite代理配置连接到后端API，无需额外配置。如需修改API地址，编辑 `knowledgebase-frontend/vite.config.ts`：

```typescript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:5000',  // 后端API地址
      changeOrigin: true
    }
  }
}
```

## API接口说明

### 知识条目接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/knowledgeitems/{id}` | 获取知识条目详情 |
| GET | `/api/knowledgeitems/search` | 搜索知识条目（支持分页） |
| POST | `/api/knowledgeitems` | 创建知识条目 |
| PUT | `/api/knowledgeitems/{id}` | 更新知识条目 |
| DELETE | `/api/knowledgeitems/{id}` | 删除知识条目 |
| POST | `/api/knowledgeitems/{id}/publish` | 发布知识条目 |

### 附件接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/attachments/upload` | 上传附件（form-data） |
| DELETE | `/api/attachments/{id}` | 删除附件 |
| GET | `/api/attachments/knowledge-item/{knowledgeItemId}` | 获取知识条目的附件列表 |

### 请求示例

**创建知识条目：**

```json
POST /api/knowledgeitems
Content-Type: application/json

{
  "title": "产品故障排查指南",
  "questionText": "产品无法启动",
  "causeText": "可能是电源问题",
  "solutionText": "检查电源连接，重启设备",
  "scopeJson": "{\"region\": \"华东\", \"product\": \"产品A\"}",
  "tags": "故障,排查,电源",
  "createdBy": "admin",
  "tenantId": "default"
}
```

**搜索知识条目：**

```
GET /api/knowledgeitems/search?keyword=故障&status=published&pageIndex=1&pageSize=20
```

**上传附件：**

```
POST /api/attachments/upload
Content-Type: multipart/form-data

knowledgeItemId: 1
file: [文件]
```

## 数据库表结构

### kb_item（知识条目表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT | 主键 |
| title | VARCHAR(500) | 标题 |
| question_text | NVARCHAR(MAX) | 问题描述 |
| cause_text | NVARCHAR(MAX) | 原因分析 |
| solution_text | NVARCHAR(MAX) | 解决方案 |
| scope_json | NVARCHAR(MAX) | 适用范围（JSON格式） |
| tags | VARCHAR(1000) | 标签 |
| status | VARCHAR(20) | 状态 |
| version | INT | 版本号 |
| tenant_id | VARCHAR(50) | 租户ID |
| created_by | VARCHAR(100) | 创建人 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |
| published_at | DATETIME | 发布时间 |

### kb_attachment（附件表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT | 主键 |
| knowledge_item_id | INT | 知识条目ID |
| file_name | VARCHAR(500) | 文件名 |
| file_path | VARCHAR(1000) | 文件路径 |
| file_url | VARCHAR(1000) | 文件URL |
| file_type | VARCHAR(50) | 文件类型 |
| file_size | BIGINT | 文件大小 |
| created_at | DATETIME | 创建时间 |

### kb_chunk（知识块表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT | 主键 |
| knowledge_item_id | INT | 知识条目ID |
| chunk_text | NVARCHAR(MAX) | 块文本 |
| chunk_index | INT | 块索引 |
| created_at | DATETIME | 创建时间 |

## 开发说明

### 向量化服务接口

向量化服务接口已预留，位于 `ai-hub-service/Services/IndexService.cs`。当前实现仅打日志占位，后续可接入：

- Milvus
- Pinecone
- Qdrant
- 自建向量数据库

实现 `UpsertEmbeddingsAsync` 方法即可。

### 文件存储扩展

当前使用本地存储，如需接入OSS/MinIO，可修改 `AttachmentService.cs` 中的文件上传逻辑。接口设计已兼容，只需替换存储实现即可。

### 代码注释

所有代码注释均使用中文，符合项目规范。

## 常见问题

### 1. 数据库连接失败

- 检查SQL Server服务是否启动（服务器地址：172.16.15.9）
- 确认连接字符串中的用户名、密码是否正确
- 执行SQL脚本会自动创建 `ai_hub` 数据库，如果数据库已存在，脚本会跳过创建步骤
- 检查网络连接，确保可以访问 172.16.15.9 服务器
- 检查防火墙设置，确保SQL Server端口（默认1433）可访问

### 2. 文件上传失败

- 检查 `wwwroot/uploads` 目录是否存在且有写权限
- 确认文件大小不超过50MB
- 确认文件类型为图片/视频/PDF

### 3. 前端无法连接后端

- 确认后端API已启动（http://localhost:5000）
- 检查Vite代理配置是否正确
- 查看浏览器控制台错误信息

## 后续优化方向

1. **向量化集成**：接入向量数据库，实现语义搜索
2. **文件存储**：迁移到OSS/MinIO，支持分布式存储
3. **权限管理**：添加用户认证和权限控制
4. **多租户**：完善多租户隔离机制
5. **版本管理**：知识条目版本历史记录
6. **批量操作**：支持批量导入、导出
7. **全文检索**：集成Elasticsearch等搜索引擎

## 许可证

本项目为内部项目，仅供企业内部使用。

## 联系方式

如有问题或建议，请联系开发团队。
