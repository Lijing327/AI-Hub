# AiHub.Service 工程化汇报

**汇报时间**: 2026-01-24  
**项目名称**: ai-hub-service  
**技术栈**: .NET 8.0 WebAPI + EF Core + SQL Server 2019+

---

## 一、工程概况

### 1) Solution/项目结构

**.sln 名称**: `ai-hub-service.sln`  
**位置**: `d:\00-Project\AI\AI-Hub\ai-hub-service\ai-hub-service.sln`

**项目结构说明**:
- **架构模式**: 单项目架构（非分层架构，所有代码在同一项目中）
- **项目文件**: `ai-hub-service.csproj` (目标框架: .NET 8.0)

**关键目录树**:
```
ai-hub-service/
├── Controllers/              # API控制器层
│   ├── KnowledgeItemsController.cs    # 知识条目API (路由: /api/knowledgeitems)
│   └── AttachmentsController.cs        # 附件API (路由: /api/attachments)
├── Services/                 # 业务服务层
│   ├── IKnowledgeArticleService.cs
│   ├── KnowledgeArticleService.cs     # 知识条目服务实现
│   ├── IAssetService.cs
│   ├── AssetService.cs                # 附件服务实现
│   ├── IIndexService.cs
│   └── IndexService.cs                 # 向量化服务（占位实现）
├── Data/                     # 数据访问层
│   └── ApplicationDbContext.cs        # EF Core DbContext
├── Models/                   # 实体模型
│   ├── KnowledgeArticle.cs            # kb_article 实体
│   ├── Asset.cs                       # kb_asset 实体
│   └── KnowledgeChunk.cs              # kb_chunk 实体
├── DTOs/                     # 数据传输对象
│   ├── KnowledgeArticleDto.cs
│   ├── AssetDto.cs
│   └── PagedResultDto.cs
├── Database/                 # 数据库迁移脚本
│   └── Migrations/
│       ├── 001_InitialCreate.sql
│       ├── 002_RefactorToNewSchema.sql
│       └── 003_AddSoftDeleteFields.sql
├── Program.cs                # 应用入口和配置
├── appsettings.json          # 开发环境配置
└── appsettings.Production.json  # 生产环境配置
```

**注意**: 当前项目**未采用分层架构**（无 Application/Domain/Infrastructure 分离），所有代码集中在单一 WebAPI 项目中。

### 2) 运行方式

**本地启动命令/方式**:
```bash
# 方式1: 使用 dotnet CLI
cd d:\00-Project\AI\AI-Hub\ai-hub-service
dotnet run

# 方式2: 使用 Visual Studio / Rider
# 直接运行项目，或按 F5 启动
```

**启动后监听地址**:
- **开发环境**: `http://localhost:5000` (在 `Program.cs` 第41行配置)
- **HTTPS**: 未配置（仅HTTP）

**Swagger 地址**:
- **开发环境**: `http://localhost:5000/swagger`
- **生产环境**: 默认禁用（可通过 `appsettings.Production.json` 中的 `EnableSwagger: true` 启用）

**appsettings.json 配置项**:

**文件路径**: `d:\00-Project\AI\AI-Hub\ai-hub-service\appsettings.json`

```json
{
  "ConnectionStrings": {
    "DefaultConnection": "Server=172.16.15.9;Database=ai_hub;User Id=sa;Password=pQdr2f@K3.Stp6Qs3hkP;TrustServerCertificate=true;"
  },
  "FileStorage": {
    "LocalPath": "wwwroot/uploads",
    "BaseUrl": "http://localhost:5000/uploads"
  },
  "CORS": {
    "AllowedOrigins": ["http://localhost:5173", "http://localhost:3000"]
  }
}
```

**关键配置说明**:
- **SQL Server 连接串**: `Server=172.16.15.9;Database=ai_hub;...` (生产数据库)
- **上传目录**: `wwwroot/uploads` (相对路径，实际路径为 `{ContentRootPath}/wwwroot/uploads`)
- **文件访问URL**: `http://localhost:5000/uploads/{文件名}`

---

## 二、数据库（SQL Server / ai_hub）

### 1) EF Core 使用情况

**DbContext 类名 + 文件路径**:
- **类名**: `ApplicationDbContext`
- **文件路径**: `d:\00-Project\AI\AI-Hub\ai-hub-service\Data\ApplicationDbContext.cs`
- **命名空间**: `ai_hub_service.Data`

**Migration 是否已生成**:
- ❌ **未使用 EF Core Migrations** (无 `dotnet ef migrations add` 生成的迁移)
- ✅ **使用手动 SQL 脚本**进行数据库结构管理

