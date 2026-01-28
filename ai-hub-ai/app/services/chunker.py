"""拆分策略（q/c/t）：输出可供 embedding 的条目"""
from app.schemas.kb_article import KbArticle
from app.utils.text import clean_text, truncate
from app.utils.ids import make_vector_id


def build_chunks(article: KbArticle) -> list[dict]:
    """
    返回：
    [
      {"id": "...:q", "doc": "...", "metadata": {...}},
      {"id": "...:c", "doc": "...", "metadata": {...}},
      ...
    ]
    """
    tenant_id = article.tenant_id
    aid = article.id

    title = clean_text(article.title)
    q = clean_text(article.question_text)
    c = clean_text(article.cause_text)

    items: list[dict] = []

    # 向量A：问题
    if q:
        doc_q = truncate(f"【标题】{title}\n【问题】{q}")
        items.append({
            "id": make_vector_id(tenant_id, aid, "q"),
            "doc": doc_q,
            "metadata": {
                "tenant_id": tenant_id,
                "article_id": aid,
                "type": "q",
                "status": article.status,
                "version": article.version,
                "tags": article.tags,
            }
        })

    # 向量B：原因
    if c:
        doc_c = truncate(f"【标题】{title}\n【原因】{c}")
        items.append({
            "id": make_vector_id(tenant_id, aid, "c"),
            "doc": doc_c,
            "metadata": {
                "tenant_id": tenant_id,
                "article_id": aid,
                "type": "c",
                "status": article.status,
                "version": article.version,
                "tags": article.tags,
            }
        })

    # 可选兜底：title + question
    if title and q:
        doc_t = truncate(f"{title}。{q}")
        items.append({
            "id": make_vector_id(tenant_id, aid, "t"),
            "doc": doc_t,
            "metadata": {
                "tenant_id": tenant_id,
                "article_id": aid,
                "type": "t",
                "status": article.status,
                "version": article.version,
                "tags": article.tags,
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
