"""智能客服问答接口"""
from typing import Optional
from fastapi import APIRouter, HTTPException

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import ChatService
from app.core.logging_config import get_logger
from app.api.deps import get_query_service, get_kb_repo

logger = get_logger(__name__)
router = APIRouter(prefix="/api/chat", tags=["智能客服"])

_chat_service: Optional[ChatService] = None


def get_chat_service() -> ChatService:
    """获取智能客服服务单例"""
    global _chat_service
    if _chat_service is None:
        _chat_service = ChatService(
            query_service=get_query_service(),
            kb_repo=get_kb_repo(),
        )
    return _chat_service


@router.post("/search", response_model=ChatResponse)
async def search_and_answer(request: ChatRequest):
    """
    搜索知识库并生成AI回答
    后续可在此接入大模型做语义匹配与自然语言生成
    """
    service = get_chat_service()
    try:
        return await service.search_and_answer(request)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("搜索和回答失败: %s", e)
        raise HTTPException(status_code=500, detail=f"搜索和回答失败: {str(e)}")
