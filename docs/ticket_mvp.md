# 售后工单系统 MVP - API 接口文档

> 本文档说明售后工单系统的 API 接口使用方法。

## 基础信息

- **Base URL**: `http://localhost:5000` (根据实际部署调整)
- **API 前缀**: `/api/tickets`
- **认证方式**: JWT Bearer Token
- **租户隔离**: 通过请求头 `X-Tenant-Id` 传递

---

## 一、工单 CRUD 接口

### 1.1 创建工单

**POST** `/api/tickets`

#### 请求头
```
Authorization: Bearer <jwt_token>
X-Tenant-Id: default
Content-Type: application/json
```

#### 请求体
```json
{
  "title": "设备不射砂-E001 报警",
  "description": "用户反映设备无法射砂，控制台显示 E001 报警代码",
  "priority": "high",
  "deviceId": "device-001",
  "deviceMn": "MN123456",
  "customerId": "customer-001",
  "sessionId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "triggerMessageId": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "source": "ai_chat",
  "metaJson": "{\"issue_category\":\"射砂异常\",\"alarm_code\":\"E001\"}"
}
```

#### 字段说明
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| title | string | 是 | 工单标题 |
| description | string | 否 | 问题描述 |
| priority | string | 否 | 优先级：low/medium/high/urgent，默认 medium |
| deviceId | string | 否 | 设备 ID |
| deviceMn | string | 否 | 设备 MN 号 |
| customerId | string | 否 | 客户 ID |
| sessionId | GUID | 否 | AI 会话 ID |
| triggerMessageId | GUID | 否 | 触发工单的 AI 消息 ID |
| source | string | 否 | 来源：ai_chat/manual/api，默认 manual |
| metaJson | string | 否 | 扩展元数据（JSON 字符串） |

#### 响应示例
```json
{
  "ticketId": "c3d4e5f6-a7b8-9012-cdef-123456789012",
  "ticketNo": "T202602260001",
  "tenantId": "default",
  "title": "设备不射砂-E001 报警",
  "description": "用户反映设备无法射砂，控制台显示 E001 报警代码",
  "status": "pending",
  "priority": "high",
  "source": "ai_chat",
  "deviceId": "device-001",
  "deviceMn": "MN123456",
  "customerId": "customer-001",
  "sessionId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "triggerMessageId": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "assigneeId": null,
  "assigneeName": null,
  "createdBy": "user-001",
  "createdAt": "2026-02-26T10:00:00",
  "updatedAt": null,
  "closedAt": null,
  "finalSolutionSummary": null,
  "metaJson": "{\"issue_category\":\"射砂异常\",\"alarm_code\":\"E001\"}",
  "logs": [
    {
      "logId": 1,
      "ticketId": "c3d4e5f6-a7b8-9012-cdef-123456789012",
      "action": "create",
      "content": "创建工单：设备不射砂-E001 报警",
      "operatorId": "user-001",
      "operatorName": null,
      "nextStatus": "pending",
      "createdAt": "2026-02-26T10:00:00"
    }
  ]
}
```

---

### 1.2 获取工单列表

**GET** `/api/tickets?pageIndex=1&pageSize=20&status=pending`

#### 查询参数
| 参数 | 类型 | 说明 |
|------|------|------|
| pageIndex | int | 页码，从 1 开始，默认 1 |
| pageSize | int | 每页数量，默认 20 |
| status | string | 状态过滤：pending/processing/resolved/closed |
| priority | string | 优先级过滤 |
| deviceMn | string | 设备 MN 号过滤 |
| assigneeId | string | 分配人 ID 过滤 |
| keyword | string | 关键词搜索（标题/描述） |

#### 权限说明
- **普通用户**: 只能查看自己创建 (`created_by`) 或分配给自已 (`assignee_id`) 的工单
- **工程师/管理员**: 可查看所有工单（需 JWT token 的 role claim 包含 engineer 或 admin）

#### 响应示例
```json
{
  "items": [
    {
      "ticketId": "c3d4e5f6-a7b8-9012-cdef-123456789012",
      "ticketNo": "T202602260001",
      "title": "设备不射砂-E001 报警",
      "status": "pending",
      "priority": "high",
      "source": "ai_chat",
      "deviceMn": "MN123456",
      "assigneeName": null,
      "createdBy": "user-001",
      "createdAt": "2026-02-26T10:00:00"
    }
  ],
  "totalCount": 1,
  "pageIndex": 1,
  "pageSize": 20
}
```

---

### 1.3 获取工单详情

**GET** `/api/tickets/{id}`

`id` 为 `ticket_id` (GUID 格式)

#### 响应示例
同「创建工单」响应格式

---

### 1.4 更新工单

**PUT** `/api/tickets/{id}`

#### 请求体（所有字段可选）
```json
{
  "title": "更新后的标题",
  "description": "更新后的描述",
  "priority": "urgent",
  "assigneeId": "engineer-001",
  "assigneeName": "张工程师",
  "finalSolutionSummary": "已更换电磁阀，问题解决",
  "metaJson": "{\"fixed\": true}"
}
```

