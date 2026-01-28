"""依赖注入：统一管理服务实例"""
from functools import lru_cache

from app.core.config import settings
from app.infra.db.sqlserver import SqlServer
from app.infra.embedding.fake_embedder import FakeEmbedder
from app.infra.embedding.openai_embedder import OpenAIEmbedder
from app.infra.vectorstore.chroma_store import ChromaVectorStore
from app.repositories.kb_article_repo import KbArticleRepository
from app.repositories.vector_repo import VectorRepository
from app.services.ingest_service import IngestService
from app.services.query_service import QueryService


@lru_cache
def get_db() -> SqlServer:
    return SqlServer()


@lru_cache
def get_vector_store() -> ChromaVectorStore:
    return ChromaVectorStore()


@lru_cache
def get_embedder():
    if settings.EMBEDDING_PROVIDER == "openai":
        return OpenAIEmbedder()
    return FakeEmbedder()


@lru_cache
def get_kb_repo() -> KbArticleRepository:
    return KbArticleRepository(get_db())


@lru_cache
def get_vec_repo() -> VectorRepository:
    return VectorRepository(get_vector_store())


@lru_cache
def get_ingest_service() -> IngestService:
    return IngestService(get_kb_repo(), get_vec_repo(), get_embedder())


@lru_cache
def get_query_service() -> QueryService:
    return QueryService(get_vec_repo(), get_embedder())
