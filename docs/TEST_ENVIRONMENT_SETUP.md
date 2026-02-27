# AI-Hub 测试环境隔离方案

## 概述

为 AI-Hub 项目提供了完整的测试环境隔离方案，确保测试数据与生产数据完全分离。

## 测试环境配置

### 1. SQL Server 测试数据库

**初始化脚本位置**: `ai-hub-service/Database/init_test_db.sql`

#### 执行步骤

```sql
-- 1. 使用 SSMS 或 sqlcmd 连接到 SQL Server
-- 2. 执行初始化脚本
sqlcmd -S localhost -U sa -P your-password -i ai-hub-service/Database/init_test_db.sql

-- 或在 SSMS 中打开 init_test_db.sql 文件并执行
```

#### 创建的数据库

- **数据库名**: `ai_hub_test`

#### 创建的表结构（完整版）

| 表名 | 说明 |
|------|------|
| `ticket` | 工单主表 |
| `ticket_log` | 工单日志表 |
| `kb_article` | 知识主表 |
| `kb_asset` | 知识资源表（附件） |
| `kb_chunk` | 知识切片表（向量化） |
| `users` | 用户表 |
| `ai_conversation` | AI 会话表 |
| `ai_message` | AI 消息表 |
| `ai_decision_log` | AI 决策日志 |
| `ai_retrieval_log` | AI 检索日志 |
| `ai_response` | AI 响应表 |

---

### 2. .NET 后端 (ai-hub-service)

**测试配置文件**: `ai-hub-service/appsettings.Test.json`

#### 环境切换方式

**方式1: 代码开关（推荐）**

编辑 `ai-hub-service/Program.cs` 文件，修改 `IS_TEST` 变量：

```csharp
// =====================================================
// 【环境切换开关】修改这里来切换环境
// =====================================================
// True = 测试环境（使用 appsettings.Test.json）
// False = 生产环境（使用 appsettings.Production.json）
static readonly bool IS_TEST = true;   // 改为 false 即切换到生产环境
// =====================================================
```

**方式2: 环境变量**

```bash
# Windows PowerShell
$env:ASPNETCORE_ENVIRONMENT="Test"
dotnet run --project ai-hub-service/ai-hub-service.csproj

# Windows CMD
set ASPNETCORE_ENVIRONMENT=Test
dotnet run --project ai-hub-service/ai-hub-service.csproj

# Linux/Mac
export ASPNETCORE_ENVIRONMENT=Test
dotnet run --project ai-hub-service/ai-hub-service.csproj
```

#### 关键配置

```json
{
  "ConnectionStrings": {
    "DefaultConnection": "Server=localhost;Database=ai_hub_test;..."
  },
  "FileStorage": {
    "LocalPath": "wwwroot/uploads_test",
    "BaseUrl": "http://localhost:5000/uploads_test"
  }
}
```

#### 切换到测试环境

**Windows (PowerShell)**:
```powershell
$env:ASPNETCORE_ENVIRONMENT="Test"
dotnet run --project ai-hub-service/ai-hub-service.csproj
```

**Windows (CMD)**:
```cmd
set ASPNETCORE_ENVIRONMENT=Test
dotnet run --project ai-hub-service/ai-hub-service.csproj
```

**Linux/Mac**:
```bash
export ASPNETCORE_ENVIRONMENT=Test
dotnet run --project ai-hub-service/ai-hub-service.csproj
```

#### 配置优先级

1. `appsettings.json` - 基础配置
2. `appsettings.{Environment}.json` - 环境特定配置（如 `appsettings.Test.json`）
3. 环境变量

---

### 3. Python AI 服务 (ai-hub-ai)

**测试配置文件**: `ai-hub-ai/.env.test`

#### 环境切换方式

**方式1: 代码开关（推荐）**

编辑 `ai-hub-ai/app/core/config.py` 文件，修改 `IS_TEST` 变量：

```python
# =====================================================
# 【环境切换开关】修改这里来切换环境
# =====================================================
# True = 测试环境（使用 .env.test）
# False = 生产环境（使用 .env.production）
IS_TEST = True   # 改为 False 即切换到生产环境
# =====================================================
```

**方式2: 环境变量**

```bash
# Windows PowerShell
$env:APP_ENV="test"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001

# Linux/Mac
export APP_ENV=test
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001
```

#### 关键配置

```bash
# 测试数据库
SQLSERVER_DSN=Driver={ODBC Driver 17 for SQL Server};Server=localhost;Database=ai_hub_test;...

# 测试向量库
CHROMA_PERSIST_DIR=./data/chroma_test
CHROMA_COLLECTION=kb_articles_test
```

#### 切换到测试环境

**Windows (PowerShell)**:
```powershell
$env:APP_ENV="test"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001
```

**Windows (CMD)**:
```cmd
set APP_ENV=test
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001
```

**Linux/Mac**:
```bash
export APP_ENV=test
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001
```

#### 配置文件选择规则

| APP_ENV 值 | 使用的配置文件 |
|------------|----------------|
| `production` | `.env.production` |
| `test` | `.env.test` |
| `development` 或其他 | `.env` |

---

## 环境切换速查

### 切换到测试环境

**方式1: 代码开关（推荐）**

```csharp
// .NET - 编辑 Program.cs
static readonly bool IS_TEST = true;
```

```python
# Python - 编辑 app/core/config.py
IS_TEST = True
```

**方式2: 环境变量**

```bash
# .NET 服务
export ASPNETCORE_ENVIRONMENT=Test

# Python AI 服务
export APP_ENV=test
```

