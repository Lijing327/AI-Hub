"""向量库读写抽象，底层委托给 infra.vectorstore"""
from app.infra.vectorstore.base import IVectorStore


class VectorRepository:
    def __init__(self, store: IVectorStore) -> None:
        self._store = store

    def upsert(self, ids: list[str], embeddings: list[list[float]], documents: list[str], metadatas: list[dict]) -> int:
        return self._store.upsert(ids, embeddings, documents, metadatas)

    def delete_by_article(self, tenant_id: str, article_id: int) -> None:
        self._store.delete_by_article(tenant_id, article_id)

    def clear_collection(self) -> None:
        """清空整个向量集合（全量覆盖前调用）。"""
        self._store.clear_collection()

    def query(self, embedding: list[float], top_k: int, where: dict) -> list[dict]:
        return self._store.query(embedding, top_k, where)


# 兼容旧代码的函数式接口
def _default_store() -> IVectorStore:
    from app.infra.vectorstore.chroma_store import ChromaVectorStore
    return ChromaVectorStore()


def upsert(
    ids: list[str],
    embeddings: list[list[float]],
    metadatas: list[dict] | None = None,
    documents: list[str] | None = None,
    store: IVectorStore | None = None,
) -> None:
    """写入或覆盖一批向量"""
    s = store or _default_store()
    s.upsert(ids=ids, embeddings=embeddings, metadatas=metadatas or [{}] * len(ids), documents=documents or [""] * len(ids))


def query(
    query_embeddings: list[list[float]],
    n_results: int = 10,
    where: dict | None = None,
    store: IVectorStore | None = None,
) -> list[dict]:
    """语义检索，返回 hits：每项含 id / metadata / distance"""
    s = store or _default_store()
    if len(query_embeddings) == 1:
        return s.query(query_embeddings[0], n_results, where or {})
    # 多查询暂不支持
    return []


def delete_by_article_id(tenant_id: str, article_id: int, store: IVectorStore | None = None) -> None:
    """按 article 删旧向量，用于重建单条前清空"""
    s = store or _default_store()
    s.delete_by_article(tenant_id=tenant_id, article_id=article_id)
