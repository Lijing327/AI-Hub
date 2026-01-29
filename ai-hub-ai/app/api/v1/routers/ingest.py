"""向量写入/重建：单条、批量、全量"""
from fastapi import APIRouter, Query
from app.api.deps import get_ingest_service
from app.core.config import settings
from app.schemas.ingest import (
    IngestArticleResponse,
    IngestBatchRequest,
    IngestAllRequest,
    IngestBatchResponse,
)

router = APIRouter(tags=["ingest"])


@router.post("/ingest/article/{article_id}", response_model=IngestArticleResponse)
def ingest_article(article_id: int):
    """重建单条向量：删旧 → 重新拆分 → 重新写入"""
    svc = get_ingest_service()
    upserted = svc.rebuild_article(article_id)
    return IngestArticleResponse(article_id=article_id, upserted=upserted)


@router.post("/ingest/batch", response_model=IngestBatchResponse)
def ingest_batch(req: IngestBatchRequest):
    """
    批量重建：tenant_id 目前主要用于未来扩展（如果你需要按 tenant 过滤 ids，可在 repo 层加校验）
    """
    svc = get_ingest_service()
    result = svc.rebuild_batch(req.ids, log_every=50)
    return IngestBatchResponse(**result)


@router.post("/ingest/all", response_model=IngestBatchResponse)
def ingest_all(req: IngestAllRequest):
    """全量重建：从 SQL 拉取 id 列表，再批量重建"""
    svc = get_ingest_service()
    tenant_id = req.tenant_id or settings.DEFAULT_TENANT
    result = svc.rebuild_all(tenant_id=tenant_id, status=req.status, limit=req.limit)
    return IngestBatchResponse(**result)


@router.get("/ingest/debug/count")
def ingest_debug_count(
    tenant_id: str | None = Query(None, description="租户 ID，不传则用配置的 DEFAULT_TENANT"),
    status: str | None = Query(None, description="按 status 过滤，不传则统计全部"),
):
    """
    调试用：返回 dbo.kb_article 中符合条件的条数。
    用于确认全量重建 total=0 是「库中无数据」还是「tenant_id/status 条件不匹配」。
    """
    svc = get_ingest_service()
    tid = tenant_id or settings.DEFAULT_TENANT
    count = svc.count_articles(tenant_id=tid, status=status)
    return {"tenant_id": tid, "status": status, "count": count}
