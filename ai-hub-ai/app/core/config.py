"""
应用配置
使用 pydantic-settings 从 .env 加载
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # 基础
    APP_NAME: str = "ai-hub-vector-service"
    APP_ENV: str = "dev"

    # .NET 后端（保留兼容）
    DOTNET_BASE_URL: str = "http://localhost:5000"
    INTERNAL_TOKEN: str = "your-internal-token-change-in-production"
    DEFAULT_TENANT: str = "default"

    # 附件（保留兼容）
    ATTACHMENT_BASE_PATH: str = ""
    ATTACHMENT_BASE_URL: str = "http://localhost:5000/uploads"

    # DeepSeek AI（保留兼容）
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-chat"

    # SQL Server（kb_article 来源）
    SQLSERVER_DSN: str = "Driver={ODBC Driver 17 for SQL Server};Server=localhost;Database=ai_hub;Trusted_Connection=yes;"

    # Chroma（向量库）
    CHROMA_PERSIST_DIR: str = "./data/chroma"
    CHROMA_COLLECTION: str = "kb_articles"

    # Embedding（先用 fake 联调，后切 openai）
    EMBEDDING_PROVIDER: str = "fake"  # fake | openai
    OPENAI_API_KEY: str | None = None
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"

    # 向量相关（保留兼容）
    EMBEDDING_API_KEY: str = ""
    EMBEDDING_BASE_URL: str = "https://api.openai.com/v1"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIM: int = 1536
    CHROMA_PERSIST_PATH: str = "./data/chroma"
    KB_SQLSERVER_CONNECTION_STRING: str = ""


settings = Settings()
