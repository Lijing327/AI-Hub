# 向量库写入与全量重建

## 问题现象

主库（SQL Server `kb_article`）更新后，向量库（Chroma）里仍是旧的 `article_id`，会导致：

- 向量检索能命中多条（如 10 条），但按 `article_ids` 查主库为空；
- 日志出现：`向量检索返回了 article_ids，但数据库查询为空`，只能走 .NET 兜底只返回 1 条。

**原因**：只更新了主库，没有对向量库做「全量覆盖」重建。

## 全量覆盖（推荐）

**一次请求完成：先清空向量库，再按当前主库全量写入。**

- **接口**：`POST /api/v1/ingest/all`
- **请求体示例**：
  ```json
  {
    "clear_first": true
  }
  ```
- 可选参数：`tenant_id`、`status`、`limit`（与不带 `clear_first` 时一致）。

若主应用挂了 `/python-api` 前缀，则完整路径为：`POST /python-api/api/v1/ingest/all`。

## 仅清空向量库

若需要「先清空、稍后再全量写入」分两步操作：

1. **清空**：`POST /api/v1/ingest/clear`（或 `/python-api/api/v1/ingest/clear`）  
   - 仅删除当前 Chroma 集合并重建空集合，不写入数据。
2. **全量写入**：再调 `POST /api/v1/ingest/all`（可不带 `clear_first`，因已清空）。

## 其它接口

- `POST /api/v1/ingest/article/{article_id}`：重建单条。
- `POST /api/v1/ingest/batch`：按 `ids` 批量重建。
- `GET /api/v1/ingest/debug/count`：查看当前主库符合条件的条数（调试用）。
