"""意图分流聊天入口：先分类 intent，再走 RAG 或普通 LLM 闲聊"""
from __future__ import annotations
from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import settings
from app.services.intent_service import classify_intent, Intent
from app.api.v1.chat import get_chat_service
from app.schemas.chat import ChatRequest
from app.clients.deepseek_client import DeepSeekClient

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatReq(BaseModel):
    message: str


class ChatResp(BaseModel):
    intent: str
    confidence: float
    answer: str
    reason: str


async def rag_answer(message: str) -> str:
    """查向量库 + 知识库，返回结构化回答的短文案"""
    service = get_chat_service()
    request = ChatRequest(question=message, tenant_id=settings.DEFAULT_TENANT)
    response = await service.search_and_answer(request)
    return response.short_answer_text or "暂未找到匹配的解决方案，请补充设备型号或报警码后重试。"


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


@router.post("", response_model=ChatResp)
async def chat(req: ChatReq):
    intent_res = await classify_intent(req.message)

    if intent_res.intent == Intent.SOLUTION:
        ans = await rag_answer(req.message)
    else:
        ans = await llm_chat(req.message)

    return ChatResp(
        intent=intent_res.intent.value,
        confidence=intent_res.confidence,
        answer=ans,
        reason=intent_res.reason,
    )
