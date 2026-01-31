"""意图分流聊天入口：先分类 intent，再走 RAG 或普通 LLM 闲聊

支持审计日志：
- 如果没有 conversation_id，自动创建
- 记录 user message、意图决策、RAG 检索、assistant message
"""
from __future__ import annotations
import time
from typing import Optional, List
from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import settings
from app.core.logging_config import get_logger
from app.services.intent_service import classify_intent, Intent
from app.api.v1.chat import get_chat_service
from app.schemas.chat import ChatRequest
from app.clients.deepseek_client import DeepSeekClient
from app.audit.audit_client import get_audit_client

logger = get_logger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])


class ChatReq(BaseModel):
    """聊天请求"""
    message: str
    conversation_id: Optional[str] = None  # 可选，前端传入；不传则自动创建
    user_id: Optional[str] = None
    channel: str = "web"


class ChatResp(BaseModel):
    """聊天响应"""
    intent: str
    confidence: float
    answer: str
    reason: str
    conversation_id: Optional[str] = None  # 返回给前端，用于后续消息
    message_id: Optional[str] = None  # 本条 assistant 消息 ID


class RagResult:
    """RAG 检索结果"""
    def __init__(self, answer: str, docs: List[dict]):
        self.answer = answer
        self.docs = docs


async def rag_answer(message: str) -> RagResult:
    """查向量库 + 知识库，返回结构化回答 + 命中文档"""
    service = get_chat_service()
    request = ChatRequest(question=message, tenant_id=settings.DEFAULT_TENANT)
    response = await service.search_and_answer(request)
    
    # 提取命中文档（从 cited_docs 提取）
    docs = []
    if response.cited_docs:
        for i, doc in enumerate(response.cited_docs):
            docs.append({
                "doc_id": str(doc.get("kbId", "")),
                "doc_title": doc.get("title"),
                "score": response.confidence,  # 使用整体置信度
                "rank": i + 1,
                "chunk_id": None,
            })
    
    answer = response.short_answer_text or "暂未找到匹配的解决方案，请补充设备型号或报警码后重试。"
    return RagResult(answer=answer, docs=docs)


async def llm_chat(message: str) -> str:
    """普通闲聊：不查库，直接 LLM 回复"""
    client = DeepSeekClient()
    if not client.is_available:
        return "当前未配置 AI，仅支持故障类问题检索。请描述设备故障或报警现象。"
    system = (
        "你是造型机设备的售后技术支持助手。对闲聊、寒暄类问题，请用一两句话友好简短回复。"
        "回答控制在 150 字以内。"
    )
    reply = await client.chat(user_content=message, system_prompt=system, max_tokens=256)
    return reply or "抱歉，暂时无法回复，请稍后再试。"


def capability_answer() -> str:
    """返回系统能力介绍"""
    return """我是造型机设备的智能售后助手，可以帮您解决以下问题：

**🔧 故障诊断**
描述设备异常现象（如"不射砂"、"压力异常"），我会帮您分析可能原因和排查步骤。

**⚠️ 报警码解读**
告诉我报警码（如 E001、E102），我会解释报警含义和处理方法。

**📋 操作指导**
提供常见操作的步骤指导，如设备校准、参数调整等。

**💡 使用示例**
- "设备不射砂怎么办"
- "E001 报警是什么意思"
- "压力表显示异常"

请描述您遇到的具体问题，我来帮您分析！"""


@router.post("", response_model=ChatResp)
async def chat(req: ChatReq):
    """聊天入口：意图分类 -> RAG/闲聊 -> 返回"""
    start_time = time.time()
    audit = get_audit_client()
    
    # 1. 准备 conversation_id
    conversation_id = req.conversation_id
    if not conversation_id and audit.is_enabled:
        conversation_id = await audit.start_conversation(
            tenant_id=settings.DEFAULT_TENANT,
            user_id=req.user_id,
            channel=req.channel,
        )
    
    # 2. 记录 user message
    user_message_id: Optional[str] = None
    if audit.is_enabled and conversation_id:
        user_message_id = await audit.append_message(
            conversation_id=conversation_id,
            role="user",
            content=req.message,
        )
    
    # 3. 意图识别
    intent_res = await classify_intent(req.message)
    
    # 4. 根据意图处理
    answer = ""
    docs: List[dict] = []
    fallback_reason: Optional[str] = None
    use_knowledge = False
    is_success = True
    error_type: Optional[str] = None
    error_detail: Optional[str] = None
    
    try:
        if intent_res.intent == Intent.SOLUTION:
            # 故障解决：走 RAG 查知识库
            use_knowledge = True
            result = await rag_answer(req.message)
            answer = result.answer
            docs = result.docs
            # 如果没有命中文档，标记为兜底
            if not docs:
                fallback_reason = "no_match"
        elif intent_res.intent == Intent.CAPABILITY:
            # 能力咨询：返回系统介绍
            answer = capability_answer()
        else:
            # 闲聊：LLM 简短回复
            answer = await llm_chat(req.message)
    except Exception as e:
        logger.error("处理消息异常: %s", e)
        is_success = False
        error_type = "model_error"
        error_detail = str(e)
        answer = "抱歉，处理您的问题时发生错误，请稍后重试。"
    
    # 5. 记录 assistant message
    assistant_message_id: Optional[str] = None
    if audit.is_enabled and conversation_id:
        assistant_message_id = await audit.append_message(
            conversation_id=conversation_id,
            role="assistant",
            content=answer,
        )
    
    # 6. 记录决策（关联到 user message）
    if audit.is_enabled and user_message_id:
        await audit.log_decision(
            message_id=user_message_id,
            intent_type=intent_res.intent.value,
            confidence=intent_res.confidence,
            model_name=settings.LLM_MODEL or settings.DEEPSEEK_MODEL,
            prompt_version="v1",
            use_knowledge=use_knowledge,
            fallback_reason=fallback_reason,
        )
    
    # 7. 记录 RAG 检索（如果有）
    if audit.is_enabled and user_message_id and docs:
        await audit.log_retrieval(message_id=user_message_id, docs=docs)
    
    # 8. 记录响应（关联到 assistant message）
    response_time_ms = int((time.time() - start_time) * 1000)
    if audit.is_enabled and assistant_message_id:
        await audit.log_response(
            message_id=assistant_message_id,
            final_answer=answer,
            response_time_ms=response_time_ms,
            is_success=is_success,
            error_type=error_type,
            error_detail=error_detail,
        )
    
    return ChatResp(
        intent=intent_res.intent.value,
        confidence=intent_res.confidence,
        answer=answer,
        reason=intent_res.reason,
        conversation_id=conversation_id,
        message_id=assistant_message_id,
    )
