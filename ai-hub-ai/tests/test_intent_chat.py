"""
意图识别与闲聊兜底规则测试
验收：闲聊/能力不查库，故障查库；「你是什么故障」→ solution；LLM 不可用时规则兜底
"""
import pytest
from app.services.intent_service import (
    Intent,
    _fallback_rule,
    classify_intent,
)
from app.services.chat_service import _is_chitchat_question, _is_handoff_question


# ----- 规则兜底 _fallback_rule / _is_chitchat_question（不依赖 LLM）-----


@pytest.mark.parametrize("q", ["你是", "你能做什么", "你好"])
def test_chitchat_rule_returns_true(q: str):
    """「你是」「你能做什么」「你好」→ 规则判为闲聊/能力，不查库"""
    assert _is_chitchat_question(q) is True


@pytest.mark.parametrize("q", ["不射砂", "报警了怎么处理"])
def test_solution_rule_returns_false(q: str):
    """「不射砂」「报警了怎么处理」→ 规则不判闲聊，应走查库"""
    assert _is_chitchat_question(q) is False


def test_what_fault_solution_rule():
    """「你是什么故障」→ 规则不判闲聊，应走查库（solution）"""
    assert _is_chitchat_question("你是什么故障") is False


def test_fallback_intent_what_fault():
    """兜底规则：「你是什么故障」→ SOLUTION"""
    r = _fallback_rule("你是什么故障")
    assert r.intent == Intent.SOLUTION


def test_fallback_intent_no_sand():
    """兜底规则：「不射砂」→ SOLUTION"""
    r = _fallback_rule("不射砂")
    assert r.intent == Intent.SOLUTION


def test_fallback_intent_ability():
    """兜底规则：「你能做什么」→ CAPABILITY"""
    r = _fallback_rule("你能做什么")
    assert r.intent == Intent.CAPABILITY


def test_short_greeting_chitchat():
    """极短句止血：「在吗」「哈喽」→ 闲聊"""
    assert _is_chitchat_question("在吗") is True
    assert _is_chitchat_question("哈喽") is True


def test_fallback_handoff():
    """兜底规则：「转人工」「我要转人工」→ HANDOFF"""
    r = _fallback_rule("转人工")
    assert r.intent == Intent.HANDOFF
    r2 = _fallback_rule("我要转人工")
    assert r2.intent == Intent.HANDOFF


# ----- 意图分类 classify_intent（依赖 LLM，可 mock 或跳过）-----


@pytest.mark.asyncio
async def test_classify_intent_you_are():
    """「你是」→ chat 或 capability（不查库）；若 LLM 异常则兜底也为 CHAT"""
    r = await classify_intent("你是")
    assert r.intent in (Intent.CHAT, Intent.CAPABILITY)


@pytest.mark.asyncio
async def test_classify_intent_no_sand():
    """「不射砂」→ solution（查库）；若 LLM 异常则兜底也为 SOLUTION"""
    r = await classify_intent("不射砂")
    assert r.intent == Intent.SOLUTION


@pytest.mark.asyncio
async def test_classify_intent_what_fault():
    """「你是什么故障」→ solution（查库）"""
    r = await classify_intent("你是什么故障")
    assert r.intent == Intent.SOLUTION


def test_handoff_question_detection():
    """规则：转人工/找客服/联系工程师 → handoff"""
    assert _is_handoff_question("转人工") is True
    assert _is_handoff_question("我要转人工") is True
    assert _is_handoff_question("联系工程师") is True
    assert _is_handoff_question("找客服") is True
    assert _is_handoff_question("不射砂") is False


# ----- 验收说明 -----
# 运行：cd ai-hub-ai && pip install -r requirements.txt && python -m pytest tests/test_intent_chat.py -v
# 若未配置 LLM，classify_intent 会走兜底规则，async 测试仍可验证兜底结果。
