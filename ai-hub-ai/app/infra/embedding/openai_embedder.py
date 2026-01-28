"""OpenAI 兼容的 Embedding 实现（批量）"""
from typing import List
from openai import OpenAI
from app.core.config import settings
from app.core.logging_config import get_logger
from app.infra.embedding.base import IEmbedder

logger = get_logger(__name__)


class OpenAIEmbedder(IEmbedder):
    def __init__(self) -> None:
        api_key = settings.OPENAI_API_KEY or settings.EMBEDDING_API_KEY
        if not api_key:
            raise ValueError("OPENAI_API_KEY 未配置，无法使用 openai embedder")
        self._client = OpenAI(api_key=api_key)
        self._model = settings.OPENAI_EMBEDDING_MODEL or settings.EMBEDDING_MODEL

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """OpenAI embeddings 支持批量 input"""
        resp = self._client.embeddings.create(model=self._model, input=texts)
        # 按 index 排序保证顺序
        items = sorted(resp.data, key=lambda x: x.index)
        return [item.embedding for item in items]

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """兼容旧代码的方法名"""
        return self.embed_texts(texts)
