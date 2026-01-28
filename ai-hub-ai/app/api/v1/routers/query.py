"""语义检索：返回 article_id 列表，.NET 回表拿 solution/附件"""
from fastapi import APIRouter
from app.api.deps import get_query_service
from app.core.config import settings
from app.schemas.query import QueryRequest, QueryResponse, QueryHit

router = APIRouter(tags=["query"])


@router.post("/query", response_model=QueryResponse)
def query(req: QueryRequest):
    """POST /query - 语义检索"""
    svc = get_query_service()
    tenant_id = req.tenant_id or settings.DEFAULT_TENANT
    hits = svc.query(tenant_id=tenant_id, query_text=req.query, top_k=req.top_k)
    return QueryResponse(hits=[QueryHit(**h) for h in hits])
