# Excel 导入架构说明

## 架构设计

采用**前后端分离 + 服务分离**的架构：

1. **.NET 后端（ai-hub-service）**：提供知识库 CRUD 和发布功能
   - 提供内部 API（`/api/ai/kb/articles/*`）供 Python 服务调用
   - 使用 `X-Internal-Token` 进行简单鉴权
   - 保持现有知识库逻辑不变

2. **Python 服务（ai-hub-ai）**：处理 Excel 导入
   - FastAPI 服务，接收 Excel 文件
   - 使用 pandas/openpyxl 解析 Excel
   - 调用 .NET 内部 API 批量创建知识条目

## 文件结构

```
AI-Hub/
├── ai-hub-service/              # .NET 后端
│   ├── Controllers/
│   │   └── InternalApiController.cs    # 内部 API 控制器
│   ├── Middleware/
│   │   └── InternalApiAuthMiddleware.cs # 内部 API 鉴权中间件
│   ├── DTOs/
│   │   └── InternalApiDto.cs          # 内部 API DTO
│   ├── appsettings.json               # 配置 InternalToken
│   └── INTERNAL_API_GUIDE.md          # 内部 API 使用指南
│
└── ai-hub-ai/                    # Python FastAPI 服务
    ├── main.py                   # 主服务文件
    ├── requirements.txt          # Python 依赖
    ├── .env.example              # 环境变量示例
    ├── README.md                 # Python 服务使用说明
    └── test-import.ps1           # 测试脚本
```

## 工作流程

```
1. 用户上传 Excel 文件
   ↓
2. Python 服务接收文件 (POST /import/excel)
   ↓
3. pandas 解析 Excel，每行映射为知识条目 DTO
   ↓
4. Python 服务调用 .NET 内部 API
   POST /api/ai/kb/articles/batch
   (带 X-Internal-Token 鉴权)
   ↓
5. .NET 后端批量创建知识条目（draft 状态）
   ↓
6. 返回创建的 article IDs
   ↓
7. (可选) Python 服务调用批量发布接口
   POST /api/ai/kb/articles/publish/batch
   ↓
8. .NET 后端批量发布，生成 chunks
```

## 配置说明

### .NET 后端配置

**appsettings.json**：
```json
{
  "InternalToken": "your-internal-token-change-in-production"
}
```

**重要**：生产环境必须修改为强随机字符串。

### Python 服务配置

**.env**：
```env
DOTNET_BASE_URL=http://localhost:5000
INTERNAL_TOKEN=your-internal-token-change-in-production
DEFAULT_TENANT=default
```

**重要**：`INTERNAL_TOKEN` 必须与 .NET 后端的 `InternalToken` 一致。

## API 接口

### .NET 后端内部 API

1. **POST /api/ai/kb/articles/batch**
   - 批量创建知识条目（draft 状态）
   - 需要 `X-Internal-Token` 鉴权

2. **POST /api/ai/kb/articles/publish/batch**
   - 批量发布知识条目
   - 需要 `X-Internal-Token` 鉴权

### Python 服务 API

1. **POST /import/excel**
   - 接收 Excel 文件
   - 解析并调用 .NET 内部 API
   - 返回导入统计

## 字段映射规则

Excel 行 → 知识条目：

| Excel 字段 | 知识条目字段 | 处理规则 |
|-----------|------------|---------|
| 设备型号 | title (部分) | `设备型号 + 故障现象` |
| 故障现象 | title (部分) | `设备型号 + 故障现象` |
| 故障现象 | questionText | `【具体表现】{故障现象}` |
| 报警信息 | questionText | `【报警信息】{报警信息}` |
| 原因分析 | causeText | 自动格式化为"原因 1/2/3" |
| 处理方法 | solutionText | 自动格式化为"步骤 1/2/3" |
| 设备型号 | scopeJson | `{"设备型号": "xxx"}` |
| 设备型号 + 报警信息 + 文件名 | tags | 逗号分隔 |

## 测试步骤

### 1. 启动 .NET 后端

```bash
cd ai-hub-service
dotnet run
```

访问：http://localhost:5000/swagger

### 2. 配置 Token

编辑 `ai-hub-service/appsettings.json`：
```json
{
  "InternalToken": "test-token-123"
}
```

### 3. 启动 Python 服务

```bash
cd ai-hub-ai
pip install -r requirements.txt

# 创建 .env 文件
cp .env.example .env
# 编辑 .env，设置 INTERNAL_TOKEN=test-token-123

uvicorn main:app --reload --port 8000
```

访问：http://localhost:8000/docs

### 4. 测试 Excel 导入

```bash
# PowerShell
cd ai-hub-ai
.\test-import.ps1

# 或使用 curl
curl -X POST "http://localhost:8000/import/excel" \
  -F "file=@YH系列造型机常见故障及处置明细.xlsx"
```

### 5. 验证结果

```bash
# 查询导入的知识条目
curl "http://localhost:5000/api/knowledgeitems/search?keyword=YH" \
  -H "X-Tenant-Id: default"
```

## 优势

1. **职责分离**：.NET 负责数据持久化，Python 负责 Excel 解析
2. **技术选型灵活**：Python 生态的 pandas/openpyxl 更适合 Excel 处理
3. **可扩展性**：未来可以轻松添加其他数据源（CSV、JSON 等）
4. **安全性**：内部 API 使用 Token 鉴权，不暴露给前端
5. **向后兼容**：不影响现有的知识库 API

## 注意事项

1. **Token 安全**：生产环境必须使用强随机 Token
2. **错误处理**：单行处理失败不影响其他行
3. **批量大小**：建议单次批量创建不超过 100 条
4. **状态管理**：导入的知识条目为 `draft`，需要手动或批量发布
5. **租户隔离**：所有操作都受租户隔离机制限制
