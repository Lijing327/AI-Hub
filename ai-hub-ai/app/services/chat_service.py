"""
智能客服问答：搜索知识库并生成结构化回答
- 优先调用 .NET 知识库搜索，有结果则解析为结构化回答
- 若首次搜索结果为空且已配置 DeepSeek，则用 AI 从用户问题中提炼检索关键词再查知识库（如「球阀密封圈漏气怎么处理」→「球阀密封圈漏气」），提高命中率
- 若仍无结果或知识库不可用（502/503/超时等），则用 AI 生成兜底/引导性回答
"""
import re
from typing import List, Optional, Dict, Any

import httpx
from fastapi import HTTPException

from app.core.config import settings
from app.core.logging_config import get_logger
from app.clients.dotnet_client import DotnetClient
from app.clients.deepseek_client import DeepSeekClient
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.query_service import QueryService
from app.repositories.kb_article_repo import KbArticleRepository

logger = get_logger(__name__)

# 知识库不可用或结果为空时，让 AI 扮演售后客服的系统提示
# 强调：主动引导用户补充信息，而不是直接给建议
AI_FALLBACK_SYSTEM = (
    "你是造型机设备的售后技术支持助手。当用户的问题描述不够详细时，你需要主动、友好地引导用户补充关键信息。"
    "\n\n引导方式："
    "1. 先简短理解用户的问题（如'我理解您的设备出现了故障'）"
    "2. 然后主动提问，逐步收集信息，例如："
    "   - '请问您的设备具体是什么型号？'"
    "   - '设备出现了什么现象？是报警了吗？如果有报警码，请告诉我。'"
    "   - '最近您对设备做了什么操作？'"
    "   - '问题是什么时候开始出现的？'"
    "3. 语气要友好、专业，不要生硬地说'请补充信息'，而是用提问的方式引导"
    "4. 如果用户的问题已经比较详细（包含报警码、现象等），可以给出初步的排查建议"
    "\n\n回答控制在 200-300 字以内，重点是通过提问引导用户，而不是直接给出解决方案。"
)

# 身份/闲聊类问题直接走 AI 时用的系统提示（不查知识库）
AI_CHITCHAT_SYSTEM = (
    "你是造型机设备的售后技术支持助手。请用一两句话简短介绍自己的身份和能提供的帮助（如：设备故障、报警码、操作问题等）。"
    "回答控制在 150 字以内，语气友好专业。"
)

# 视为「身份/闲聊」、直接走 AI 不查知识库的句式（小写匹配）
CHITCHAT_PATTERNS = (
    "你是谁", "你是啥", "你是什么", "你是哪个", "介绍一下你自己", "介绍下自己",
    "你能做什么", "你能干什么", "你有什么用", "你的作用", "你的功能",
    "你是干什么的", "你是干嘛的", "你是机器人吗", "你是真人吗", "你好",
)

# 知识库无结果时，用 AI 从用户问题中提炼「检索关键词」，便于再次检索知识库
# 知识库中多为简短故障描述，如：球阀密封圈漏气、油温过高、E101报警
AI_QUERY_EXPAND_SYSTEM = (
    "你是故障知识库检索助手。用户会输入一句自然语言问题。"
    "知识库中的条目多为简短的故障/现象描述，例如：球阀密封圈漏气、油温过高、E101报警、送料异常。"
    "请从用户问题中提炼出 1～3 个可直接用于检索知识库的关键词或短语（保持与知识库表述风格一致，简短、名词或现象描述）。"
    "只输出这些关键词或短语，用英文逗号分隔，不要编号、不要解释、不要加引号。若无法提炼则输出一个最短的核心短语。"
)


def _parse_keywords_from_ai(text: Optional[str]) -> List[str]:
    """从 AI 的「检索词扩展」回复中解析出关键词列表，最多 3 个"""
    if not text or not text.strip():
        return []
    raw = text.strip()
    # 支持逗号、顿号、分号、换行分隔
    parts = re.split(r"[,，、；\n]+", raw)
    keywords: List[str] = []
    for p in parts:
        # 去掉首尾空白、编号（如 "1. "）、引号
        w = re.sub(r"^\d+[\.．、]\s*", "", p.strip()).strip(" \t\"'")
        if len(w) >= 2 and len(w) <= 50:  # 过短或过长丢弃
            keywords.append(w)
            if len(keywords) >= 3:
                break
    return keywords[:3]


