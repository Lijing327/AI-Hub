"""Chroma 向量库实现"""
import chromadb
from app.core.config import settings
from app.core.logging_config import get_logger
from app.infra.vectorstore.base import IVectorStore

logger = get_logger(__name__)


class ChromaVectorStore(IVectorStore):
    def __init__(self) -> None:
        persist_dir = settings.CHROMA_PERSIST_DIR or settings.CHROMA_PERSIST_PATH or "./data/chroma"
        self._collection_name = settings.CHROMA_COLLECTION or "kb_articles"
        self._client = chromadb.PersistentClient(path=persist_dir)
        self._col = self._client.get_or_create_collection(name=self._collection_name)

    def _recreate_collection(self) -> None:
        """删除当前集合并重新创建（用于切换 embedding 维度后）"""
        try:
            self._client.delete_collection(name=self._collection_name)
            logger.info("Chroma 已删除旧集合: %s（维度已变更，将重建）", self._collection_name)
        except Exception as e:
            logger.debug("删除集合时忽略: %s", e)
        self._col = self._client.get_or_create_collection(name=self._collection_name)

    def clear_collection(self) -> None:
        """清空向量库（删集合并重建），用于全量覆盖前先去掉旧 article_id。"""
        try:
            self._client.delete_collection(name=self._collection_name)
            logger.info("Chroma 已清空集合: %s（全量重建前）", self._collection_name)
        except Exception as e:
            logger.debug("清空集合时忽略: %s", e)
        self._col = self._client.get_or_create_collection(name=self._collection_name)

    def upsert(self, ids: list[str], embeddings: list[list[float]], documents: list[str], metadatas: list[dict]) -> int:
        try:
            self._col.upsert(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)
        except Exception as e:
            err_msg = str(e).lower()
            # 维度与集合不一致（如从 fake 64 维切到百炼 1024 维）：删集合重建后重试一次
            # 兼容两种报错: "does not match" 或 "expecting ... dimension ... got"
            is_dimension_mismatch = (
                "dimension" in err_msg
                and ("match" in err_msg or "expecting" in err_msg or " got " in err_msg)
            )
            if is_dimension_mismatch:
                logger.warning("Chroma 维度不一致，重建集合后重试: %s", e)
                self._recreate_collection()
                self._col.upsert(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)
            else:
                raise
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
        # 新版 Chroma 的 include 只支持: documents, embeddings, metadatas, distances, uris, data（不含 ids）
        res = self._col.query(
            query_embeddings=[embedding],
            n_results=top_k,
            where=where,
            include=["metadatas", "distances"],
        )
        # Chroma distances：越小越相近（默认）
        ids = res.get("ids", [[]])
        ids_list = ids[0] if ids else []
        dists = res.get("distances", [[]])[0]
        metas = res.get("metadatas", [[]])[0]

        out: list[dict] = []
        for i, (d, m) in enumerate(zip(dists, metas)):
            meta = m or {}
            # 若返回里没有 ids，用 metadata 拼出唯一标识
            _id = ids_list[i] if i < len(ids_list) else _reconstruct_id(meta)
            out.append({"id": _id, "score": float(d), "metadata": meta})
        return out


def _reconstruct_id(meta: dict) -> str:
    """用 metadata 拼出与写入时一致的 vector id"""
    t = meta.get("tenant_id") or "default"
    aid = meta.get("article_id") or 0
    typ = meta.get("type") or "q"
    return f"{t}:kb:{aid}:{typ}"