**SQL 迁移脚本列表**:
1. `001_InitialCreate.sql` - 初始表结构（如果存在）
2. `002_RefactorToNewSchema.sql` - 表结构重构（kb_item→kb_article, kb_attachment→kb_asset）
3. `003_AddSoftDeleteFields.sql` - 添加软删除字段

**数据库是否已成功创建并更新**:
- ✅ **数据库已创建**: `ai_hub` 数据库存在于 `172.16.15.9`
- ✅ **表结构已落地**: 通过执行 SQL 脚本完成
- ⚠️ **未使用 `dotnet ef database update`**: 项目采用手动执行 SQL 脚本的方式

### 2) 表是否已落地

**表名规范**: 实际表名为 `kb_article`、`kb_asset`、`kb_chunk`（**非** `ai_kb_*` 前缀）

#### ✅ dbo.kb_article（知识主表）

**是否存在**: ✅ 是  
**创建脚本**: `Database/Migrations/002_RefactorToNewSchema.sql` (第14-40行)

**字段清单**:
| 字段名 | 类型 | 说明 | 是否齐全 |
|--------|------|------|----------|
| id | INT IDENTITY(1,1) | 主键 | ✅ |
| tenant_id | NVARCHAR(50) | 租户ID | ✅ |
| title | NVARCHAR(500) NOT NULL | 知识标题 | ✅ |
| question_text | NVARCHAR(MAX) | 用户问题/现象描述 | ✅ |
| cause_text | NVARCHAR(MAX) | 原因分析 | ✅ |
| solution_text | NVARCHAR(MAX) | 解决步骤 | ✅ |
| scope_json | NVARCHAR(MAX) | 适用范围（JSON格式） | ✅ |
| tags | NVARCHAR(1000) | 标签（逗号分隔） | ✅ |
| status | NVARCHAR(20) NOT NULL DEFAULT 'draft' | 状态 | ✅ |
| version | INT DEFAULT 1 | 版本号 | ✅ |
| created_by | NVARCHAR(100) | 创建人 | ✅ |
| created_at | DATETIME NOT NULL DEFAULT GETDATE() | 创建时间 | ✅ |
| updated_at | DATETIME | 更新时间 | ✅ |
| published_at | DATETIME | 发布时间 | ✅ |
| deleted_at | DATETIME | 软删除标记 | ✅ |

**索引清单**:
- ✅ `idx_tenant_id` ON (tenant_id)
- ✅ `idx_status` ON (status)
- ✅ `idx_created_at` ON (created_at)
- ✅ `idx_tenant_status` ON (tenant_id, status)
- ✅ `idx_deleted_at` ON (deleted_at)

**差异清单**: 无差异，字段齐全

#### ✅ dbo.kb_asset（附件表）

**是否存在**: ✅ 是  
**创建脚本**: `Database/Migrations/002_RefactorToNewSchema.sql` (第43-65行)

**字段清单**:
| 字段名 | 类型 | 说明 | 是否齐全 |
|--------|------|------|----------|
| id | INT IDENTITY(1,1) | 主键 | ✅ |
| tenant_id | NVARCHAR(50) | 租户ID | ✅ |
| article_id | INT NOT NULL | 关联的知识条目ID | ✅ |
| asset_type | NVARCHAR(50) NOT NULL | 资产类型：image/video/pdf/other | ✅ |
| file_name | NVARCHAR(500) NOT NULL | 文件名 | ✅ |
| url | NVARCHAR(1000) NOT NULL | URL（OSS/本地路径） | ✅ |
| size | BIGINT | 文件大小（字节） | ✅ |
| duration | INT | 视频时长（秒，可选） | ✅ |
| created_at | DATETIME NOT NULL DEFAULT GETDATE() | 创建时间 | ✅ |
| deleted_at | DATETIME | 软删除标记 | ✅ |

**FK 是否存在**: ✅ 是
- **外键**: `FOREIGN KEY (article_id) REFERENCES kb_article(id) ON DELETE CASCADE`
- **位置**: `002_RefactorToNewSchema.sql` 第57行

**索引清单**:
- ✅ `idx_tenant_id` ON (tenant_id)
- ✅ `idx_article_id` ON (article_id)
- ✅ `idx_asset_type` ON (asset_type)
- ✅ `idx_deleted_at` ON (deleted_at)

**差异清单**: 无差异，字段齐全

#### ✅ dbo.kb_chunk（入库切片表）

