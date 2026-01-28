"""Embedding 接口，便于替换为本地模型 / 其他厂商"""
from abc import ABC, abstractmethod


class IEmbedder(ABC):
    @abstractmethod
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """批量生成向量"""
        raise NotImplementedError