---

## 二、工单状态流转接口

### 2.1 开始处理

**POST** `/api/tickets/{id}/start`

将工单状态从 `pending` 变更为 `processing`

#### 请求体（可选）
```json
{
  "assigneeId": "engineer-001",
  "assigneeName": "张工程师",
  "note": "开始排查，初步判断是电磁阀故障"
}
```

#### 响应
返回更新后的工单详情

---

### 2.2 标记已解决

**POST** `/api/tickets/{id}/resolve`

将工单状态从 `processing` 变更为 `resolved`，**必须填写解决方案**

#### 请求体
```json
{
  "finalSolutionSummary": "检查发现电磁阀线圈烧毁，更换新品后测试正常。建议：备件库补充电磁阀备件。",
  "note": "已更换电磁阀型号 SV-25，测试 3 次无异常"
}
```

> **注意**: `finalSolutionSummary` 必填，后续用于转知识库

---

### 2.3 关闭工单

**POST** `/api/tickets/{id}/close`

将工单状态变更为 `closed`

#### 请求体（可选）
```json
{
  "note": "客户确认问题已解决，关闭工单"
}
```

---

## 三、工单日志接口

### 3.1 添加工单日志/备注

**POST** `/api/tickets/{id}/logs`

#### 请求体
```json
{
  "content": "已联系客户，确认设备停机时间为今天上午 10 点左右",
  "operatorName": "李客服"
}
```

---

### 3.2 获取工单日志列表

**GET** `/api/tickets/{id}/logs`

#### 响应示例
```json
[
  {
    "logId": 1,
    "ticketId": "c3d4e5f6-a7b8-9012-cdef-123456789012",
    "action": "create",
    "content": "创建工单：设备不射砂-E001 报警",
    "operatorId": "user-001",
    "operatorName": null,
    "nextStatus": "pending",
    "createdAt": "2026-02-26T10:00:00"
  },
  {
    "logId": 2,
    "ticketId": "c3d4e5f6-a7b8-9012-cdef-123456789012",
    "action": "start",
    "content": "开始排查，初步判断是电磁阀故障",
    "operatorId": "engineer-001",
    "operatorName": null,
    "nextStatus": "processing",
    "createdAt": "2026-02-26T11:00:00"
  }
]
```

---

## 四、转知识库接口

### 4.1 将工单转为知识库文章

**POST** `/api/tickets/{id}/convert-to-kb`

#### 前置条件
- 工单状态必须为 `resolved` (已解决)
- `final_solution_summary` 不能为空

#### 请求体（可选）
```json
{
  "triggerVectorIndex": true
}
```

#### 功能说明
1. 根据工单信息创建知识库文章 (`kb_article`)
2. 文章内容映射规则:
   - **标题**: `[工单号] 故障分类 - 报警码 - 原标题`
   - **question_text**: 工单 description
   - **cause_text**: 从 meta_json 中提取 issue_category/alarm_code
   - **solution_text**: final_solution_summary
   - **scope_json**: 设备信息 (device_mn, device_id)
   - **tags**: 工单号 + 故障分类
3. 写入工单日志 (action=convert_to_kb)
4. 调用 ai-hub-ai 的 `/api/v1/ingest/article/{articleId}` 触发向量入库

#### 响应示例（成功）
```json
{
  "message": "已成功转换为知识库文章（文章 ID: 123）",
  "articleId": 123,
  "vectorSuccess": true,
  "vectorMessage": "向量入库成功"
}
```

#### 响应示例（向量入库失败）
```json
{
  "message": "已成功转换为知识库文章（文章 ID: 123）",
  "articleId": 123,
  "vectorSuccess": false,
  "vectorMessage": "向量入库失败，请查看工单日志"
}
```

> **注意**: 向量入库失败不会回滚知识库文章创建，失败原因会记录到 ticket_log

---

## 五、错误码说明

| HTTP 状态码 | 说明 |
|-------------|------|
| 200 | 操作成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误或业务规则校验失败 |
| 401 | 未授权（JWT 缺失或过期） |
| 403 | 无权限访问 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

---

## 六、cURL 示例

### 创建工单
```bash
curl -X POST http://localhost:5000/api/tickets \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "X-Tenant-Id: default" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "设备不射砂-E001 报警",
    "description": "用户反映设备无法射砂，控制台显示 E001 报警代码",
    "priority": "high",
    "deviceMn": "MN123456",
    "source": "ai_chat"
  }'
```

### 获取工单列表
```bash
curl -X GET "http://localhost:5000/api/tickets?status=pending&pageIndex=1&pageSize=20" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "X-Tenant-Id: default"
```

### 开始处理工单
```bash
curl -X POST http://localhost:5000/api/tickets/TICKET_ID/start \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "X-Tenant-Id: default" \
  -H "Content-Type: application/json" \
  -d '{
    "assigneeId": "engineer-001",
    "note": "开始排查"
  }'
```