**是否存在**: ✅ 是  
**创建脚本**: `Database/Migrations/002_RefactorToNewSchema.sql` (第68-114行)

**字段清单**:
| 字段名 | 类型 | 说明 | 是否齐全 |
|--------|------|------|----------|
| id | INT IDENTITY(1,1) | 主键 | ✅ |
| tenant_id | NVARCHAR(50) | 租户ID | ✅ |
| article_id | INT NOT NULL | 关联的知识条目ID | ✅ |
| chunk_index | INT NOT NULL | 块索引 | ✅ |
| chunk_text | NVARCHAR(MAX) NOT NULL | 块文本 | ✅ |
| hash | NVARCHAR(64) | SHA256 hash用于去重 | ✅ |
| source_fields | NVARCHAR(100) | 来自 question/cause/solution 哪部分 | ✅ |
| created_at | DATETIME NOT NULL DEFAULT GETDATE() | 创建时间 | ✅ |

**唯一索引 tenant_id+hash 是否存在**: ❌ **不存在**

**当前索引**:
- ✅ `idx_tenant_id` ON (tenant_id)
- ✅ `idx_article_id` ON (article_id)
- ✅ `idx_hash` ON (hash)

**差异清单**:
- ⚠️ **缺少唯一索引**: 未创建 `UNIQUE INDEX UX_kb_chunk_tenant_hash ON (tenant_id, hash)` 用于去重
- **建议**: 在 `002_RefactorToNewSchema.sql` 中添加：
  ```sql
  CREATE UNIQUE INDEX UX_kb_chunk_tenant_hash ON kb_chunk(tenant_id, hash) 
  WHERE hash IS NOT NULL;
  ```

---

## 三、接口实现情况（/api/knowledgeitems 和 /api/attachments）

**基础路由说明**:
- 知识条目API: `/api/knowledgeitems` (Controller: `KnowledgeItemsController`)
- 附件API: `/api/attachments` (Controller: `AttachmentsController`)

### 1) POST /api/knowledgeitems

**状态**: ✅ **已完成**

**Controller/Action**:
- **文件路径**: `d:\00-Project\AI\AI-Hub\ai-hub-service\Controllers\KnowledgeItemsController.cs`
- **类名**: `KnowledgeItemsController`
- **方法**: `Create([FromBody] CreateKnowledgeArticleDto createDto)` (第59-64行)
- **路由**: `[HttpPost]` → `/api/knowledgeitems`

**请求DTO**:
- **类名**: `CreateKnowledgeArticleDto`
- **文件路径**: `d:\00-Project\AI\AI-Hub\ai-hub-service\DTOs\KnowledgeArticleDto.cs` (第29-39行)
- **字段**: `TenantId`, `Title`, `QuestionText`, `CauseText`, `SolutionText`, `ScopeJson`, `Tags`, `CreatedBy`

**响应DTO**:
- **类名**: `KnowledgeArticleDto`
- **文件路径**: `d:\00-Project\AI\AI-Hub\ai-hub-service\DTOs\KnowledgeArticleDto.cs` (第6-24行)
- **HTTP状态**: `201 Created` (使用 `CreatedAtAction`)

**实现位置**: `Services/KnowledgeArticleService.cs` → `CreateAsync` 方法

### 2) PUT /api/knowledgeitems/{id}

**状态**: ✅ **已完成**

**Controller/Action**:
- **文件路径**: `d:\00-Project\AI\AI-Hub\ai-hub-service\Controllers\KnowledgeItemsController.cs`
- **方法**: `Update(int id, [FromBody] UpdateKnowledgeArticleDto updateDto)` (第69-77行)
- **路由**: `[HttpPut("{id}")]` → `/api/knowledgeitems/{id}`

**请求DTO**:
- **类名**: `UpdateKnowledgeArticleDto`
- **文件路径**: `d:\00-Project\AI\AI-Hub\ai-hub-service\DTOs\KnowledgeArticleDto.cs` (第44-52行)
- **字段**: `Title`, `QuestionText`, `CauseText`, `SolutionText`, `ScopeJson`, `Tags`

**响应DTO**: `KnowledgeArticleDto` (同上)

**实现位置**: `Services/KnowledgeArticleService.cs` → `UpdateAsync` 方法

### 3) GET /api/knowledgeitems/search?keyword=&status=&tag=

**状态**: ✅ **已完成**

**Controller/Action**:
- **文件路径**: `d:\00-Project\AI\AI-Hub\ai-hub-service\Controllers\KnowledgeItemsController.cs`
- **方法**: `Search([FromQuery] SearchKnowledgeArticleDto searchDto)` (第37-54行)
- **路由**: `[HttpGet("search")]` → `/api/knowledgeitems/search`

