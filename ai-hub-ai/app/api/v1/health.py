"""健康检查接口"""
from fastapi import APIRouter

router = APIRouter(tags=["健康检查"])


@router.get("/health")
async def health():
    """健康检查，用于运维探活"""
    return {"status": "ok", "service": "ai-hub-ai"}
