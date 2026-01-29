"""统一 LLM 调用：对接 DeepSeek，供意图分类等使用"""
from __future__ import annotations
import json
from typing import Any, Dict

from app.clients.deepseek_client import DeepSeekClient


async def call_llm(prompt: str) -> str:
    """调用 DeepSeek 返回纯文本；未配置或失败时抛出或返回空，由调用方兜底"""
    client = DeepSeekClient()
    if not client.is_available:
        raise RuntimeError("DeepSeek 未配置，无法调用 LLM")
    result = await client.chat(
        user_content=prompt,
        system_prompt="你只输出用户要求的内容，不要加任何解释或前后缀。",
        max_tokens=256,
    )
    if result is None:
        raise RuntimeError("DeepSeek 调用无返回")
    return result


def safe_json_loads(text: str) -> Dict[str, Any]:
    """尽量容错解析 JSON：去掉代码块、前后杂文本"""
    t = text.strip()
    if t.startswith("```"):
        t = t.strip("`")
        idx = t.find("{")
        if idx >= 0:
            t = t[idx:]
    l = t.find("{")
    r = t.rfind("}")
    if l >= 0 and r > l:
        t = t[l : r + 1]
    return json.loads(t)
