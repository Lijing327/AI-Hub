"""embedding → topK → 去重加权 → 返回 [{article_id, score, hit_type}]"""
from typing import Optional, List
from app.core.logging_config import get_logger
from app.infra.embedding.base import IEmbedder
from app.repositories.vector_repo import VectorRepository

logger = get_logger(__name__)


class QueryService:
    def __init__(self, vec_repo: VectorRepository, embedder: IEmbedder) -> None:
        self._vec_repo = vec_repo
        self._embedder = embedder

    def query(
        self,
        tenant_id: str,
        query_text: str,
        top_k: int,
        device_type_code: Optional[str] = None,
        enable_fallback: bool = True
    ) -> list[dict]:
        """
        语义检索，返回 [{article_id, score, hit_type}]

        Args:
            tenant_id: 租户ID
            query_text: 查询文本
            top_k: 返回结果数量
            device_type_code: 设备类型代码，为 None 时使用原逻辑
            enable_fallback: 是否启用兜底机制
        """
        qvec = self._embedder.embed_texts([query_text])[0]

        # 设备类型过滤逻辑
        if device_type_code:
            # 第一阶段：按设备类型过滤
            hits = self._query_with_device_filter(
                qvec, tenant_id, device_type_code, top_k
            )

            # 检查是否需要兜底
            if enable_fallback and self._need_fallback(hits, top_k):
                logger.info(
                    "第一阶段结果不足，启用兜底机制。设备类型: %s, 命中: %d",
                    device_type_code, len(hits)
                )
                # 第二阶段：宽松查询（不限制设备类型）
                fallback_hits = self._query_with_device_filter(
                    qvec, tenant_id, None, top_k
                )
                # 合并结果，优先显示第一阶段的结果
                hits = self._merge_results(hits, fallback_hits, top_k)
        else:
            # 保持原有逻辑
            raw = self._vec_repo.query(
                embedding=qvec,
                top_k=max(top_k * 3, 10),
                where={"tenant_id": tenant_id},
            )
            hits = self._process_raw_results(raw, top_k)

        return hits

    def _query_with_device_filter(
        self,
        qvec: List[float],
        tenant_id: str,
        device_type_code: Optional[str],
        top_k: int
    ) -> list[dict]:
        """使用设备类型过滤进行查询"""
        if device_type_code:
            # 构造 where 条件：设备类型匹配或通用知识
            where = {
                "$or": [
                    {"device_type_code": device_type_code},
                    {"device_type_code": "COMMON"}
                ]
            }
            # 同时确保 tenant_id 匹配
            where["$and"] = [{"tenant_id": tenant_id}]
        else:
            # 仅按 tenant_id 过滤
            where = {"tenant_id": tenant_id}

        # 多取一点，方便去重
        raw = self._vec_repo.query(
            embedding=qvec,
            top_k=max(top_k * 3, 10),
            where=where,
        )
        return self._process_raw_results(raw, top_k)

    def _need_fallback(self, hits: list[dict], top_k: int) -> bool:
        """判断是否需要启用兜底机制"""
        # 如果命中数量少于 top_k，需要兜底
        if len(hits) < top_k:
            return True

        # 如果最高分过低（低于0.5），说明匹配质量不高，需要兜底
        if hits and hits[0]["score"] < 0.5:
            return True

        return False

    def _merge_results(
        self,
        primary_hits: list[dict],
        fallback_hits: list[dict],
        top_k: int
    ) -> list[dict]:
        """合并第一阶段和第二阶段的结果"""
        # 收集已包含的文章ID
        seen_articles = set()
        merged_hits = []

        # 先添加第一阶段的结果
        for hit in primary_hits:
            if hit["article_id"] not in seen_articles:
                merged_hits.append(hit)
                seen_articles.add(hit["article_id"])

        # 添加第二阶段的结果（不重复）
        for hit in fallback_hits:
            if hit["article_id"] not in seen_articles:
                # 标记为来自兜底结果
                hit_with_source = hit.copy()
                hit_with_source["source"] = "fallback"
                merged_hits.append(hit_with_source)
                seen_articles.add(hit["article_id"])

        return merged_hits[:top_k]

    def _process_raw_results(self, raw: list[dict], top_k: int) -> list[dict]:
        """处理原始查询结果"""
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
                by_article[aid] = {
                    "article_id": aid,
                    "score": final,
                    "hit_type": typ,
                    # 添加设备类型信息
                    "device_type_code": meta.get("device_type_code"),
                    "is_common": meta.get("is_common", False)
                }

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
