# 向量能力闭环 - 设置与验证指南

## 一、依赖安装

```bash
# 安装新增依赖
pip install pydantic-settings
```

所有依赖已在 `requirements.txt` 中，运行：
```bash
pip install -r requirements.txt
```

## 二、配置 .env

复制 `.env.example` 为 `.env`，并配置以下项：

```env
# SQL Server（必须）
SQLSERVER_DSN=Driver={ODBC Driver 17 for SQL Server};Server=localhost;Database=ai_hub;Trusted_Connection=yes;

# Embedding（先用 fake 联调）
EMBEDDING_PROVIDER=fake

# Chroma（可选，有默认值）
CHROMA_PERSIST_DIR=./data/chroma
CHROMA_COLLECTION=kb_articles
```

## 三、Windows ODBC Driver 安装

如果本机缺少 **ODBC Driver 17 for SQL Server**，需要安装：

1. 下载地址：https://learn.microsoft.com/zh-cn/sql/connect/odbc/download-odbc-driver-for-sql-server
2. 或使用 SQL Server 安装包自带的驱动
3. 安装后，在连接串中使用 `Driver={ODBC Driver 17 for SQL Server}`

## 四、启动服务

```bash
# Windows
.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Linux/Mac
.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 五、验证步骤

### 1. 健康检查

```bash
GET http://localhost:8000/api/v1/health
```

预期响应：
```json
{"ok": true}
```

### 2. 重建单条向量

**前提**：SQL Server 的 `dbo.kb_article` 表中有数据，例如 `id=601`。

```bash
POST http://localhost:8000/api/v1/ingest/article/601
```

预期响应：
```json
{
  "article_id": 601,
  "upserted": 2
}
```

说明：`upserted` 表示写入的向量条数（q/c/t，通常 2-3 条）。

### 3. 语义检索

```bash
POST http://localhost:8000/api/v1/query
Content-Type: application/json

{
  "tenant_id": "default",
  "query": "下芯轴不动作怎么办",
  "top_k": 5
}
```

预期响应：
```json
{
  "hits": [
    {
      "article_id": 601,
      "score": 0.85,
      "hit_type": "q"
    },
    ...
  ]
}
```

说明：返回的 `article_id` 列表，.NET 可按这些 id 回表取 `solution_text` 和附件。

## 六、从 fake 切换到 OpenAI

修改 `.env`：
```env
EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=你的key
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

重启服务即可。向量维度会自动从 64（fake）切换到 1536（OpenAI），Chroma 会自动适应。

## 七、目录结构

```
app/
├─ api/
│  ├─ deps.py              # 依赖注入
│  └─ v1/
│     ├─ routers/         # 向量路由（health/ingest/query）
│     └─ router.py        # 旧路由（兼容）
├─ core/
│  ├─ config.py           # 配置（pydantic-settings）
│  ├─ logging.py          # 日志（新增）
│  └─ exceptions.py       # 异常（含 AppError）
├─ infra/
│  ├─ db/sqlserver.py     # SQL Server 连接
│  ├─ embedding/
│  │  ├─ base.py          # IEmbedder 接口
│  │  ├─ fake_embedder.py # 本地伪向量（联调用）
│  │  └─ openai_embedder.py
│  └─ vectorstore/
│     ├─ base.py          # IVectorStore 接口
│     └─ chroma_store.py  # Chroma 实现
├─ repositories/
│  ├─ kb_article_repo.py  # 读 kb_article
│  └─ vector_repo.py      # 向量库抽象
├─ schemas/
│  ├─ kb_article.py       # KbArticle DTO
│  ├─ ingest.py            # IngestArticleResponse
│  └─ query.py            # QueryRequest/Response
├─ services/
│  ├─ chunker.py          # 拆分规则（q/c/t）
│  ├─ ingest_service.py   # 重建向量服务
│  └─ query_service.py    # 语义检索服务
└─ utils/
   ├─ ids.py              # 向量 id 生成
   └─ text.py             # 文本清洗/截断
```

## 八、常见问题

### Q: 启动时报 "No module named 'fastapi'"
A: 确保在虚拟环境中安装依赖：`.venv\Scripts\python.exe -m pip install -r requirements.txt`

### Q: SQL Server 连接失败
A: 检查：
1. ODBC Driver 17 是否已安装
2. 连接串中的 Server、Database 是否正确
3. 是否使用 Trusted_Connection 或 UID/PWD

### Q: Chroma 报维度不匹配
A: 首次使用 fake（64 维）后切换到 OpenAI（1536 维）时，需要删除 `./data/chroma` 目录重新创建，或使用不同的 `CHROMA_COLLECTION` 名称。

### Q: 向量检索无结果
A: 检查：
1. 是否已调用 `/ingest/article/{id}` 写入向量
2. `tenant_id` 是否匹配
3. 查询文本是否与知识库内容相关
