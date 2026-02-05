"""意图分类：闲聊(chat) / 能力咨询(capability) / 故障解决(solution)"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class Intent(str, Enum):
    CHAT = "chat"              # 闲聊/寒暄/情绪
    CAPABILITY = "capability"  # 询问系统能力：你能做什么、你会分析什么
    SOLUTION = "solution"      # 故障/要解决方案
    HANDOFF = "handoff"        # 转人工/联系工程师/找客服


@dataclass
class IntentResult:
    intent: Intent
    confidence: float
    reason: str


INTENT_PROMPT = """你是工业设备售后客服的"意图分类器"。
请把用户输入分成四类，只输出 JSON（不要输出其它内容）。

【硬规则，必须遵守，按优先级】
1. 命中以下含义 → handoff（转人工优先）：
   “转人工/人工/人工客服/真人/联系工程师/找客服/转接/电话/售后电话/客服/投诉/人工服务”
   示例：「我要你转人工」「转人工」「找客服」「联系工程师」
2. 只要用户输入中包含“故障/报警/异常/报错/不工作/不射砂/不出砂/卡住/停机/怎么处理/怎么办”等描述设备问题的词，一律归为 solution。
   “你是什么故障”“你是啥故障”“这是什么故障”等问设备故障类型，归为 solution。
3. “你是谁/你是/你好/在吗/你能做什么”等身份或能力询问，归为 chat 或 capability。

【四类定义】
- handoff：用户明确要求转人工、找真人、联系工程师、客服电话、投诉等。示例：转人工、我要转人工、找客服、联系工程师、人工客服。
- chat：闲聊/寒暄/情绪表达。示例：你好、谢谢、再见、辛苦了。
- capability：询问系统能力/功能介绍。示例：你能做什么、你会分析什么问题、你有什么功能。
- solution：描述具体设备故障、异常、报警、请求排查或解决方案。示例：设备不射砂、E001报警、你是什么故障。

【边界样例】
「我要你转人工」→ handoff
「转人工」→ handoff
「你是什么故障」→ solution
「你能做什么」→ capability
「你好」→ chat

输出 JSON 格式（严格只输出这一行）：
{{"intent":"chat|capability|solution|handoff","confidence":0~1,"reason":"一句话理由"}}

用户输入：
{user_input}
"""


def _fallback_rule(user_input: str) -> IntentResult:
    """兜底规则：handoff > solution > capability > chat"""
    q = (user_input or "").strip()
    # 1. 转人工优先
    keywords_handoff = (
        "转人工", "人工客服", "人工服务", "真人", "联系工程师", "找客服",
        "转接", "售后电话", "客服电话", "投诉",
    )
    if any(k in q for k in keywords_handoff):
        return IntentResult(intent=Intent.HANDOFF, confidence=0.70, reason="命中转人工关键词(兜底)")
    # 2. 故障/解决方案关键词
    keywords_solution = [
        "报警", "故障", "异常", "停机", "不工作", "不出", "无法",
        "怎么办", "如何解决", "原因", "为什么", "报错",
        "不射砂", "不合箱", "不翻箱", "压力", "温度", "卡住", "不出砂",
    ]
    if any(k in q for k in keywords_solution):
        return IntentResult(intent=Intent.SOLUTION, confidence=0.60, reason="命中故障/解决关键词(兜底)")
    # 3. 能力咨询关键词
    keywords_capability = [
        "你能做什么", "你会什么", "能帮我什么", "有什么功能",
        "你能分析", "能分析什么", "你能解决", "能解决什么",
        "你是干什么的", "你的功能", "系统能做什么",
    ]
    for kw in keywords_capability:
        if kw in q:
            return IntentResult(intent=Intent.CAPABILITY, confidence=0.70, reason="命中能力咨询关键词(兜底)")
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
        if intent_str == "handoff":
            intent = Intent.HANDOFF
        elif intent_str == "solution":
            intent = Intent.SOLUTION
        elif intent_str == "capability":
            intent = Intent.CAPABILITY
        else:
            intent = Intent.CHAT
        
        # 置信度范围校验；低于阈值时走兜底规则更安全，避免漏检故障
        conf = max(0.0, min(1.0, conf))
        if conf < 0.55:
            return _fallback_rule(user_input)

        return IntentResult(intent=intent, confidence=conf, reason=reason or "ok")
    except Exception:
        return _fallback_rule(user_input)
