"""健康检查接口"""
from fastapi import APIRouter

router = APIRouter(tags=["健康检查"])


@router.get("/health")
async def health():
    """健康检查，用于运维探活（含 ok 字段便于探针判断）"""
    return {"ok": True, "status": "ok", "service": "ai-hub-ai"}
