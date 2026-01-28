"""v1 路由汇聚（向量能力闭环）"""
from fastapi import APIRouter
from app.api.v1.routers import router as v1_routers

router = APIRouter(prefix="/api/v1")
router.include_router(v1_routers)
