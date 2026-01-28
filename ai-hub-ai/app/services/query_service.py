"""embedding → topK → 去重加权 → 返回 [{article_id, score, hit_type}]"""
from app.infra.embedding.base import IEmbedder
from app.repositories.vector_repo import VectorRepository


class QueryService:
    def __init__(self, vec_repo: VectorRepository, embedder: IEmbedder) -> None:
        self._vec_repo = vec_repo
        self._embedder = embedder

    def query(self, tenant_id: str, query_text: str, top_k: int) -> list[dict]:
        """语义检索，返回 [{article_id, score, hit_type}]"""
        qvec = self._embedder.embed_texts([query_text])[0]

        # 多取一点，方便去重
        raw = self._vec_repo.query(
            embedding=qvec,
            top_k=max(top_k * 3, 10),
            where={"tenant_id": tenant_id},
        )

        # Chroma distance 越小越好 -> 我们做一个"可理解"的分数：score = 1/(1+dist)
        def dist_to_score(dist: float) -> float:
            return 1.0 / (1.0 + max(dist, 0.0))

        # hit_type 加权：q > c > t
        weight = {"q": 1.20, "c": 1.00, "t": 0.90}

        by_article: dict[int, dict] = {}
        for item in raw:
            meta = item.get("metadata", {}) or {}
            aid = int(meta.get("article_id", 0))
            if aid <= 0:
                continue
            typ = str(meta.get("type", "q"))
            base = dist_to_score(float(item["score"]))
            final = base * weight.get(typ, 1.0)

            # 同一 article 取最高分
            old = by_article.get(aid)
            if (old is None) or (final > old["score"]):
                by_article[aid] = {"article_id": aid, "score": final, "hit_type": typ}

        # 排序取 top_k
        hits = sorted(by_article.values(), key=lambda x: x["score"], reverse=True)[:top_k]
        return hits


# 兼容旧代码的函数式接口
from typing import Optional, List
from collections import defaultdict
from app.repositories import vector_repo
from app.infra.embedding.openai_embedder import OpenAIEmbedder
from app.core.logging_config import get_logger

logger = get_logger(__name__)


def _parse_vector_id(vid: str) -> tuple[str, int, str]:
    """{tenant_id}:kb:{article_id}:q|c|t -> (tenant_id, article_id, hit_type)"""
    parts = (vid or "").split(":")
    if len(parts) >= 4:
        return parts[0], int(parts[2]) if parts[2].isdigit() else 0, parts[3]
    return "", 0, "t"


def query(
    tenant_id: str,
    query_text: str,
    top_k: int = 10,
    tags: Optional[str] = None,
    status: Optional[str] = None,
) -> List[dict]:
    """语义检索，返回 [{article_id, score, hit_type}]，按 score 降序，同 article 去重取最高分"""
    embedder = OpenAIEmbedder()
    query_embeddings = embedder.embed_batch([query_text.strip() or " "])
    if not query_embeddings:
        return []

    where: dict = {"tenant_id": tenant_id}
    if status:
        where = {"$and": [{"tenant_id": tenant_id}, {"status": status}]}

    hits = vector_repo.query(
        query_embeddings=query_embeddings,
        n_results=min(top_k * 2, 50),
        where=where,
    )

    # 去重加权：同 article_id 只保留最高分，cosine distance 转 score (1 - d) 或 1/(1+d)
    best: dict[int, tuple[float, str]] = {}
    for h in hits:
        mid = h.get("metadata") or {}
        vid = h.get("id") or ""
        t, aid, hit_type = _parse_vector_id(vid)
        if t != tenant_id or aid <= 0:
            continue
        dist = float(h.get("distance") or 0)
        score = 1.0 / (1.0 + dist) if dist >= 0 else 1.0
        if aid not in best or best[aid][0] < score:
            best[aid] = (score, hit_type)

    out = [{"article_id": aid, "score": round(s, 4), "hit_type": ht} for aid, (s, ht) in best.items()]
    out.sort(key=lambda x: -x["score"])
    return out[:top_k]