**请求DTO**:
- **类名**: `SearchKnowledgeArticleDto`
- **文件路径**: `d:\00-Project\AI\AI-Hub\ai-hub-service\DTOs\KnowledgeArticleDto.cs` (第57-65行)
- **查询参数**: `keyword`, `status`, `tag`, `scopeJson`, `pageIndex`, `pageSize`

**响应DTO**:
- **类名**: `PagedResultDto<KnowledgeArticleDto>`
- **文件路径**: `d:\00-Project\AI\AI-Hub\ai-hub-service\DTOs\PagedResultDto.cs`
- **分页字段**: `items`, `totalCount`, `pageIndex`, `pageSize`, `totalPages`

**实现位置**: `Services/KnowledgeArticleService.cs` → `SearchAsync` 方法 (第50-110行)

**搜索逻辑**:
- 关键词搜索: title/question_text/solution_text 包含关键词
- 状态过滤: 精确匹配 status
- 标签过滤: tags 包含指定标签
- 适用范围过滤: scope_json 包含指定内容

### 4) GET /api/knowledgeitems/{id}

**状态**: ✅ **已完成**，**包含附件列表**

**Controller/Action**:
- **文件路径**: `d:\00-Project\AI\AI-Hub\ai-hub-service\Controllers\KnowledgeItemsController.cs`
- **方法**: `GetById(int id)` (第24-32行)
- **路由**: `[HttpGet("{id}")]` → `/api/knowledgeitems/{id}`

**响应DTO**: `KnowledgeArticleDto` (包含 `Assets` 列表)

**附件列表实现**:
- ✅ **已包含**: `KnowledgeArticleDto.Assets` 属性 (类型: `List<AssetDto>`)
- **加载位置**: `Services/KnowledgeArticleService.cs` → `GetByIdAsync` 方法 (第27-44行)
- **加载逻辑**: 手动加载未删除的附件 (`Where(asset => asset.DeletedAt == null)`)
- **映射位置**: `MapToDto` 方法 (第357-393行)

### 5) POST /api/knowledgeitems/{id}/publish

**状态**: ✅ **已完成**，**生成 chunk**

**Controller/Action**:
- **文件路径**: `d:\00-Project\AI\AI-Hub\ai-hub-service\Controllers\KnowledgeItemsController.cs`
- **方法**: `Publish(int id)` (第108-116行)
- **路由**: `[HttpPost("{id}/publish")]` → `/api/knowledgeitems/{id}/publish`

**实现位置**: `Services/KnowledgeArticleService.cs` → `PublishAsync` 方法 (第236-266行)

**Chunk 生成逻辑**:
- ✅ **删除旧chunk**: 第254行 `_context.KnowledgeChunks.RemoveRange(article.Chunks)`
- ✅ **生成新chunk**: 第257行调用 `GenerateChunks(article)`
- ✅ **保存chunk**: 第258行 `_context.KnowledgeChunks.AddRange(chunks)`
- ✅ **调用向量化**: 第263行调用 `_indexService.UpsertEmbeddingsAsync` (占位实现)

**Chunk 生成规则**: 见"五、发布切片（chunk）逻辑"章节

### 6) POST /api/attachments/upload

**状态**: ✅ **已完成**

**Controller/Action**:
- **文件路径**: `d:\00-Project\AI\AI-Hub\ai-hub-service\Controllers\AttachmentsController.cs`
- **方法**: `Upload([FromForm] int knowledgeItemId, [FromForm] IFormFile file)` (第24-40行)
- **路由**: `[HttpPost("upload")]` → `/api/attachments/upload`

**文件类型限制**: ✅ **已实现**
- **允许类型**: `image`, `video`, `pdf`, `other`
- **校验位置**: `Services/AssetService.cs` → `UploadAsync` 方法 (第38-41行)
- **类型判断**: `GetAssetType` 方法根据 `ContentType` 和文件扩展名判断

**返回内容**: ✅ **返回 url + asset_id**
- **响应DTO**: `AssetDto`
- **文件路径**: `d:\00-Project\AI\AI-Hub\ai-hub-service\DTOs\AssetDto.cs`
- **包含字段**: `Id` (asset_id), `Url`, `FileName`, `AssetType`, `Size`, `Duration` 等

**实现位置**: `Services/AssetService.cs` → `UploadAsync` 方法 (第30-99行)

---

