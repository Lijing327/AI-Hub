# 闲聊 / 能力询问 / 故障检测 区分逻辑说明

## 0）目标验收（已实现）

- 输入「你是」「你好」「你能做什么」→ **不查知识库**，走 **conversation** 回复（reply_mode=conversation）。
- 输入「不射砂」「报警」「异常」「怎么处理」→ **查知识库**（向量 + .NET 兜底），走 **solution** 回复（结构化）。
- 输入「你是什么故障」→ 判为 **solution**（不走闲聊）。
- 输入「转人工」「人工客服」「联系工程师」「找客服」等 → **不查库**，返回 **reply_mode=handoff**，前端展示转人工卡片与客服电话 0312-7027666。
- DeepSeek/LLM 不可用时：仍能用**规则兜底**分流（handoff > solution > capability > chat），且「你是」不再误命中知识库。

## 一、当前实际走哪条链路

- **前端请求**：`POST /api/chat/search`（由 `app/api/v1/chat.py` 处理）
- **入口**：`ChatService.search_and_answer(request)`（`app/services/chat_service.py`）
- **是否走意图分类**：**否**。v1 的 chat **没有**调用 `intent_service.classify_intent()`，只依赖 `chat_service` 里的 **`_is_chitchat_question(question)`** 做「是否闲聊/能力询问」判断；若为 True 则直接走 AI 不查知识库，否则一律查知识库（向量 + .NET 兜底）。

因此「你是」被当成故障检测，是因为 **`_is_chitchat_question("你是")` 当前返回 False**（见下文规则），于是会去查知识库，容易误命中故障条目。

---

## 二、闲聊/能力询问判断：`_is_chitchat_question`（chat_service.py）

当前逻辑：**仅当下面 1 或 2 成立时** 视为闲聊/能力询问，**不查知识库**。

### 1. 完整模式匹配（子串包含即可）

```python
# 视为「身份/闲聊」、直接走 AI 不查知识库的句式
CHITCHAT_PATTERNS = (
    "你是谁", "你是啥", "你是什么", "你是哪个", "介绍一下你自己", "介绍下自己",
    "你能做什么", "你能干什么", "你有什么用", "你的作用", "你的功能",
    "你是干什么的", "你是干嘛的", "你是机器人吗", "你是真人吗", "你好",
    "你会什么", "你可以做什么", "你能帮我什么",
)

# 判断：any(p in q for p in CHITCHAT_PATTERNS)
```

- 例如：「你是谁」→ 命中「你是谁」→ True，走 AI。
- **「你是」**：没有任何一个 pattern 是「你是」的子串（「你是谁」不是「你是」的子串），所以 **不命中**。

### 2. 能力咨询关键词组合（需三者都有）

```python
CAPABILITY_PREFIXES = ("你能", "你可以", "你会", "你能够")
CAPABILITY_VERBS = ("解决", "处理", "分析", "帮", "诊断", "排查", "检测", "识别", "回答")
CAPABILITY_SUFFIXES = ("什么", "哪些", "啥", "哪种", "多少")

# 判断：has_prefix and has_verb and has_suffix
```

- 「你能解决什么问题」→ 有前缀+动词+后缀 → True。
- **「你是」**：没有前缀/动词/后缀 → **不命中**。

### 3. 函数完整实现

```python
def _is_chitchat_question(question: str) -> bool:
    """
    判断是否为身份/闲聊/能力咨询类问题（如「你是谁」「你能解决什么问题」）
    这类问题直接走 AI，不查知识库
    """
    if not question or not isinstance(question, str):
        return False
    q = question.strip()
    if len(q) > 50:
        return False

    # 1. 完整模式匹配
    if any(p in q for p in CHITCHAT_PATTERNS):
        return True

    # 2. 能力咨询关键词组合匹配
    has_prefix = any(p in q for p in CAPABILITY_PREFIXES)
    has_verb = any(v in q for v in CAPABILITY_VERBS)
    has_suffix = any(s in q for s in CAPABILITY_SUFFIXES)
    if has_prefix and has_verb and has_suffix:
        return True

    return False
```

---

## 三、search_and_answer 里如何使用该判断（chat_service.py）

