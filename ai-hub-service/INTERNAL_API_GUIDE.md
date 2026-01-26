# 内部 API 使用指南

## 概述

内部 API 供 Python 服务调用，用于批量创建和发布知识条目。

## 鉴权

所有内部 API 请求必须包含 `X-Internal-Token` 请求头，Token 值需与 `appsettings.json` 中的 `InternalToken` 配置一致。

## API 接口

### 1. 批量创建知识条目（草稿）

**接口**：`POST /api/ai/kb/articles/batch`

**请求头**：
- `Content-Type: application/json`
- `X-Tenant-Id: default`（可选，缺省为 "default"）
- `X-Internal-Token: your-internal-token-change-in-production`

**请求体**：
```json
{
  "articles": [
    {
      "title": "YH-100 启动后无法进入自动模式",
      "questionText": "【发生场景】待补充\n【具体表现】启动后无法进入自动模式\n【报警信息】无报警码\n【影响范围】待补充",
      "causeText": "原因 1：安全门未完全关闭\n原因 2：液压站压力不足",
      "solutionText": "步骤 1：检查安全门状态\n步骤 2：检查液压站压力表\n步骤 3：重新尝试切换",
      "scopeJson": "{\"设备型号\": \"YH-100\"}",
      "tags": "YH-100, 无报警码, 来源:YH系列造型机常见故障及处置明细",
      "createdBy": "系统导入"
    },
    {
      "title": "YH-200 运行中压力波动大",
      "questionText": "【发生场景】待补充\n【具体表现】运行中压力波动大\n【报警信息】E101\n【影响范围】待补充",
      "causeText": "原因 1：压力传感器故障",
      "solutionText": "步骤 1：更换压力传感器\n步骤 2：补充液压油",
      "scopeJson": "{\"设备型号\": \"YH-200\"}",
      "tags": "YH-200, E101, 来源:YH系列造型机常见故障及处置明细",
      "createdBy": "系统导入"
    }
  ]
}
```

**响应**：
```json
{
  "successCount": 2,
  "failureCount": 0,
  "results": [
    {
      "index": 0,
      "success": true,
      "articleId": 1,
      "error": null
    },
    {
      "index": 1,
      "success": true,
      "articleId": 2,
      "error": null
    }
  ]
}
```

**curl 示例**：
```bash
curl -X POST "http://localhost:5000/api/ai/kb/articles/batch" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Id: default" \
  -H "X-Internal-Token: your-internal-token-change-in-production" \
  -d '{
    "articles": [
      {
        "title": "YH-100 启动后无法进入自动模式",
        "questionText": "【发生场景】待补充\n【具体表现】启动后无法进入自动模式\n【报警信息】无报警码\n【影响范围】待补充",
        "causeText": "原因 1：安全门未完全关闭\n原因 2：液压站压力不足",
        "solutionText": "步骤 1：检查安全门状态\n步骤 2：检查液压站压力表\n步骤 3：重新尝试切换",
        "scopeJson": "{\"设备型号\": \"YH-100\"}",
        "tags": "YH-100, 无报警码, 来源:YH系列造型机常见故障及处置明细",
        "createdBy": "系统导入"
      }
    ]
  }'
```

### 2. 批量创建附件记录

**接口**：`POST /api/ai/kb/articles/assets/batch`

**请求头**：
- `Content-Type: application/json`
- `X-Tenant-Id: default`（可选，缺省为 "default"）
- `X-Internal-Token: your-internal-token-change-in-production`

**请求体**：
```json
{
  "assets": [
    {
      "articleId": 1,
      "assetType": "video",
      "fileName": "下芯机比例阀拆解.mp4",
      "url": "http://localhost:5000/uploads/videos/下芯机比例阀拆解.mp4",
      "size": 10485760,
      "duration": null
    }
  ]
}
```

**响应**：
```json
{
  "successCount": 1,
  "failureCount": 0,
  "results": [
    {
      "index": 0,
      "success": true,
      "assetId": 1,
      "error": null
    }
  ]
}
```

