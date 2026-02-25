"""智能客服问答接口（v1）"""
import time
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends

from app.schemas.chat import ChatRequest, ChatResponse, ArticleDetailResponse
from app.services.chat_service import ChatService, _is_chitchat_question
from app.core.config import settings
from app.core.logging_config import get_logger
from app.api.deps import get_query_service, get_kb_repo
from app.audit.audit_client import get_audit_client
from app.core.auth import get_current_user

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


@router.get("/article-detail", response_model=ArticleDetailResponse)
def get_article_detail(article_id: int):
    """
    按文章 ID 返回单条详情（可能原因、排查步骤、解决方案、参考资料）。
    前端点击「其他问题」时调用，无需首次搜索即拉取全量。
    """
    service = get_chat_service()
    detail = service.get_article_detail(article_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="文章不存在或已删除")
    return detail


@router.post("/search", response_model=ChatResponse)
async def search_and_answer(
    request: ChatRequest,
    authorization: str = None
):
    """
    搜索知识库并生成AI回答
    支持审计日志：
    - 传入 conversation_id 则加入现有会话
    - 不传则自动创建新会话
    - 响应中返回 conversation_id 和 message_id
    """
    start_time = time.time()
    audit = get_audit_client()
    service = get_chat_service()

    # 1. 准备用户ID（从认证头获取，如果有的话）
    current_user_id = request.user_id
    if authorization and authorization.startswith("Bearer "):
        # 如果有JWT token，使用它作为user_id
        current_user_id = f"jwt_{authorization.split(' ')[1][:8]}"

    # 2. 准备 conversation_id
    conversation_id = request.conversation_id
    if not conversation_id and audit.is_enabled:
        conversation_id = await audit.start_conversation(
            tenant_id=request.tenant_id or settings.DEFAULT_TENANT,
            user_id=current_user_id,
            channel=request.channel,
        )
    
    # 2. 记录 user message
    user_message_id: Optional[str] = None
    if audit.is_enabled and conversation_id:
        user_message_id = await audit.append_message(
            conversation_id=conversation_id,
            role="user",
            content=request.question,
        )
    
    # 3. 执行搜索和回答
    is_success = True
    error_type: Optional[str] = None
    error_detail: Optional[str] = None
    response: Optional[ChatResponse] = None
    
    try:
        response = await service.search_and_answer(request)
    except HTTPException:
        raise
    except Exception as e:
        is_success = False
        error_type = "model_error"
        error_detail = str(e)
        logger.exception("搜索和回答失败: %s", e)
        raise HTTPException(status_code=500, detail=f"搜索和回答失败: {str(e)}")
    finally:
        response_time_ms = int((time.time() - start_time) * 1000)
        
        # 4. 记录 assistant message
        assistant_message_id: Optional[str] = None
        if audit.is_enabled and conversation_id and response:
            assistant_message_id = await audit.append_message(
                conversation_id=conversation_id,
                role="assistant",
                content=response.short_answer_text,
            )
        
        # 5. 记录决策（关联到 user message）
        if audit.is_enabled and user_message_id and response:
            # 判断意图类型：转人工 / 闲聊 / 故障解决
            if getattr(response, "reply_mode", None) == "handoff":
                intent_type = "handoff"
            else:
                is_chitchat = _is_chitchat_question(request.question)
                intent_type = "chat" if is_chitchat else "solution"
            
            # 判断是否使用了知识库（cited_docs 非空）
            use_knowledge = bool(response.cited_docs)
            fallback_reason = None
            if not use_knowledge or response.confidence < 0.5:
                fallback_reason = "no_match" if not use_knowledge else "low_confidence"
            
            await audit.log_decision(
                message_id=user_message_id,
                intent_type=intent_type,
                confidence=response.confidence,
                model_name=settings.LLM_MODEL or settings.DEEPSEEK_MODEL,
                prompt_version="v1",
                use_knowledge=use_knowledge,
                fallback_reason=fallback_reason,
            )
        
        # 6. 记录 RAG 检索（从 cited_docs 提取）
        if audit.is_enabled and user_message_id and response and response.cited_docs:
            docs = [
                {
                    "doc_id": doc.get("kbId", ""),
                    "doc_title": doc.get("title"),
                    "score": response.confidence,
                    "rank": i + 1,
                }
                for i, doc in enumerate(response.cited_docs)
            ]
            await audit.log_retrieval(message_id=user_message_id, docs=docs)
        
        # 7. 记录响应
        if audit.is_enabled and assistant_message_id:
            await audit.log_response(
                message_id=assistant_message_id,
                final_answer=response.short_answer_text if response else None,
                response_time_ms=response_time_ms,
                is_success=is_success,
                error_type=error_type,
                error_detail=error_detail,
            )
    
    # 8. 填充审计字段到响应
    if response:
        response.conversation_id = conversation_id
        response.message_id = assistant_message_id
    
    return response