## 四、租户隔离（X-Tenant-Id）

### 1) 是否实现了统一读取 tenant 的机制？

**状态**: ❌ **未实现**

**当前情况**:
- ❌ **无中间件**: 未实现 `TenantMiddleware` 或类似机制
- ❌ **无Filter**: 未实现 `TenantActionFilter` 或 `TenantAuthorizationFilter`
- ❌ **无BaseController**: 未实现统一的 `BaseController` 读取 `X-Tenant-Id` 请求头

**代码位置**: 无相关实现

**当前实现方式**:
- ⚠️ **通过DTO传递**: `CreateKnowledgeArticleDto.TenantId` 和 `KnowledgeArticleDto.TenantId` 作为请求/响应字段
- ⚠️ **手动赋值**: 在服务层手动从DTO读取 `tenantId` 并赋值给实体

**示例**:
- `Services/KnowledgeArticleService.cs` → `CreateAsync` 方法 (第112-145行): 从 `createDto.TenantId` 读取
- `Services/AssetService.cs` → `UploadAsync` 方法 (第73行): 从关联的 `article.TenantId` 读取

### 2) 所有写入/查询是否都带 tenant_id？

**写入操作检查**:

| 操作 | 文件路径 | 方法 | 是否带tenant_id | 备注 |
|------|----------|------|----------------|------|
| 创建article | `Services/KnowledgeArticleService.cs` | `CreateAsync` | ✅ 是 | 第125行赋值 |
| 更新article | `Services/KnowledgeArticleService.cs` | `UpdateAsync` | ⚠️ 否 | 未更新tenant_id（合理） |
| 上传asset | `Services/AssetService.cs` | `UploadAsync` | ✅ 是 | 第73行从article获取 |
| 发布article | `Services/KnowledgeArticleService.cs` | `PublishAsync` | ⚠️ 否 | 未更新tenant_id（合理） |

**查询操作检查**:

| 操作 | 文件路径 | 方法 | 是否过滤tenant_id | 备注 |
|------|----------|------|-------------------|------|
| 根据ID查询 | `Services/KnowledgeArticleService.cs` | `GetByIdAsync` | ❌ 否 | 第29行，无tenant过滤 |
| 搜索 | `Services/KnowledgeArticleService.cs` | `SearchAsync` | ❌ 否 | 第62行，无tenant过滤 |
| 获取附件列表 | `Services/AssetService.cs` | `GetByArticleIdAsync` | ❌ 否 | 第143行，无tenant过滤 |

**遗漏清单**:
1. ❌ **GET /api/knowledgeitems/{id}**: 未按 `tenant_id` 过滤
2. ❌ **GET /api/knowledgeitems/search**: 未按 `tenant_id` 过滤
3. ❌ **GET /api/attachments/knowledge-item/{id}**: 未按 `tenant_id` 过滤
4. ❌ **PUT /api/knowledgeitems/{id}**: 未验证 `tenant_id` 匹配
5. ❌ **DELETE /api/knowledgeitems/{id}**: 未验证 `tenant_id` 匹配
6. ❌ **POST /api/knowledgeitems/{id}/publish**: 未验证 `tenant_id` 匹配

**建议实现**:
1. 创建 `TenantMiddleware` 从请求头 `X-Tenant-Id` 读取并存储到 `HttpContext.Items`
2. 创建 `BaseController` 提供 `GetTenantId()` 方法
3. 在所有查询中添加 `Where(a => a.TenantId == tenantId)` 过滤
4. 在所有更新/删除操作中添加 `tenant_id` 验证

---

## 五、发布切片（chunk）逻辑

### 1) 合并文本规则

**状态**: ⚠️ **部分实现**（未包含 title + tags）

**当前实现**: `Services/KnowledgeArticleService.cs` → `GenerateChunks` 方法 (第271-319行)

**合并规则**:
- ✅ **question_text**: 已处理 (第279行)
- ✅ **cause_text**: 已处理 (第280行)
- ✅ **solution_text**: 已处理 (第281行)
- ❌ **title**: 未包含
- ❌ **tags**: 未包含
- ❌ **scope_json**: 未包含

**差异清单**:
- ⚠️ **缺少 title**: 应添加到合并文本的开头
- ⚠️ **缺少 tags**: 应添加到合并文本
- ⚠️ **缺少 scope_json**: 应添加到合并文本

