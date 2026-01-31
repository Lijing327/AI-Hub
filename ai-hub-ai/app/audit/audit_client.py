"""审计客户端：调用 .NET internal audit API"""
import httpx
from typing import Optional, List
from app.core.config import settings
from app.core.logging_config import get_logger
from app.audit.models import (
    StartConversationRequest,
    StartConversationResponse,
    AppendMessageRequest,
    AppendMessageResponse,
    LogDecisionRequest,
    LogRetrievalRequest,
    LogResponseRequest,
    EndConversationRequest,
    RetrievalDocItem,
)

logger = get_logger(__name__)


class AuditClient:
    """审计日志客户端：封装 .NET internal API 调用"""

    def __init__(self):
        self._base_url = (settings.DOTNET_BASE_URL or "http://localhost:5000").rstrip("/")
        self._token = settings.INTERNAL_TOKEN or ""
        self._enabled = getattr(settings, "ENABLE_AUDIT_LOG", True)
        self._timeout = 10.0
        
        # 启动时记录配置状态
        logger.info(
            "AuditClient 初始化: enabled=%s, token=%s, base_url=%s",
            self._enabled,
            "已配置" if self._token else "未配置",
            self._base_url
        )

    @property
    def is_enabled(self) -> bool:
        """是否启用审计日志"""
        enabled = self._enabled and bool(self._token)
        if not enabled and self._enabled:
            logger.warning("审计日志已启用但 INTERNAL_TOKEN 未配置，跳过审计")
        return enabled

    def _headers(self) -> dict:
        return {
            "Content-Type": "application/json",
            "X-Internal-Token": self._token,
        }

    async def start_conversation(
        self,
        tenant_id: str = "default",
        user_id: Optional[str] = None,
        channel: str = "web",
        meta_json: Optional[str] = None,
    ) -> Optional[str]:
        """创建会话，返回 conversation_id；失败返回 None"""
        if not self.is_enabled:
            logger.debug("审计未启用，跳过创建会话")
            return None

        url = f"{self._base_url}/internal/ai-audit/conversation/start"
        payload = {
            "tenantId": tenant_id,
            "userId": user_id,
            "channel": channel,
            "metaJson": meta_json,
        }

        try:
            logger.info("调用审计 API 创建会话: %s", url)
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, json=payload, headers=self._headers(), timeout=self._timeout)
                logger.info("审计 API 响应: status=%d", resp.status_code)
                resp.raise_for_status()
                data = resp.json()
                conv_id = data.get("conversationId")
                logger.info("创建会话成功: %s", conv_id)
                return conv_id
        except httpx.HTTPStatusError as e:
            logger.error("创建会话失败 (HTTP %d): %s", e.response.status_code, e.response.text)
            return None
        except Exception as e:
            logger.error("创建会话失败: %s", e)
            return None

    async def append_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        is_masked: bool = False,
        masked_content: Optional[str] = None,
    ) -> Optional[str]:
        """追加消息，返回 message_id；失败返回 None"""
        if not self.is_enabled or not conversation_id:
            return None

        url = f"{self._base_url}/internal/ai-audit/message"
        payload = {
            "conversationId": conversation_id,
            "role": role,
            "content": content,
            "isMasked": is_masked,
            "maskedContent": masked_content,
        }

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, json=payload, headers=self._headers(), timeout=self._timeout)
                resp.raise_for_status()
                data = resp.json()
                msg_id = data.get("messageId")
                logger.debug("追加消息: %s, role=%s", msg_id, role)
                return msg_id
        except Exception as e:
            logger.warning("追加消息失败: %s", e)
            return None

    async def log_decision(
        self,
        message_id: str,
        intent_type: str,
        confidence: float,
        model_name: Optional[str] = None,
        prompt_version: Optional[str] = None,
        use_knowledge: bool = False,
        fallback_reason: Optional[str] = None,
        tokens_in: Optional[int] = None,
        tokens_out: Optional[int] = None,
    ) -> bool:
        """记录决策，返回是否成功"""
        if not self.is_enabled or not message_id:
            return False

        url = f"{self._base_url}/internal/ai-audit/decision"
        payload = {
            "messageId": message_id,
            "intentType": intent_type,
            "confidence": confidence,
            "modelName": model_name,
            "promptVersion": prompt_version,
            "useKnowledge": use_knowledge,
            "fallbackReason": fallback_reason,
            "tokensIn": tokens_in,
            "tokensOut": tokens_out,
        }

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, json=payload, headers=self._headers(), timeout=self._timeout)
                resp.raise_for_status()
                logger.debug("记录决策: msg=%s, intent=%s", message_id, intent_type)
                return True
        except Exception as e:
            logger.warning("记录决策失败: %s", e)
            return False

    async def log_retrieval(
        self,
        message_id: str,
        docs: List[dict],
    ) -> bool:
        """记录 RAG 检索，docs 格式：[{doc_id, doc_title, score, rank, chunk_id}]"""
        if not self.is_enabled or not message_id:
            return False

        url = f"{self._base_url}/internal/ai-audit/retrieval"
        payload = {
            "messageId": message_id,
            "docs": [
                {
                    "docId": str(d.get("doc_id") or d.get("article_id") or ""),
                    "docTitle": d.get("doc_title") or d.get("title"),
                    "score": float(d.get("score", 0)),
                    "rank": int(d.get("rank", i + 1)),
                    "chunkId": d.get("chunk_id") or d.get("hit_type"),
                }
                for i, d in enumerate(docs)
            ],
        }

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, json=payload, headers=self._headers(), timeout=self._timeout)
                resp.raise_for_status()
                logger.debug("记录检索: msg=%s, docs=%d", message_id, len(docs))
                return True
        except Exception as e:
            logger.warning("记录检索失败: %s", e)
            return False

    async def log_response(
        self,
        message_id: str,
        final_answer: Optional[str],
        response_time_ms: int,
        is_success: bool = True,
        error_type: Optional[str] = None,
        error_detail: Optional[str] = None,
    ) -> bool:
        """记录响应，返回是否成功"""
        if not self.is_enabled or not message_id:
            return False

        url = f"{self._base_url}/internal/ai-audit/response"
        payload = {
            "messageId": message_id,
            "finalAnswer": final_answer,
            "responseTimeMs": response_time_ms,
            "isSuccess": is_success,
            "errorType": error_type,
            "errorDetail": error_detail,
        }

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, json=payload, headers=self._headers(), timeout=self._timeout)
                resp.raise_for_status()
                logger.debug("记录响应: msg=%s, time=%dms", message_id, response_time_ms)
                return True
        except Exception as e:
            logger.warning("记录响应失败: %s", e)
            return False

    async def end_conversation(self, conversation_id: str) -> bool:
        """结束会话"""
        if not self.is_enabled or not conversation_id:
            return False

        url = f"{self._base_url}/internal/ai-audit/conversation/end"
        payload = {"conversationId": conversation_id}

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, json=payload, headers=self._headers(), timeout=self._timeout)
                resp.raise_for_status()
                logger.debug("结束会话: %s", conversation_id)
                return True
        except Exception as e:
            logger.warning("结束会话失败: %s", e)
            return False


# 单例
_audit_client: Optional[AuditClient] = None


def get_audit_client() -> AuditClient:
    """获取审计客户端单例"""
    global _audit_client
    if _audit_client is None:
        _audit_client = AuditClient()
    return _audit_client
