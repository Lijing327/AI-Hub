"""
DeepSeek 大模型客户端
调用 OpenAI 兼容接口：POST /v1/chat/completions
用于知识库不可用时的 AI 兜底回答，或后续语义匹配、自然语言生成
"""
from typing import List, Optional

import httpx

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class DeepSeekClient:
    """DeepSeek 聊天补全客户端"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 30.0,
    ):
        self.api_key = (api_key or settings.DEEPSEEK_API_KEY or "").strip()
        self.base_url = (base_url or settings.DEEPSEEK_BASE_URL or "https://api.deepseek.com").rstrip("/")
        self.model = model or settings.DEEPSEEK_MODEL or "deepseek-chat"
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
        """
        if not self.api_key:
            logger.warning("DeepSeek API Key 未配置，跳过 AI 调用")
            return None

        url = f"{self.base_url}/v1/chat/completions"
        messages: List[dict] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_content})

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
                # OpenAI 兼容格式：choices[0].message.content
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
