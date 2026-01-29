"""读 SQL → 拆分 → embedding → upsert"""
import logging
from app.core.exceptions import AppError
from app.repositories.kb_article_repo import KbArticleRepository
from app.repositories.vector_repo import VectorRepository
from app.infra.embedding.base import IEmbedder
from app.services.chunker import build_chunks

logger = logging.getLogger(__name__)


class IngestService:
    def __init__(self, kb_repo: KbArticleRepository, vec_repo: VectorRepository, embedder: IEmbedder) -> None:
        self._kb_repo = kb_repo
        self._vec_repo = vec_repo
        self._embedder = embedder

    def rebuild_article(self, article_id: int) -> int:
        """重建单条向量：删旧 → 重新拆分 → 重新写入"""
        article = self._kb_repo.get_by_id(article_id)
        if not article:
            raise AppError(f"kb_article 不存在: {article_id}")

        # 先删旧，再写新
        self._vec_repo.delete_by_article(article.tenant_id, article.id)

        chunks = build_chunks(article)
        if not chunks:
            return 0

        docs = [c["doc"] for c in chunks]
        vecs = self._embedder.embed_texts(docs)

        ids = [c["id"] for c in chunks]
        metas = [c["metadata"] for c in chunks]

        return self._vec_repo.upsert(ids=ids, embeddings=vecs, documents=docs, metadatas=metas)

    def rebuild_batch(self, ids: list[int], log_every: int = 50) -> dict:
        """
        批量重建：返回统计信息（成功/失败）
        """
        total = len(ids)
        success = 0
        failed: list[dict] = []
        upserted_total = 0

        for i, aid in enumerate(ids, start=1):
            try:
                upserted = self.rebuild_article(aid)
                upserted_total += upserted
                success += 1
            except Exception as e:
                failed.append({"article_id": aid, "error": str(e)})

            if log_every > 0 and i % log_every == 0:
                logger.info(f"批量 ingest 进度: {i}/{total}, success={success}, failed={len(failed)}, upserted_total={upserted_total}")

        logger.info(f"批量 ingest 完成: total={total}, success={success}, failed={len(failed)}, upserted_total={upserted_total}")
        return {
            "total": total,
            "success": success,
            "failed": failed,
            "upserted_total": upserted_total,
        }

    def count_articles(self, tenant_id: str, status: str | None = None) -> int:
        """统计库中符合条件的 article 数量（调试用）"""
        return self._kb_repo.count_ids(tenant_id=tenant_id, status=status)

    def rebuild_all(self, tenant_id: str, status: str | None = None, limit: int | None = None) -> dict:
        """
        全量重建：先从 SQL 拉取 id 列表，再走 batch
        """
        ids = self._kb_repo.list_ids(tenant_id=tenant_id, status=status, limit=limit)
        if not ids:
            return {"total": 0, "success": 0, "failed": [], "upserted_total": 0}
        return self.rebuild_batch(ids, log_every=100)


# 兼容旧代码的函数式接口
from typing import Optional, List
from app.repositories import kb_article_repo, vector_repo
from app.services.chunker import chunk_article, ChunkItem
from app.utils.ids import vector_id
from app.utils.text import truncate
from app.infra.embedding.openai_embedder import OpenAIEmbedder
from app.core.logging_config import get_logger

logger = get_logger(__name__)


def ingest_article(article_id: int, tenant_id: str) -> int:
    """重建单条向量：删旧（按 article_id）→ 重新拆分 → 重新写入"""
    article = kb_article_repo.get_article(article_id, tenant_id)
    if not article:
        logger.warning("article not found: id=%s tenant=%s", article_id, tenant_id)
        return 0

    vector_repo.delete_by_article_id(tenant_id=tenant_id, article_id=article_id)

    items = chunk_article(
        article_id=article.id,
        tenant_id=article.tenant_id,
        title=article.title or "",
        question_text=article.question_text,
        cause_text=article.cause_text,
    )
    if not items:
        return 0

    texts = [truncate(it.text) for it in items]
    embedder = OpenAIEmbedder()
    embeddings = embedder.embed_batch(texts)

    ids = [vector_id(it.tenant_id, it.article_id, it.hit_type) for it in items]
    metadatas = [
        {
            "tenant_id": it.tenant_id,
            "article_id": it.article_id,
            "type": it.hit_type,
            "status": getattr(article, "status", "published"),
            "version": getattr(article, "version", 1),
            "tags": (article.tags or "")[:500],
        }
        for it in items
    ]
    documents = [it.text for it in items]

    vector_repo.upsert(ids=ids, embeddings=embeddings, metadatas=metadatas, documents=documents)
    return len(ids)


def ingest_batch(
    tenant_id: str,
    ids: Optional[List[int]] = None,
    updated_after: Optional[str] = None,
) -> int:
    """批量重建：用于后台按钮"""
    articles = kb_article_repo.list_articles(tenant_id=tenant_id, ids=ids, updated_after=updated_after)
    total = 0
    for a in articles:
        n = ingest_article(a.id, tenant_id)
        total += n
    logger.info("ingest_batch tenant=%s count=%s vectors=%s", tenant_id, len(articles), total)
    return total
