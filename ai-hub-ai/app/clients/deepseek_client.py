"""
对话 LLM 客户端：支持直连 DeepSeek 或百炼兼容（dashscope + deepseek-v3.2 / qwen-plus）
统一走 OpenAI 兼容接口：POST /v1/chat/completions
"""
from typing import List, Optional

import httpx
from openai import AsyncOpenAI

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


def _use_dashscope_llm() -> bool:
    """是否使用百炼兼容模式（base_url + model 已配置）"""
    base = (settings.LLM_BASE_URL or "").strip()
    model = (settings.LLM_MODEL or "").strip()
    key = (settings.LLM_API_KEY or settings.DASHSCOPE_API_KEY or "").strip()
    return bool(base and model and key)


class DeepSeekClient:
    """对话 LLM 客户端：DeepSeek 直连 或 百炼兼容（openai 库）"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 30.0,
    ):
        self._use_dashscope = _use_dashscope_llm()
        if self._use_dashscope:
            self.api_key = (api_key or settings.LLM_API_KEY or settings.DASHSCOPE_API_KEY or "").strip()
            self.base_url = (base_url or settings.LLM_BASE_URL or "").rstrip("/")
            self.model = (model or settings.LLM_MODEL or "").strip()
            self._client: Optional[AsyncOpenAI] = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
            logger.info("对话 LLM 使用百炼兼容: base_url=%s, model=%s", self.base_url, self.model)
        else:
            self.api_key = (api_key or settings.DEEPSEEK_API_KEY or "").strip()
            self.base_url = (base_url or settings.DEEPSEEK_BASE_URL or "https://api.deepseek.com").rstrip("/")
            self.model = model or settings.DEEPSEEK_MODEL or "deepseek-chat"
            self._client = None
        self.timeout = timeout

    @property
    def is_available(self) -> bool:
        """是否已配置 API Key，可用以调用"""
        return bool(self.api_key)

    async def chat(
        self,
        user_content: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
    ) -> Optional[str]:
        """
        调用 chat completions，返回助手回复正文；失败返回 None
        百炼兼容时用 openai 库，否则用 httpx 直连 DeepSeek
        """
        if not self.api_key:
            logger.warning("对话 API Key 未配置，跳过 AI 调用")
            return None

        messages: List[dict] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_content})

        if self._use_dashscope and self._client:
            return await self._chat_openai(messages, max_tokens)
        return await self._chat_httpx(messages, max_tokens)

    async def _chat_openai(self, messages: List[dict], max_tokens: int) -> Optional[str]:
        """百炼兼容：openai 库非流式"""
        try:
            resp = await self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.3,
            )
            choices = resp.choices or []
            if choices:
                msg = choices[0].message
                if msg and getattr(msg, "content", None):
                    return (msg.content or "").strip()
            return None
        except Exception as e:
            logger.warning("百炼对话调用异常: %s", e)
            return None

    async def _chat_httpx(self, messages: List[dict], max_tokens: int) -> Optional[str]:
        """直连 DeepSeek：httpx"""
        url = f"{self.base_url}/v1/chat/completions"
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.3,
        }
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    timeout=self.timeout,
                )
                response.raise_for_status()
                data = response.json()
                choices = data.get("choices") or []
                if choices:
                    msg = choices[0].get("message")
                    if isinstance(msg, dict):
                        return (msg.get("content") or "").strip()
                return None
        except httpx.HTTPStatusError as e:
            logger.warning("DeepSeek API 请求失败: %s %s", e.response.status_code, e.response.text[:200])
            return None
        except Exception as e:
            logger.warning("DeepSeek 调用异常: %s", e)
            return None
