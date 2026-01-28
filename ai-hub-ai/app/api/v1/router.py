"""v1 路由汇聚，对外 API 路径与原先保持一致"""
from fastapi import APIRouter

from app.api.v1 import health
from app.api.v1 import import_excel
from app.api.v1 import attachments
from app.api.v1 import chat
from app.api.v1 import router as v1_vector_router

# 汇聚所有 v1 路由，路径保持兼容：/health、/import/excel、/api/chat/search
api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(import_excel.router)
api_router.include_router(attachments.router)
api_router.include_router(chat.router)
# 向量能力闭环：/api/v1/health、/api/v1/ingest/*、/api/v1/query（已带 prefix="/api/v1"）
api_router.include_router(v1_vector_router)
