"""语义检索请求与响应 DTO"""
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    tenant_id: str | None = None
    query: str = Field(min_length=1)
    top_k: int = 5


class QueryHit(BaseModel):
    article_id: int
    score: float
    hit_type: str  # q/c/t


class QueryResponse(BaseModel):
    hits: list[QueryHit]
