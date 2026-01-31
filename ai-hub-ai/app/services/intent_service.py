"""意图分类：闲聊(chat) / 能力咨询(capability) / 故障解决(solution)"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class Intent(str, Enum):
    CHAT = "chat"              # 闲聊/寒暄/情绪
    CAPABILITY = "capability"  # 询问系统能力：你能做什么、你会分析什么
    SOLUTION = "solution"      # 故障/要解决方案


@dataclass
class IntentResult:
    intent: Intent
    confidence: float
    reason: str


INTENT_PROMPT = """你是工业设备售后客服的"意图分类器"。
请把用户输入分成三类，只输出 JSON（不要输出其它内容）：

- chat：闲聊/寒暄/情绪表达/客套/感谢/问候
  示例：你好、谢谢、再见、辛苦了

- capability：询问系统能力/功能介绍/能帮什么忙
  示例：你能做什么、你会分析什么问题、你有什么功能、能帮我什么

- solution：描述具体设备故障、异常、报警、请求排查或解决方案
  示例：设备不射砂、E001报警、压力异常、为什么停机

注意：如果用户只是问"你能分析什么"而没有描述具体故障，应该是 capability 而不是 solution。

输出 JSON 格式：
{{"intent":"chat|capability|solution","confidence":0~1,"reason":"一句话理由"}}

用户输入：
{user_input}
"""


def _fallback_rule(user_input: str) -> IntentResult:
    """兜底规则：模型不可用或输出异常时使用"""
    # 能力咨询关键词
    keywords_capability = [
        "你能做什么", "你会什么", "能帮我什么", "有什么功能",
        "你能分析", "能分析什么", "你能解决", "能解决什么",
        "你是干什么的", "你的功能", "系统能做什么",
    ]
    for kw in keywords_capability:
        if kw in user_input:
            return IntentResult(intent=Intent.CAPABILITY, confidence=0.70, reason="命中能力咨询关键词(兜底)")
    
    # 故障/解决方案关键词
    keywords_solution = [
        "报警", "故障", "异常", "停机", "不工作", "不出", "无法",
        "怎么办", "如何解决", "原因", "为什么", "报错",
        "不射砂", "不合箱", "不翻箱", "压力", "温度",
    ]
    if any(k in user_input for k in keywords_solution):
        return IntentResult(intent=Intent.SOLUTION, confidence=0.60, reason="命中故障/解决关键词(兜底)")
    
    return IntentResult(intent=Intent.CHAT, confidence=0.55, reason="未命中特定关键词(兜底)")


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

        # 解析意图类型
        if intent_str == "solution":
            intent = Intent.SOLUTION
        elif intent_str == "capability":
            intent = Intent.CAPABILITY
        else:
            intent = Intent.CHAT
        
        # 置信度范围校验
        conf = max(0.0, min(1.0, conf))

        return IntentResult(intent=intent, confidence=conf, reason=reason or "ok")
    except Exception:
        return _fallback_rule(user_input)