**建议修改**:
```csharp
// 在 GenerateChunks 方法开头添加：
var fullText = $"{article.Title}\n\n";
if (!string.IsNullOrWhiteSpace(article.Tags))
    fullText += $"标签: {article.Tags}\n\n";
if (!string.IsNullOrWhiteSpace(article.ScopeJson))
    fullText += $"适用范围: {article.ScopeJson}\n\n";
// 然后继续处理 question/cause/solution
```

### 2) 切片参数

**Chunk 字数范围**:
- **最大chunk大小**: `1000` 字符 (第291行: `const int maxChunkSize = 1000`)
- **最小chunk大小**: 无明确限制（单个段落可能小于1000字符）

**Overlap**:
- ❌ **未实现**: 当前实现无重叠（overlap）机制
- **切分方式**: 按段落切分，当累计字符数超过1000时创建新chunk

**实现位置**: `Services/KnowledgeArticleService.cs` → `GenerateChunks` 方法 (第289-316行)

### 3) Hash 计算

**使用的算法**: ✅ **SHA256**

**实现位置**: `Services/KnowledgeArticleService.cs` → `ComputeHash` 方法 (第344-352行)

**代码**:
```csharp
private string ComputeHash(string text)
{
    using (var sha256 = SHA256.Create())
    {
        var bytes = Encoding.UTF8.GetBytes(text);
        var hashBytes = sha256.ComputeHash(bytes);
        return BitConverter.ToString(hashBytes).Replace("-", "").ToLower();
    }
}
```

**Hash 去重策略**: ❌ **未实现**

**当前情况**:
- ✅ **计算hash**: 每个chunk都计算hash (第327行)
- ❌ **去重检查**: 未在插入前检查 `tenant_id + hash` 是否已存在
- ❌ **唯一索引**: 数据库未创建 `UX_kb_chunk_tenant_hash` 唯一索引

**建议实现**:
1. 在 `CreateChunk` 方法中，插入前查询是否存在相同 `tenant_id + hash`
2. 如果存在，跳过插入或更新现有记录
3. 创建唯一索引防止数据库层面重复

### 4) 写入 kb_chunk

**是否先清理旧chunk再重建**: ✅ **是**

**实现位置**: `Services/KnowledgeArticleService.cs` → `PublishAsync` 方法 (第253-254行)
```csharp
// 删除旧的chunks
_context.KnowledgeChunks.RemoveRange(article.Chunks);
```

**Chunk_index 起始值**: ✅ **从 0 开始**

**实现位置**: `Services/KnowledgeArticleService.cs` → `GenerateChunks` 方法 (第274行)
```csharp
int chunkIndex = 0;
```

**写入逻辑**: 第257-258行
```csharp
var chunks = GenerateChunks(article);
_context.KnowledgeChunks.AddRange(chunks);
```

---

## 六、文件上传（本地存储，兼容未来 OSS/MinIO）

### 1) 上传保存路径（本地目录）

**配置项**: `appsettings.json` → `FileStorage:LocalPath`
- **配置值**: `"wwwroot/uploads"`
- **实际路径**: `{ContentRootPath}/wwwroot/uploads`
- **示例**: `d:\00-Project\AI\AI-Hub\ai-hub-service\wwwroot\uploads\`

**实现位置**: `Services/AssetService.cs` → `UploadAsync` 方法 (第45-50行)
```csharp
var localPath = _configuration["FileStorage:LocalPath"] ?? "wwwroot/uploads";
var uploadPath = Path.Combine(_environment.ContentRootPath, localPath);
```

**目录创建**: 第49-50行自动创建目录（如果不存在）

### 2) URL 生成规则

**配置项**: `appsettings.json` → `FileStorage:BaseUrl`
- **开发环境**: `"http://localhost:5000/uploads"`
- **生产环境**: `appsettings.Production.json` → `"https://your-domain.com/uploads"`

**URL 格式**: `{BaseUrl}/{Guid}_{原始文件名}`

**实现位置**: `Services/AssetService.cs` → `UploadAsync` 方法 (第44行、第53-54行)
```csharp
var fileName = $"{Guid.NewGuid()}_{file.FileName}";
var baseUrl = _configuration["FileStorage:BaseUrl"] ?? "http://localhost:5000/uploads";
var fileUrl = $"{baseUrl}/{fileName}";
```

**示例URL**: `http://localhost:5000/uploads/079e9051-452e-45fe-bf8b-e230b04f923e_Snipaste_2026-01-24_14-43-03.png`

### 3) 是否做了 StorageProvider 抽象？

**状态**: ❌ **未实现**

**当前实现**: 直接在 `AssetService` 中硬编码本地文件系统操作