def _is_chitchat_question(question: str) -> bool:
    """判断是否为身份/闲聊类问题（如「你是谁」），这类问题直接走 AI，不查知识库"""
    if not question or not isinstance(question, str):
        return False
    q = question.strip().lower()
    if len(q) > 50:
        return False
    return any(p in q for p in CHITCHAT_PATTERNS)


def parse_causes(cause_text: Optional[str]) -> List[str]:
    """从原因文本解析可能原因列表"""
    if not cause_text or not cause_text.strip():
        return []
    lines = [ln.strip() for ln in re.split(r"[\n\r；;。]", cause_text) if ln.strip()]
    causes = []
    for ln in lines:
        cleaned = re.sub(r"^\d+[\.、]?\s*", "", ln)
        cleaned = re.sub(r"^[•·]\s*", "", cleaned).strip()
        if len(cleaned) > 3:
            causes.append(cleaned)
    return causes[:5]


def parse_steps(
    solution_text: Optional[str],
    cause_text: Optional[str] = None,
) -> List[Dict[str, str]]:
    """解析排查步骤"""
    text = solution_text or cause_text or ""
    if not text:
        return []
    lines = [ln.strip() for ln in re.split(r"[\n\r；;。]", text) if ln.strip()]
    steps = []
    for i, ln in enumerate(lines, 1):
        cleaned = re.sub(r"^\d+[\.、]?\s*", "", ln)
        cleaned = re.sub(r"^[•·]\s*", "", cleaned).strip()
        if len(cleaned) <= 5:
            continue
        if re.search(r"检查|测试|校准|清理|调整|更换|维修|查看|观察", cleaned):
            steps.append({
                "title": cleaned[:50] if len(cleaned) > 50 else cleaned,
                "action": cleaned,
                "expect": "完成检查或操作",
                "next": "如问题未解决，进行下一步" if i < len(lines) else "如问题未解决，请联系技术支持",
            })
        else:
            steps.append({
                "title": f"步骤 {i}",
                "action": cleaned,
                "expect": "完成操作",
                "next": "进行下一步" if i < len(lines) else "如问题未解决，请联系技术支持",
            })
    if not steps and text:
        steps.append({
            "title": "查看解决方案",
            "action": text[:200],
            "expect": "问题得到解决",
            "next": "如问题未解决，请联系技术支持",
        })
    return steps


def parse_solution(
    solution_text: Optional[str],
    cause_text: Optional[str] = None,
) -> Dict[str, str]:
    """解析临时/根本解决文案"""
    text = solution_text or cause_text or ""
    if not text:
        return {"temporary": "暂无临时解决方案", "final": "请查看详细排查步骤或联系技术支持"}
    temp_m = re.search(r"临时[：:]\s*([^。]+)", text)
    final_m = re.search(r"(?:最终|根因|永久)[：:]\s*([^。]+)", text)
    return {
        "temporary": temp_m.group(1).strip() if temp_m else text[:100],
        "final": final_m.group(1).strip() if final_m else text,
    }


def extract_alarm_code(text: str) -> Optional[str]:
    r"""提取报警码 E\d{3}"""
    m = re.search(r"E\d{3}", text, re.IGNORECASE)
    return m.group(0).upper() if m else None


def determine_issue_category(
    title: str,
    question_text: Optional[str] = None,
    tags: Optional[str] = None,
) -> str:
    """确定问题分类"""
    combined = (title + " " + (question_text or "")).lower()
    if extract_alarm_code(title + " " + (question_text or "")):
        return "报警码"
    if "送料" in combined or "进料" in combined:
        return "送料异常"
    if "压力" in combined:
        return "压力异常"
    if "温度" in combined:
        return "温度异常"
    if tags:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        if tag_list:
            return tag_list[0]
    return "其他"


# 无匹配时的默认响应
NO_MATCH_RESPONSE = ChatResponse(
    issue_category="其他",
    confidence=0.3,
    top_causes=["问题描述不够详细", "知识库中暂无相关解决方案"],
    steps=[{
        "title": "补充问题信息",
        "action": "请提供以下信息：1) 设备型号和控制器版本；2) 报警码（如有）；3) 具体现象描述；4) 最近的操作",
        "expect": "信息完整，便于诊断",
        "next": "根据补充信息重新分析",
    }],
    solution={
        "temporary": "暂时无法提供具体解决方案，需要更多信息",
        "final": "请补充详细信息后重新咨询，或联系技术支持",
    },
    safety_tip="⚠️ 安全提示：如设备出现异常，请先停止运行，确保安全。",
    cited_docs=[],
    should_escalate=True,
    short_answer_text="问题描述不够详细，无法在知识库中找到匹配的解决方案。请补充：机型/报警码/现象/最近操作等信息，或直接转人工客服。",
)


