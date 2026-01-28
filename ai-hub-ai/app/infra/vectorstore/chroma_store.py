"""Chroma 向量库实现"""
import chromadb
from app.core.config import settings
from app.core.logging_config import get_logger
from app.infra.vectorstore.base import IVectorStore

logger = get_logger(__name__)


class ChromaVectorStore(IVectorStore):
    def __init__(self) -> None:
        persist_dir = settings.CHROMA_PERSIST_DIR or settings.CHROMA_PERSIST_PATH or "./data/chroma"
        collection_name = settings.CHROMA_COLLECTION or "kb_articles"
        self._client = chromadb.PersistentClient(path=persist_dir)
        self._col = self._client.get_or_create_collection(name=collection_name)

    def upsert(self, ids: list[str], embeddings: list[list[float]], documents: list[str], metadatas: list[dict]) -> int:
        self._col.upsert(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)
        logger.info("Chroma upsert %d 条", len(ids))
        return len(ids)

    def delete_by_article(self, tenant_id: str, article_id: int) -> None:
        """用 where 过滤删除（依赖你写入时 metadata 带 article_id）"""
        try:
            self._col.delete(where={"tenant_id": tenant_id, "article_id": article_id})
            logger.info("Chroma 按 article_id 删除 tenant=%s id=%s", tenant_id, article_id)
        except Exception as e:
            logger.debug("Chroma delete_by_article 可能无匹配: %s", e)

    def query(self, embedding: list[float], top_k: int, where: dict) -> list[dict]:
        res = self._col.query(
            query_embeddings=[embedding],
            n_results=top_k,
            where=where,
            include=["metadatas", "distances", "ids"],
        )
        # Chroma distances：越小越相近（默认）
        ids = res.get("ids", [[]])[0]
        dists = res.get("distances", [[]])[0]
        metas = res.get("metadatas", [[]])[0]

        out: list[dict] = []
        for _id, d, m in zip(ids, dists, metas):
            out.append({"id": _id, "score": float(d), "metadata": m or {}})
        return out
