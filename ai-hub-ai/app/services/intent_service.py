"""意图分类：闲聊(chat) vs 要解决方案(solution)，供统一聊天入口分流"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class Intent(str, Enum):
    CHAT = "chat"          # 闲聊/寒暄/情绪
    SOLUTION = "solution"  # 故障/要解决方案


@dataclass
class IntentResult:
    intent: Intent
    confidence: float
    reason: str


INTENT_PROMPT = """你是工业设备售后客服的"意图分类器"。
请把用户输入分成两类，只输出 JSON（不要输出其它内容）：
- chat：闲聊/寒暄/情绪表达/客套
- solution：设备故障、异常、报警、排查原因、请求解决方案

输出 JSON 格式：
{"intent":"chat|solution","confidence":0~1,"reason":"一句话理由"}

用户输入：
{user_input}
"""


def _fallback_rule(user_input: str) -> IntentResult:
    """兜底规则：模型不可用或输出异常时使用"""
    keywords_solution = [
        "报警", "故障", "异常", "停机", "不工作", "不出", "无法",
        "怎么办", "如何解决", "原因", "为什么", "报错",
    ]
    hit = any(k in user_input for k in keywords_solution)
    if hit:
        return IntentResult(intent=Intent.SOLUTION, confidence=0.60, reason="命中故障/解决关键词(兜底)")
    return IntentResult(intent=Intent.CHAT, confidence=0.55, reason="未命中故障关键词(兜底)")


async def classify_intent(user_input: str) -> IntentResult:
    """调用 LLM 做意图分类；异常时走兜底规则"""
    from app.services.llm_service import call_llm, safe_json_loads

    try:
        prompt = INTENT_PROMPT.format(user_input=user_input.strip())
        raw = await call_llm(prompt)
        data = safe_json_loads(raw)

        intent_str = str(data.get("intent", "")).strip().lower()
        conf = float(data.get("confidence", 0.5))
        reason = str(data.get("reason", "")).strip()[:60]

        intent = Intent.SOLUTION if intent_str == "solution" else Intent.CHAT
        if conf < 0:
            conf = 0.0
        if conf > 1:
            conf = 1.0

        return IntentResult(intent=intent, confidence=conf, reason=reason or "ok")
    except Exception:
        return _fallback_rule(user_input)
