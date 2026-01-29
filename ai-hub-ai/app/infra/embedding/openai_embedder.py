"""OpenAI 兼容的 Embedding 实现（批量），支持 OpenAI / DeepSeek / 阿里百炼 DashScope"""
from typing import List
from openai import OpenAI
from app.core.config import settings
from app.core.logging_config import get_logger
from app.infra.embedding.base import IEmbedder

logger = get_logger(__name__)


def _embedder_api_key() -> str:
    """优先 OPENAI_API_KEY / EMBEDDING_API_KEY；base_url 为 DeepSeek 时可用 DEEPSEEK_API_KEY，为 DashScope 时可用 DASHSCOPE_API_KEY"""
    key = settings.OPENAI_API_KEY or settings.EMBEDDING_API_KEY
    if key:
        return key
    base = (settings.OPENAI_BASE_URL or settings.EMBEDDING_BASE_URL or "").strip().lower()
    if "deepseek" in base and settings.DEEPSEEK_API_KEY:
        return settings.DEEPSEEK_API_KEY
    if "dashscope" in base and settings.DASHSCOPE_API_KEY:
        return settings.DASHSCOPE_API_KEY
    return ""


def _embedder_base_url() -> str | None:
    """OPENAI_BASE_URL 或 EMBEDDING_BASE_URL"""
    return settings.OPENAI_BASE_URL or settings.EMBEDDING_BASE_URL or None


def _embedder_extra_kwargs() -> dict:
    """百炼 text-embedding-v3/v4 支持 dimensions、encoding_format"""
    extra: dict = {}
    if settings.OPENAI_EMBEDDING_DIMENSIONS is not None:
        extra["dimensions"] = settings.OPENAI_EMBEDDING_DIMENSIONS
    base = (_embedder_base_url() or "").lower()
    if "dashscope" in base:
        extra.setdefault("encoding_format", "float")
    return extra


class OpenAIEmbedder(IEmbedder):
    def __init__(self) -> None:
        api_key = _embedder_api_key()
        if not api_key:
            raise ValueError(
                "未配置 Embedding API Key。请设置 OPENAI_API_KEY / EMBEDDING_API_KEY；"
                "或 DeepSeek: OPENAI_BASE_URL=https://api.deepseek.com/v1 + DEEPSEEK_API_KEY；"
                "或百炼: OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1 + DASHSCOPE_API_KEY"
            )
        base_url = _embedder_base_url()
        if base_url:
            self._client = OpenAI(api_key=api_key, base_url=base_url.rstrip("/"))
            logger.info("Embedding 使用兼容接口: base_url=%s", base_url)
        else:
            self._client = OpenAI(api_key=api_key)
        self._model = settings.OPENAI_EMBEDDING_MODEL or settings.EMBEDDING_MODEL
        self._extra = _embedder_extra_kwargs()

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """OpenAI 兼容 embeddings，支持批量 input；百炼 v3/v4 可传 dimensions"""
        kwargs: dict = {"model": self._model, "input": texts, **self._extra}
        resp = self._client.embeddings.create(**kwargs)
        items = sorted(resp.data, key=lambda x: x.index)
        return [item.embedding for item in items]

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """兼容旧代码的方法名"""
        return self.embed_texts(texts)