### 切换到生产环境

**方式1: 代码开关**

```csharp
// .NET - 编辑 Program.cs
static readonly bool IS_TEST = false;
```

```python
# Python - 编辑 app/core/config.py
IS_TEST = False
```

**方式2: 环境变量**

```bash
# .NET 服务
export ASPNETCORE_ENVIRONMENT=Production

# Python AI 服务
export APP_ENV=production
```

### 切换到开发环境

```bash
# .NET 服务
export ASPNETCORE_ENVIRONMENT=Development

# Python AI 服务
export APP_ENV=development
# 或不设置 APP_ENV（默认使用代码中的 IS_TEST 配置）
```

---

### 启动服务

```bash
# .NET
dotnet run --project ai-hub-service/ai-hub-service.csproj

# Python
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001
```

---

## 启动日志确认

### .NET 服务启动日志

```
============================================================
AI-Hub .NET 服务启动 | 当前环境: Test
============================================================
```

### Python AI 服务启动日志

```
============================================================
AI-Hub 服务启动 | 当前环境: test
============================================================
数据库: ai_hub_test
向量库: ./data/chroma_test (collection: kb_articles_test)
配置: DOTNET_BASE_URL=http://localhost:5000, DEFAULT_TENANT=default_test, ...
============================================================
```

---

## 验收清单

- [ ] 执行 `init_test_db.sql` 成功创建 `ai_hub_test` 数据库
- [ ] 验证表结构完整：`SELECT name FROM sys.tables WHERE type = 'U' ORDER BY name;`
- [ ] .NET 服务在 Test 环境下连接到 `ai_hub_test` 数据库
- [ ] Python AI 服务在 Test 环境下使用 `./data/chroma_test` 向量目录
- [ ] 测试环境创建的工单写入 `ai_hub_test.dbo.ticket`
- [ ] 测试环境用户注册写入 `ai_hub_test.dbo.users`
- [ ] 测试环境转知识库写入 `ai_hub_test.dbo.kb_article`
- [ ] 测试环境向量入库写入 `chroma_test` 集合
- [ ] 测试环境 AI 对话审计写入 `ai_hub_test.dbo.ai_*` 表
- [ ] 切换回 Production 环境后，测试数据不影响生产数据

---

## 目录结构

```
ai-hub-service/
├── appsettings.json              # 基础配置
├── appsettings.Development.json  # 开发环境配置
├── appsettings.Test.json         # 测试环境配置
├── appsettings.Production.json   # 生产环境配置
├── Program.cs                  # 主程序（包含 IS_TEST 环境切换开关）
└── Database/
    ├── init_test_db.sql          # 测试数据库完整初始化脚本
    └── Migrations/               # 数据库迁移脚本
        ├── 001_InitialCreate.sql
        ├── 002_RefactorToNewSchema.sql
        ├── 003_AddSoftDeleteFields.sql
        ├── 004_AddChunkUniqueIndex.sql
        ├── 005_CreateAiAuditTables.sql
        ├── 006_CreateUsersTable.sql
        ├── 007_FixUserIdDefault.sql
        ├── 008_ChangePhoneToAccount.sql
        ├── 009_AddDeviceMN.sql
        ├── 010_AddSourceFieldsToKbArticle.sql
        ├── 011_AddUserRole.sql
        ├── 012_AddKbArticleIdToTicket.sql
        └── 013_DropAllForeignKeys.sql

ai-hub-ai/
├── .env                         # 开发环境配置
├── .env.test                    # 测试环境配置
├── .env.production              # 生产环境配置
├── data/
│   ├── chroma/                  # 开发/生产向量库
│   └── chroma_test/             # 测试向量库
└── app/core/config.py           # 配置加载逻辑（支持 IS_TEST 开关和 APP_ENV 环境变量）
                                    # 修改文件顶部的 IS_TEST = True/False 即可切换环境
```

---

## 注意事项

1. **.NET 服务环境切换**：优先级顺序
   - 最高：`ASPNETCORE_ENVIRONMENT` 环境变量（`Test`/`Production`/`Development`）
   - 次之：`Program.cs` 文件中的 `IS_TEST` 变量（`true`=测试，`false`=生产）
   - 默认：`IS_TEST=false` 即生产环境

2. **Python AI 服务环境切换**：优先级顺序
   - 最高：`APP_ENV` 环境变量（`test`/`production`/`development`）
   - 次之：`app/core/config.py` 文件中的 `IS_TEST` 变量（`True`=测试，`False`=生产）
   - 默认：`IS_TEST=False` 即生产环境

2. **首次启动测试环境前**，请确保：
   - SQL Server 中已创建 `ai_hub_test` 数据库
   - 数据库连接字符串中的用户名密码正确
   - `data/chroma_test` 目录有写入权限

2. **环境变量优先级**高于配置文件，如需临时覆盖可设置环境变量

3. **测试数据清理**：
   ```bash
   # 方式1: 清空测试数据库（慎用！会删除所有测试数据）
   sqlcmd -S localhost -U sa -P your-password -Q "DROP DATABASE ai_hub_test"

   # 方式2: 只清空特定表的数据
   sqlcmd -S localhost -U sa -P your-password -d ai_hub_test -Q "TRUNCATE TABLE ticket_log; TRUNCATE TABLE ai_message; TRUNCATE TABLE ai_retrieval_log;"
   ```
   ```bash
   # 清空测试向量库
   rm -rf ai-hub-ai/data/chroma_test
   ```

4. **跨服务调用**：测试环境下，.NET 和 Python 服务需要使用相同的 `InternalToken`
