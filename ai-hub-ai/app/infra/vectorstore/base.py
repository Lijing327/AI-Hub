"""向量库接口，便于替换为 Milvus / PG 等"""
from abc import ABC, abstractmethod


class IVectorStore(ABC):
    @abstractmethod
    def upsert(self, ids: list[str], embeddings: list[list[float]], documents: list[str], metadatas: list[dict]) -> int:
        raise NotImplementedError

    @abstractmethod
    def delete_by_article(self, tenant_id: str, article_id: int) -> None:
        raise NotImplementedError

    @abstractmethod
    def query(self, embedding: list[float], top_k: int, where: dict) -> list[dict]:
        """
        返回结构统一成：
        [
          {"id": "...", "score": 0.12, "metadata": {...}}
        ]
        """
        raise NotImplementedError

    def clear_collection(self) -> None:
        """清空当前集合（全量重建前使用）。未实现的 store 会抛 NotImplementedError。"""
        raise NotImplementedError("clear_collection not supported")