**代码位置**: `Services/AssetService.cs` → `UploadAsync` 方法 (第52-60行)
```csharp
var filePath = Path.Combine(uploadPath, fileName);
// 保存文件
using (var stream = new FileStream(filePath, FileMode.Create))
{
    await file.CopyToAsync(stream);
}
```

**建议实现**:
1. 创建 `IStorageProvider` 接口
2. 实现 `LocalFileStorageProvider` (当前逻辑)
3. 实现 `OssStorageProvider` / `MinIOStorageProvider` (未来)
4. 在 `Program.cs` 中注册 `IStorageProvider`，通过配置选择实现

### 4) 是否支持 image/video/pdf？

**状态**: ✅ **支持**

**支持类型**: `image`, `video`, `pdf`, `other`

**ContentType/扩展名校验**: ✅ **已实现**

**实现位置**: `Services/AssetService.cs` → `GetAssetType` 方法

**校验逻辑**:
- 根据 `IFormFile.ContentType` 判断
- 根据文件扩展名（`.jpg`, `.png`, `.mp4`, `.pdf` 等）判断
- 默认返回 `"other"`

**代码片段** (第101-158行):
```csharp
private string GetAssetType(string contentType, string fileName)
{
    // 根据 ContentType 判断
    if (contentType.StartsWith("image/")) return "image";
    if (contentType.StartsWith("video/")) return "video";
    if (contentType == "application/pdf") return "pdf";
    
    // 根据扩展名判断
    var ext = Path.GetExtension(fileName).ToLower();
    if (new[] { ".jpg", ".jpeg", ".png", ".gif", ".webp" }.Contains(ext)) return "image";
    if (new[] { ".mp4", ".avi", ".mov", ".wmv" }.Contains(ext)) return "video";
    if (ext == ".pdf") return "pdf";
    
    return "other";
}
```

---

## 七、当前可验收状态（从 0 到 1 验收链路）

### 前置条件

1. **启动后端服务**:
   ```bash
   cd d:\00-Project\AI\AI-Hub\ai-hub-service
   dotnet run
   ```
   - 期望结果: 服务启动在 `http://localhost:5000`，Swagger 可访问 `http://localhost:5000/swagger`

2. **确认数据库连接**: 检查 `appsettings.json` 中的连接串是否正确

### 验收步骤

#### 1) 创建 Article（含 X-Tenant-Id）

**请求示例** (Postman/curl):
```bash
curl -X POST "http://localhost:5000/api/knowledgeitems" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Id: tenant-001" \
  -d '{
    "tenantId": "tenant-001",
    "title": "测试知识条目",
    "questionText": "用户遇到什么问题？",
    "causeText": "可能原因1：xxx\n可能原因2：yyy",
    "solutionText": "解决步骤1：aaa\n解决步骤2：bbb",
    "scopeJson": "{\"机型\":\"iPhone 14\",\"版本\":\"iOS 17\"}",
    "tags": "iOS,问题排查",
    "createdBy": "测试用户"
  }'
```

**期望结果**:
- HTTP 201 Created
- 返回 `KnowledgeArticleDto`，包含 `id`（例如: `1`）
- `status` 为 `"draft"`
- `tenantId` 为 `"tenant-001"`

**验证SQL**:
```sql
SELECT * FROM kb_article WHERE id = 1;
-- 应看到 tenant_id = 'tenant-001', status = 'draft'
```

#### 2) 上传附件

**请求示例**:
```bash
curl -X POST "http://localhost:5000/api/attachments/upload" \
  -H "X-Tenant-Id: tenant-001" \
  -F "knowledgeItemId=1" \
  -F "file=@/path/to/image.png"
```

**期望结果**:
- HTTP 200 OK
- 返回 `AssetDto`，包含:
  - `id`: 附件ID（例如: `1`）
  - `url`: `"http://localhost:5000/uploads/{Guid}_image.png"`
  - `assetType`: `"image"`
  - `fileName`: 原始文件名
  - `size`: 文件大小（字节）

**验证SQL**:
```sql
SELECT * FROM kb_asset WHERE article_id = 1;
-- 应看到 asset_type = 'image', tenant_id = 'tenant-001'
```

**验证文件**: 检查 `wwwroot/uploads/` 目录，应存在上传的文件

#### 3) 发布 Article（生成 Chunk）

**请求示例**:
```bash
curl -X POST "http://localhost:5000/api/knowledgeitems/1/publish" \
  -H "X-Tenant-Id: tenant-001"
```

**期望结果**:
- HTTP 200 OK
- 返回 `{ "message": "发布成功" }`
- Article 状态变为 `"published"`
- `published_at` 字段有值