### 标记已解决
```bash
curl -X POST http://localhost:5000/api/tickets/TICKET_ID/resolve \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "X-Tenant-Id: default" \
  -H "Content-Type: application/json" \
  -d '{
    "finalSolutionSummary": "已更换电磁阀，问题解决",
    "note": "测试三次正常"
  }'
```

### 转知识库
```bash
curl -X POST http://localhost:5000/api/tickets/TICKET_ID/convert-to-kb \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "X-Tenant-Id: default" \
  -H "Content-Type: application/json" \
  -d '{
    "triggerVectorIndex": true
  }'
```

---

## 七、Postman 集合导入

可将以下 JSON 保存为 `tickets_api.json` 导入 Postman：

```json
{
  "info": {
    "name": "工单系统 API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "创建工单",
      "request": {
        "method": "POST",
        "url": "{{base_url}}/api/tickets",
        "header": [
          {"key": "Authorization", "value": "Bearer {{jwt_token}}"},
          {"key": "X-Tenant-Id", "value": "default"},
          {"key": "Content-Type", "value": "application/json"}
        ],
        "body": {
          "mode": "raw",
          "payload": "{\n  \"title\": \"设备不射砂-E001 报警\",\n  \"description\": \"用户反映设备无法射砂\",\n  \"priority\": \"high\"\n}"
        }
      }
    },
    {
      "name": "获取工单列表",
      "request": {
        "method": "GET",
        "url": "{{base_url}}/api/tickets?status=pending",
        "header": [
          {"key": "Authorization", "value": "Bearer {{jwt_token}}"},
          {"key": "X-Tenant-Id", "value": "default"}
        ]
      }
    },
    {
      "name": "转知识库",
      "request": {
        "method": "POST",
        "url": "{{base_url}}/api/tickets/{{ticket_id}}/convert-to-kb",
        "header": [
          {"key": "Authorization", "value": "Bearer {{jwt_token}}"},
          {"key": "X-Tenant-Id", "value": "default"},
          {"key": "Content-Type", "value": "application/json"}
        ],
        "body": {
          "mode": "raw",
          "payload": "{\n  \"triggerVectorIndex\": true\n}"
        }
      }
    }
  ],
  "variable": [
    {"key": "base_url", "value": "http://localhost:5000"},
    {"key": "jwt_token", "value": ""},
    {"key": "ticket_id", "value": ""}
  ]
}
```

---

## 八、配置说明

### appsettings.json 配置项

```json
{
  "AiHubAi": {
    "BaseUrl": "http://localhost:8001"
  }
}
```

- `AiHubAi.BaseUrl`: ai-hub-ai 服务的地址，用于触发向量入库
- 如果不需要向量入库功能，可将 `BaseUrl` 留空或在调用时设置 `triggerVectorIndex: false`

---

## 九、工程师端 API（管理后台）

工程师端 API 用于管理后台（`/admin/tickets`），需要工程师/管理员权限。

**Base URL**: `http://localhost:5000`
**API 前缀**: `/api/admin/tickets`

### 权限说明

- 请求头 `X-User-Role` 需设置为 `engineer` 或 `admin`
- 或者 JWT token 的 `role` claim 中包含相应角色

### 接口列表

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/admin/tickets` | 获取工单列表（工程师可见全部） |
| GET | `/api/admin/tickets/{id}` | 获取工单详情 |
| POST | `/api/admin/tickets/{id}/start` | 开始处理 |
| POST | `/api/admin/tickets/{id}/resolve` | 标记已解决 |
| POST | `/api/admin/tickets/{id}/close` | 关闭工单 |
| POST | `/api/admin/tickets/{id}/logs` | 添加备注 |
| POST | `/api/admin/tickets/{id}/convert-to-kb` | 转为知识库 |

### cURL 示例

#### 获取工单列表
```bash
curl -X GET "http://localhost:5000/api/admin/tickets?status=pending&pageIndex=1&pageSize=20" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "X-Tenant-Id: default" \
  -H "X-User-Role: engineer"
```

#### 开始处理
```bash
curl -X POST http://localhost:5000/api/admin/tickets/TICKET_ID/start \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "X-Tenant-Id: default" \
  -H "X-User-Role: engineer" \
  -H "Content-Type: application/json" \
  -d '{
    "assigneeName": "张工程师",
    "note": "开始排查，初步判断是电磁阀故障"
  }'
```

#### 标记已解决
```bash
curl -X POST http://localhost:5000/api/admin/tickets/TICKET_ID/resolve \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "X-Tenant-Id: default" \
  -H "X-User-Role: engineer" \
  -H "Content-Type: application/json" \
  -d '{
    "finalSolutionSummary": "检查发现电磁阀线圈烧毁，更换新品后测试正常。建议：备件库补充电磁阀备件。",
    "note": "已更换电磁阀型号 SV-25，测试 3 次无异常"
  }'
```

#### 转为知识库
```bash
curl -X POST http://localhost:5000/api/admin/tickets/TICKET_ID/convert-to-kb \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "X-Tenant-Id: default" \
  -H "X-User-Role: engineer" \
  -H "Content-Type: application/json"
```

---

*文档版本：v1.0 | 日期：2026-02-26*