**curl 示例**：
```bash
curl -X POST "http://localhost:5000/api/ai/kb/articles/assets/batch" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Id: default" \
  -H "X-Internal-Token: your-internal-token-change-in-production" \
  -d '{
    "assets": [
      {
        "articleId": 1,
        "assetType": "video",
        "fileName": "下芯机比例阀拆解.mp4",
        "url": "http://localhost:5000/uploads/videos/下芯机比例阀拆解.mp4",
        "size": 10485760
      }
    ]
  }'
```

### 3. 批量发布知识条目

**接口**：`POST /api/ai/kb/articles/publish/batch`

**请求头**：
- `Content-Type: application/json`
- `X-Tenant-Id: default`（可选，缺省为 "default"）
- `X-Internal-Token: your-internal-token-change-in-production`

**请求体**：
```json
{
  "articleIds": [1, 2, 3, 4, 5]
}
```

**响应**：
```json
{
  "successCount": 5,
  "failureCount": 0,
  "results": [
    {
      "articleId": 1,
      "success": true,
      "error": null
    },
    {
      "articleId": 2,
      "success": true,
      "error": null
    },
    {
      "articleId": 3,
      "success": true,
      "error": null
    },
    {
      "articleId": 4,
      "success": true,
      "error": null
    },
    {
      "articleId": 5,
      "success": true,
      "error": null
    }
  ]
}
```

**curl 示例**：
```bash
curl -X POST "http://localhost:5000/api/ai/kb/articles/publish/batch" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Id: default" \
  -H "X-Internal-Token: your-internal-token-change-in-production" \
  -d '{
    "articleIds": [1, 2, 3, 4, 5]
  }'
```

## 错误处理

### 401 Unauthorized

缺少或无效的 `X-Internal-Token`：
```json
"Unauthorized: Invalid or missing X-Internal-Token"
```

### 400 Bad Request

请求体格式错误或缺少必需字段：
```json
{
  "type": "https://tools.ietf.org/html/rfc7231#section-6.5.1",
  "title": "One or more validation errors occurred.",
  "status": 400,
  "errors": {
    "Articles": ["Articles 列表不能为空"]
  }
}
```

## 验证步骤

### 1. 配置 InternalToken

编辑 `appsettings.json`：
```json
{
  "InternalToken": "your-internal-token-change-in-production"
}
```

### 2. 测试批量创建

```bash
# 使用 Swagger
# 访问 http://localhost:5000/swagger
# 找到 InternalApi 控制器
# 使用 POST /api/ai/kb/articles/batch 接口

# 或使用 curl（替换 TOKEN 为实际值）
curl -X POST "http://localhost:5000/api/ai/kb/articles/batch" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Id: default" \
  -H "X-Internal-Token: your-internal-token-change-in-production" \
  -d @test-batch-create.json
```

### 3. 验证创建结果

```bash
# 查询创建的知识条目
curl "http://localhost:5000/api/knowledgeitems/search?keyword=YH" \
  -H "X-Tenant-Id: default"
```

### 4. 测试批量发布

```bash
# 使用返回的 articleIds
curl -X POST "http://localhost:5000/api/ai/kb/articles/publish/batch" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Id: default" \
  -H "X-Internal-Token: your-internal-token-change-in-production" \
  -d '{"articleIds": [1, 2, 3]}'
```

### 5. 验证发布结果

```sql
-- 查询生成的 chunks
SELECT 
    article_id,
    COUNT(*) as chunk_count,
    MAX(created_at) as last_chunk_time
FROM kb_chunk
WHERE article_id IN (1, 2, 3)
GROUP BY article_id;
```

## 注意事项

1. **Token 安全**：生产环境必须修改 `InternalToken` 为强随机字符串
2. **租户隔离**：所有操作都受租户隔离机制限制
3. **批量大小**：建议单次批量创建不超过 100 条
4. **错误处理**：单条失败不影响其他条目的处理
5. **状态管理**：批量创建的知识条目状态为 `draft`，需要调用批量发布接口才能生成 chunks