**验证SQL - Article**:
```sql
SELECT id, status, published_at FROM kb_article WHERE id = 1;
-- 应看到 status = 'published', published_at 不为 NULL
```

**验证SQL - Chunk**:
```sql
SELECT 
    id, 
    article_id, 
    chunk_index, 
    LEFT(chunk_text, 50) as chunk_preview,
    hash,
    source_fields,
    tenant_id
FROM kb_chunk 
WHERE article_id = 1
ORDER BY chunk_index;
```

**期望结果**:
- 应看到多个 chunk 记录（根据 question/cause/solution 内容切分）
- `chunk_index` 从 0 开始递增
- `hash` 字段有值（64位十六进制字符串）
- `source_fields` 为 `"question"`, `"cause"`, `"solution"` 之一
- `tenant_id` 为 `"tenant-001"`

#### 4) 查询 Chunk

**方式1: 通过SQL直接查询** (推荐):
```sql
-- 查询某个article的所有chunk
SELECT 
    id,
    article_id,
    chunk_index,
    chunk_text,
    hash,
    source_fields,
    created_at
FROM kb_chunk
WHERE article_id = 1
ORDER BY chunk_index;
```

**方式2: 通过Article详情接口** (间接):
```bash
curl "http://localhost:5000/api/knowledgeitems/1"
```
- 注意: 当前接口**不返回chunk列表**，只返回article信息和附件列表

**方式3: 创建专门的Chunk查询接口** (未实现):
- 建议添加: `GET /api/knowledgeitems/{id}/chunks`

---

## 八、阻塞问题/待办清单

### 当前最大的阻塞

**阻塞问题**: ⚠️ **租户隔离未实现**

**影响**:
- 所有查询未按 `tenant_id` 过滤，存在数据泄露风险
- 所有更新/删除操作未验证 `tenant_id`，存在越权风险
- 无法支持多租户场景

**优先级**: 🔴 **高优先级**

### 下一步计划（按优先级）

#### 1. 🔴 实现租户隔离机制（高优先级）

**任务清单**:
- [ ] 创建 `TenantMiddleware` 从请求头 `X-Tenant-Id` 读取租户ID
- [ ] 创建 `BaseController` 提供 `GetTenantId()` 方法
- [ ] 修改所有查询方法添加 `tenant_id` 过滤
- [ ] 修改所有更新/删除方法添加 `tenant_id` 验证
- [ ] 修改 `CreateAsync` 从请求头读取 `tenant_id`（而非DTO）

**预计工作量**: 2-3 天

#### 2. 🟡 完善 Chunk 生成逻辑（中优先级）

**任务清单**:
- [ ] 修改 `GenerateChunks` 方法，包含 `title` + `tags` + `scope_json`
- [ ] 实现 hash 去重检查（插入前查询 `tenant_id + hash`）
- [ ] 创建唯一索引 `UX_kb_chunk_tenant_hash`
- [ ] 考虑实现 overlap 机制（可选）

**预计工作量**: 1-2 天

#### 3. 🟡 实现 StorageProvider 抽象（中优先级）

**任务清单**:
- [ ] 创建 `IStorageProvider` 接口
- [ ] 实现 `LocalFileStorageProvider`
- [ ] 重构 `AssetService` 使用 `IStorageProvider`
- [ ] 在 `Program.cs` 中注册服务

**预计工作量**: 1-2 天

#### 4. 🟢 添加 Chunk 查询接口（低优先级）

**任务清单**:
- [ ] 在 `KnowledgeItemsController` 添加 `GET /api/knowledgeitems/{id}/chunks`
- [ ] 创建 `ChunkDto` 用于返回
- [ ] 实现服务层方法

**预计工作量**: 0.5 天

#### 5. 🟢 完善错误处理和日志（低优先级）

**任务清单**:
- [ ] 统一异常处理中间件
- [ ] 添加结构化日志（Serilog）
- [ ] 添加请求/响应日志记录

**预计工作量**: 1 天

---

## 总结

**当前状态**: ✅ **核心功能已完成，但租户隔离缺失**

**可交付物**:
- ✅ 数据库表结构已落地
- ✅ CRUD 接口已实现
- ✅ 文件上传功能已实现
- ✅ Chunk 生成逻辑已实现（需完善）
- ❌ 租户隔离未实现（阻塞问题）

**建议**: 优先完成租户隔离机制，再进行其他优化。

---

**汇报人**: 项目执行工程师  
**日期**: 2026-01-24