```python
# 身份/闲聊类问题（如「你是谁」）直接走 AI，仅以对话形式展示，不展示故障排查结构
if _is_chitchat_question(request.question) and self.deepseek_client.is_available:
    logger.info("识别为身份/闲聊问题，直接调用 AI 回答（conversation 模式）")
    ai_text = await self.deepseek_client.chat(
        user_content=request.question,
        system_prompt=AI_CHITCHAT_SYSTEM,
    )
    return _chat_response_from_ai_fallback(request.question, ai_text, reply_mode="conversation")
if _is_chitchat_question(request.question):
    logger.warning("识别为身份/闲聊问题，但 DeepSeek 未配置，返回通用提示")
# 然后继续走知识库检索（向量 -> .NET -> AI 兜底）...
```

- 只有 `_is_chitchat_question` 为 True 且配置了 DeepSeek 时，才**不查知识库**、只做对话回复。
- 「你是」当前为 False，所以会进入知识库检索，容易被误判为故障。

---

## 四、另一套「意图分类」逻辑（当前未在 /api/chat/search 使用）

项目里还有 **`app/services/intent_service.py`**，用 **LLM 做三类意图**：`chat` / `capability` / `solution`，并有兜底规则。  
但 **v1 的 POST /api/chat/search 没有调用它**，只有别处（如 `app/api/chat.py` 的聊天入口）在用。所以当前智能客服「闲聊 vs 故障」**完全依赖**上面的 `_is_chitchat_question`。

### intent_service 摘要（供扩展方案参考）

- **Intent**：`CHAT`（闲聊）、`CAPABILITY`（能力咨询）、`SOLUTION`（故障解决）。
- **LLM prompt**：要求对用户输入输出 `{"intent":"chat|capability|solution","confidence":0~1,"reason":"一句话理由"}`。
- **兜底规则**（LLM 不可用时）：
  - 含「你能做什么」「你能分析」等 → capability
  - 含「报警」「故障」「异常」「不射砂」等 → solution
  - 其余 → chat

若希望「你是」等短句也稳定走闲聊/能力，有两种方向：

1. **在 chat_service 里扩充规则**：例如在 `_is_chitchat_question` 中增加对「你是」或「以『你是』开头的短句」的判定（注意避免把「你是什么故障」误判为闲聊）。
2. **在 v1 的 search 前先走 intent_service**：先 `classify_intent(question)`，若为 `chat` 或 `capability` 则直接走 AI、不查知识库；只有 `solution` 才查知识库。这样可由 LLM 区分「你是」和「你是什么故障」。

---

## 五、建议给 ChatGPT 的提问要点

1. 用户发「你是」时被当成故障检测（走知识库），希望改为「身份/能力」类，只做简短介绍、不查知识库。
2. 当前实现：仅靠 `_is_chitchat_question(question)` 做规则判断，且 **没有** 包含「你是」或「你是」开头的短句。
3. 需求：在不把「你是什么故障」「你是哪台设备」等误判为闲聊的前提下，如何改 `CHITCHAT_PATTERNS` 或 `_is_chitchat_question` 的逻辑（和/或是否在 v1 接入 `intent_service`），才能稳定区分：**闲聊 / 能力询问 / 故障检测**。

把本文档和上面的代码片段发给 ChatGPT，即可基于现有逻辑给出具体修改方案（含推荐写法与边界 case）。

---

## 7）回归检查（本地验收）

1. 启动服务后，用 Postman 或前端分别请求：
   - `POST /api/chat/search` body: `{"question": "你是", ...}`  
   - `POST /api/chat/search` body: `{"question": "不射砂", ...}`
2. 看日志是否出现：
   - 问「你是」：`route=INTENT_CHAT` 或 `route=INTENT_CAPABILITY` 或 `route=RULE_CHITCHAT`，且**无**向量检索/.NET 检索日志。
   - 问「不射砂」：`route=RAG`，且**有**向量检索或 .NET 兜底日志。
3. 单元测试：`cd ai-hub-ai && pip install -r requirements.txt && python -m pytest tests/test_intent_chat.py -v`
4. 转人工回归：问「我要转人工」→ 日志出现 `route=INTENT_HANDOFF` 或 `route=FALLBACK_HANDOFF`，前端出现 handoff 卡片与电话 0312-7027666，不出现故障原因卡片。问「不射砂」→ 日志 `route=RAG`，前端照常故障卡片。