def _chat_response_from_ai_fallback(
    question: str,
    ai_text: Optional[str],
    reply_mode: str = "troubleshooting",
) -> ChatResponse:
    """
    用 AI 生成的纯文本构造兜底 ChatResponse
    reply_mode: "conversation"=仅对话展示，不展示故障排查结构；"troubleshooting"=完整结构展示
    """
    if not ai_text or not ai_text.strip():
        return NO_MATCH_RESPONSE

    ai_text_clean = ai_text.strip()
    short_answer = ai_text_clean[:400]
    if len(ai_text_clean) > 400:
        short_answer += "..."

    # 身份/闲聊类：仅对话气泡，不展示「可能原因/排查步骤/解决方案」结构
    if reply_mode == "conversation":
        return ChatResponse(
            issue_category="其他",
            confidence=0.5,
            top_causes=[],
            steps=[],
            solution={"temporary": "", "final": ""},
            safety_tip="",
            cited_docs=[],
            should_escalate=False,
            short_answer_text=short_answer,
            related_articles=None,
            reply_mode="conversation",
        )

    # 知识库无匹配时的引导式回复：保留结构化，便于用户按步骤补充信息
    steps = []
    lines = [ln.strip() for ln in ai_text_clean.split("\n") if ln.strip()]
    question_lines = [ln for ln in lines if "？" in ln or "?" in ln]
    if question_lines:
        for i, q_line in enumerate(question_lines[:3], 1):
            steps.append({
                "title": f"补充信息 {i}",
                "action": q_line,
                "expect": "获得相关信息，便于进一步诊断",
                "next": "继续补充其他信息" if i < len(question_lines) else "根据补充信息提供解决方案",
            })
    else:
        steps.append({
            "title": "引导补充信息",
            "action": ai_text_clean[:300],
            "expect": "获得完整信息，便于诊断",
            "next": "根据补充信息提供解决方案",
        })

    return ChatResponse(
        issue_category="其他",
        confidence=0.5,
        top_causes=["为了更好地帮助您，需要补充一些关键信息"],
        steps=steps,
        solution={
            "temporary": "请根据引导补充相关信息",
            "final": "补充完整信息后，我将为您提供针对性的解决方案",
        },
        safety_tip="⚠️ 安全提示：如设备出现异常，请先停止运行，确保安全。",
        cited_docs=[],
        should_escalate=True,
        short_answer_text=short_answer,
        related_articles=None,
        reply_mode="troubleshooting",
    )


