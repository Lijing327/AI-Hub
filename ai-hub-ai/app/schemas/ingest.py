"""向量写入 / 重建请求与响应 DTO"""
from pydantic import BaseModel, Field


class IngestArticleResponse(BaseModel):
    article_id: int
    upserted: int


class IngestBatchRequest(BaseModel):
    tenant_id: str | None = None
    ids: list[int] = Field(min_length=1)


class IngestAllRequest(BaseModel):
    tenant_id: str | None = None
    status: str | None = None  # 例如：published
    limit: int | None = None  # 开发阶段可限制一下，避免一次跑太大


class IngestBatchResponse(BaseModel):
    total: int
    success: int
    upserted_total: int
    failed: list[dict]


# 保留兼容旧代码
class IngestResponse(BaseModel):
    """单条/批量写入结果"""
    ok: bool = True
    ingested: int = 0
    message: str | None = None
