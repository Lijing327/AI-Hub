"""拆分策略（q/c/t）：输出可供 embedding 的条目"""
import json
from app.schemas.kb_article import KbArticle
from app.utils.text import clean_text, truncate
from app.utils.ids import make_vector_id
from app.utils.device_type_utils import (
    parse_device_types_from_scope,
    format_device_types_for_display,
    extract_device_type_from_text,
)


def build_chunks(article: KbArticle) -> list[dict]:
    """
    返回：
    [
      {"id": "...:q", "doc": "...", "metadata": {...}},
      {"id": "...:q", "doc": "...", "metadata": {...}},  # 多设备类型会生成多个
      ...
    ]
    """
    tenant_id = article.tenant_id
    aid = article.id

    title = clean_text(article.title)
    q = clean_text(article.question_text)
    c = clean_text(article.cause_text)

    # 解析设备类型
    device_type_codes = parse_device_types_from_scope(article.scope_json)
    is_common = len(device_type_codes) == 1 and device_type_codes[0] == "COMMON"

    # 如果没有设备类型信息，尝试从标题推断
    if device_type_codes == ["COMMON"] and article.title:
        inferred_type = extract_device_type_from_text(article.title)
        if inferred_type:
            device_type_codes = [inferred_type]
            is_common = False

    items: list[dict] = []

    # 生成设备类型文本前缀
    def _make_prefix(device_type_code: str) -> str:
        device_name = format_device_types_for_display([device_type_code])

        # 从 scope_json 中提取设备型号
        device_model = ""
        if article.scope_json:
            try:
                scope_data = json.loads(article.scope_json)
                device_model = scope_data.get("设备型号", "")
            except:
                pass

        prefix_parts = []
        if not is_common:
            prefix_parts.append(f"[设备类型:{device_name}]")
        if device_model:
            prefix_parts.append(f"[设备型号:{device_model}]")

        prefix = " ".join(prefix_parts) + "\n" if prefix_parts else ""

        # 构建增强的 chunk 文本
        chunk_parts = []
        if title:
            chunk_parts.append(f"标题：{title}")
        if q:
            chunk_parts.append(f"问题：{q}")
        if c:
            chunk_parts.append(f"原因：{c}")

        return prefix + "\n".join(chunk_parts)

    # 为每个设备类型创建 chunk
    for device_type_code in device_type_codes:
        # 向量A：问题
        if q:
            doc_q = truncate(_make_prefix(device_type_code) + f"【问题】{q}")
            items.append({
                "id": make_vector_id(tenant_id, aid, "q", device_type_code),
                "doc": doc_q,
                "metadata": {
                    "tenant_id": tenant_id,
                    "article_id": aid,
                    "type": "q",
                    "status": article.status,
                    "version": article.version,
                    "tags": article.tags,
                    "device_type_code": device_type_code,
                    "is_common": is_common,
                }
            })

        # 向量B：原因
        if c:
            doc_c = truncate(_make_prefix(device_type_code) + f"【原因】{c}")
            items.append({
                "id": make_vector_id(tenant_id, aid, "c", device_type_code),
                "doc": doc_c,
                "metadata": {
                    "tenant_id": tenant_id,
                    "article_id": aid,
                    "type": "c",
                    "status": article.status,
                    "version": article.version,
                    "tags": article.tags,
                    "device_type_code": device_type_code,
                    "is_common": is_common,
                }
            })

        # 可选兜底：title + question
        if title and q:
            doc_t = truncate(_make_prefix(device_type_code) + f"{title}。{q}")
            items.append({
                "id": make_vector_id(tenant_id, aid, "t", device_type_code),
                "doc": doc_t,
                "metadata": {
                    "tenant_id": tenant_id,
                    "article_id": aid,
                    "type": "t",
                    "status": article.status,
                    "version": article.version,
                    "tags": article.tags,
                    "device_type_code": device_type_code,
                    "is_common": is_common,
                }
            })

    return items


# 兼容旧代码
from typing import List, Literal
from dataclasses import dataclass
from app.utils.ids import HitType
from app.utils.text import clean, concat

ChunkType = Literal["q", "c", "t"]


@dataclass
class ChunkItem:
    """单条待嵌入内容"""
    article_id: int
    tenant_id: str
    hit_type: HitType
    text: str


def chunk_article(
    article_id: int,
    tenant_id: str,
    title: str,
    question_text: str | None,
    cause_text: str | None,
) -> List[ChunkItem]:
    """按规则拆成 q/c(/t)"""
    items: List[ChunkItem] = []
    t_title = clean(title)
    t_question = clean(question_text)
    t_cause = clean(cause_text)

    # q：标题 + 问题
    q_text = concat([t_title, t_question])
    if q_text:
        items.append(ChunkItem(article_id=article_id, tenant_id=tenant_id, hit_type="q", text=q_text))

    # c：标题 + 原因
    c_text = concat([t_title, t_cause])
    if c_text and c_text != q_text:
        items.append(ChunkItem(article_id=article_id, tenant_id=tenant_id, hit_type="c", text=c_text))

    # t：兜底 = title + question_text，仅在无 q 时输出，避免与 q 重复
    t_text = concat([t_title, t_question])
    if t_text and not q_text:
        items.append(ChunkItem(article_id=article_id, tenant_id=tenant_id, hit_type="t", text=t_text))

    return items