class ChatService:
    """智能客服问答服务"""

    def __init__(
        self,
        dotnet_client: Optional[DotnetClient] = None,
        deepseek_client: Optional[DeepSeekClient] = None,
        query_service: Optional[QueryService] = None,
        kb_repo: Optional[KbArticleRepository] = None,
    ):
        self.dotnet_client = dotnet_client or DotnetClient()
        self.deepseek_client = deepseek_client or DeepSeekClient()
        self._query_service = query_service
        self._kb_repo = kb_repo

    def _kb_article_to_chat_response(self, articles: list, related: list = None) -> ChatResponse:
        """将 KbArticle 列表转换为 ChatResponse"""
        if not articles:
            return NO_MATCH_RESPONSE
        
        primary = articles[0]
        related = related or (articles[1:] if len(articles) > 1 else [])

        alarm_code = extract_alarm_code(
            (primary.title or "") + " " + (primary.question_text or ""),
        )
        issue_category = determine_issue_category(
            primary.title or "",
            primary.question_text,
            primary.tags,
        )
        cause_text = primary.cause_text or ""
        solution_text = primary.solution_text or ""

        top_causes = parse_causes(cause_text)
        if not top_causes and solution_text:
            lines = [ln.strip() for ln in solution_text.split("\n") if ln.strip()]
            if lines:
                top_causes = [lines[0][:100]]

        steps = parse_steps(solution_text, cause_text)
        if not steps and cause_text:
            steps = parse_steps(cause_text)
        solution = parse_solution(solution_text, cause_text)

        confidence = 0.8
        if related:
            confidence = 0.7
        if not alarm_code and not top_causes:
            confidence = 0.6

        if alarm_code:
            short_answer = f"已识别报警码 {alarm_code}。{top_causes[0] if top_causes else '请按照排查步骤逐步检查'}。"
        elif top_causes:
            short_answer = f"{primary.title or ''}。{top_causes[0]}。建议按照排查步骤逐步检查。"
        else:
            short_answer = f"{primary.title or ''}。请查看详细排查步骤和解决方案。"

        related_list: Optional[List[Dict[str, Any]]] = None
        if related:
            related_list = [
                {
                    "id": a.id,
                    "title": a.title or "",
                    "questionText": a.question_text,
                    "excerpt": a.question_text or a.title or "",
                }
                for a in related
            ]

        return ChatResponse(
            issue_category=issue_category,
            alarm_code=alarm_code,
            confidence=confidence,
            top_causes=top_causes,
            steps=steps,
            solution=solution,
            safety_tip="⚠️ 安全提示：处理故障前请先断电，确保安全。涉及电气部件时，请由专业技术人员操作。",
            cited_docs=[{
                "kbId": str(primary.id),
                "title": primary.title or "",
                "excerpt": primary.question_text or primary.title or "",
            }],
            should_escalate=confidence < 0.7,
            short_answer_text=short_answer,
            related_articles=related_list,
        )

    async def search_and_answer(self, request: ChatRequest) -> ChatResponse:
        """
        搜索知识库并生成回答
        - 「你是谁」等身份/闲聊类问题：若已配置 DeepSeek，直接走 AI，不查知识库
        - 其余：优先使用向量检索（QueryService）；若向量检索失败或无结果，fallback 到 .NET 后端
        - 若都不可用或结果为空，且已配置 DeepSeek，则用 AI 生成兜底回答
        """
        tenant_id = request.tenant_id or settings.DEFAULT_TENANT
        self.dotnet_client.tenant_id = tenant_id
        logger.info("收到搜索请求 - 问题: %s, TenantId: %s", request.question, tenant_id)

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

        # 优先使用向量检索
        if self._query_service and self._kb_repo:
            try:
                logger.info("使用向量检索查询: %s", request.question)
                hits = self._query_service.query(
                    tenant_id=tenant_id,
                    query_text=request.question,
                    top_k=10,
                )
                if hits:
                    article_ids = [h["article_id"] for h in hits]
                    logger.info("向量检索命中 %d 条，article_ids: %s", len(hits), article_ids[:5])
                    
                    # 从数据库读取完整的 article 数据
                    articles = []
                    for aid in article_ids:
                        article = self._kb_repo.get_by_id(aid)
                        if article:
                            articles.append(article)
                    
                    if articles:
                        logger.info("成功读取 %d 条 article 数据", len(articles))
                        return self._kb_article_to_chat_response(articles)
                    else:
                        logger.warning("向量检索返回了 article_ids，但数据库查询为空")
                else:
                    logger.info("向量检索无结果")
            except Exception as e:
                logger.warning("向量检索失败，fallback 到 .NET 后端: %s", e)

        # Fallback: 使用 .NET 后端搜索
        try:
            search_result = await self.dotnet_client.search_knowledge(
                keyword=request.question,
                page_index=1,
                page_size=10,
            )
        except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError) as e:
            logger.warning("知识库请求失败，尝试 AI 兜底: %s", e)
            if self.deepseek_client.is_available:
                ai_text = await self.deepseek_client.chat(
                    user_content=request.question,
                    system_prompt=AI_FALLBACK_SYSTEM,
                )
                return _chat_response_from_ai_fallback(request.question, ai_text)
            if isinstance(e, httpx.ConnectError):
                raise HTTPException(status_code=503, detail="无法连接到知识库服务，请确保 .NET 后端已启动")
            if isinstance(e, httpx.HTTPStatusError):
                raise HTTPException(
                    status_code=502,
                    detail=f"知识库返回异常（{e.response.status_code}），请稍后重试或联系管理员",
                )
            raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")
        except Exception as e:
            logger.exception("搜索失败: %s", e)
            if self.deepseek_client.is_available:
                ai_text = await self.deepseek_client.chat(
                    user_content=request.question,
                    system_prompt=AI_FALLBACK_SYSTEM,
                )
                return _chat_response_from_ai_fallback(request.question, ai_text)
            raise HTTPException(status_code=500, detail=f"搜索和回答失败: {str(e)}")

        items = search_result.get("items", [])
        total = search_result.get("totalCount", 0)
        logger.info("搜索到 %s 条记录，返回 %s 条", total, len(items))

        # 首次无结果时，用 AI 提炼检索关键词再查知识库（如「球阀密封圈漏气怎么处理」→「球阀密封圈漏气」）
        if not items and self.deepseek_client.is_available:
            expand_text = await self.deepseek_client.chat(
                user_content=f"用户问题：{request.question}",
                system_prompt=AI_QUERY_EXPAND_SYSTEM,
                max_tokens=128,
            )
            keywords = _parse_keywords_from_ai(expand_text)
            for kw in keywords:
                if not kw or kw == request.question.strip():
                    continue
                try:
                    sr = await self.dotnet_client.search_knowledge(
                        keyword=kw, page_index=1, page_size=10
                    )
                    it = sr.get("items", [])
                    if it:
                        search_result = sr
                        items = it
                        total = sr.get("totalCount", 0)
                        logger.info("检索词扩展命中知识库，关键词: %s，命中 %s 条", kw, len(items))
                        break
                except Exception as e:
                    logger.debug("扩展关键词检索失败 kw=%s: %s", kw, e)
                    continue

        if not items:
            if self.deepseek_client.is_available:
                logger.info("知识库无匹配结果，使用 AI 兜底生成引导性回复")
                ai_text = await self.deepseek_client.chat(
                    user_content=request.question,
                    system_prompt=AI_FALLBACK_SYSTEM,
                )
                if ai_text:
                    logger.info("AI 兜底回复生成成功，长度: %d 字符", len(ai_text))
                else:
                    logger.warning("AI 兜底回复生成失败，返回默认响应")
                return _chat_response_from_ai_fallback(request.question, ai_text)
            else:
                logger.warning(
                    "知识库无匹配结果，但 DeepSeek 未配置（DEEPSEEK_API_KEY 为空），返回默认响应。"
                    "如需启用 AI 引导功能，请在 .env 中配置 DEEPSEEK_API_KEY"
                )
            return NO_MATCH_RESPONSE

        primary = items[0]
        related = items[1:] if len(items) > 1 else []

        alarm_code = extract_alarm_code(
            primary.get("title", "") + " " + (primary.get("questionText", "") or ""),
        )
        issue_category = determine_issue_category(
            primary.get("title", ""),
            primary.get("questionText"),
            primary.get("tags"),
        )
        cause_text = primary.get("causeText") or ""
        solution_text = primary.get("solutionText") or ""

        top_causes = parse_causes(cause_text)
        if not top_causes and solution_text:
            lines = [ln.strip() for ln in solution_text.split("\n") if ln.strip()]
            if lines:
                top_causes = [lines[0][:100]]

        steps = parse_steps(solution_text, cause_text)
        if not steps and cause_text:
            steps = parse_steps(cause_text)
        solution = parse_solution(solution_text, cause_text)

        confidence = 0.8
        if related:
            confidence = 0.7
        if not alarm_code and not top_causes:
            confidence = 0.6

        if alarm_code:
            short_answer = f"已识别报警码 {alarm_code}。{top_causes[0] if top_causes else '请按照排查步骤逐步检查'}。"
        elif top_causes:
            short_answer = f"{primary.get('title', '')}。{top_causes[0]}。建议按照排查步骤逐步检查。"
        else:
            short_answer = f"{primary.get('title', '')}。请查看详细排查步骤和解决方案。"

        related_list: Optional[List[Dict[str, Any]]] = None
        if related:
            related_list = [
                {
                    "id": a.get("id"),
                    "title": a.get("title", ""),
                    "questionText": a.get("questionText"),
                    "excerpt": a.get("questionText") or a.get("title", ""),
                }
                for a in related
            ]

        return ChatResponse(
            issue_category=issue_category,
            alarm_code=alarm_code,
            confidence=confidence,
            top_causes=top_causes,
            steps=steps,
            solution=solution,
            safety_tip="⚠️ 安全提示：处理故障前请先断电，确保安全。涉及电气部件时，请由专业技术人员操作。",
            cited_docs=[{
                "kbId": str(primary.get("id", "")),
                "title": primary.get("title", ""),
                "excerpt": primary.get("questionText") or primary.get("title", ""),
            }],
            should_escalate=confidence < 0.7,
            short_answer_text=short_answer,
            related_articles=related_list,
        )
