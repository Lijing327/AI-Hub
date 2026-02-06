"""
应用配置
使用 pydantic-settings 从 .env 加载；
当 APP_ENV=production 时自动加载 .env.production（部署时设置环境变量即可）。
"""
import os
from pydantic_settings import BaseSettings, SettingsConfigDict

# 生产环境加载 .env.production，否则加载 .env（部署时设置 APP_ENV=production）
_env_file = ".env.production" if os.getenv("APP_ENV") == "production" else ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_env_file, env_file_encoding="utf-8")

    # 基础
    APP_NAME: str = "ai-hub-vector-service"
    APP_ENV: str = "dev"

    # .NET 后端（保留兼容）
    DOTNET_BASE_URL: str = "http://localhost:5000"
    INTERNAL_TOKEN: str = "your-internal-token-change-in-production"
    DEFAULT_TENANT: str = "default"

    # 附件（本地目录，开发用）
    ATTACHMENT_BASE_PATH: str = ""
    ATTACHMENT_BASE_URL: str = "http://localhost:5000/uploads"
    # 服务器附件 API（生产用，与本地二选一）：列表接口 + 远程路径
    ATTACHMENT_FILES_API_BASE_URL: str = ""  # 如 https://www.yonghongjituan.com:4023
    ATTACHMENT_REMOTE_PATH: str = ""         # 如 diyi/永红造型线维修视频

    # DeepSeek AI（保留兼容）
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-chat"

    # 对话 LLM 可选走百炼兼容（与上面示例一致：base_url + model + DASHSCOPE_API_KEY）
    # 配置后 chat 将用 openai 库请求该 base_url，不再用 DEEPSEEK_* 直连
    LLM_BASE_URL: str | None = None  # 如 https://dashscope.aliyuncs.com/compatible-mode/v1
    LLM_MODEL: str | None = None     # 如 deepseek-v3.2 或 qwen-plus
    LLM_API_KEY: str | None = None   # 不填则用 DASHSCOPE_API_KEY

    # SQL Server（kb_article 来源）
    SQLSERVER_DSN: str = "Driver={ODBC Driver 17 for SQL Server};Server=localhost;Database=ai_hub;Trusted_Connection=yes;"

    # Chroma（向量库）
    CHROMA_PERSIST_DIR: str = "./data/chroma"
    CHROMA_COLLECTION: str = "kb_articles"

    # Embedding（fake 联调 | openai 语义向量；支持 OpenAI / DeepSeek / 阿里百炼 DashScope）
    EMBEDDING_PROVIDER: str = "fake"  # fake | openai
    OPENAI_API_KEY: str | None = None
    OPENAI_BASE_URL: str | None = None  # DeepSeek: https://api.deepseek.com/v1；百炼: https://dashscope.aliyuncs.com/compatible-mode/v1
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"  # DeepSeek: deepseek-embedding-v2；百炼: text-embedding-v3
    OPENAI_EMBEDDING_DIMENSIONS: int | None = None  # 百炼 v3/v4 可选：1024,768,512,256,128,64，不填则用模型默认

    # 阿里百炼 DashScope（embedding 用 OpenAI 兼容接口时可用 DASHSCOPE_API_KEY）
    DASHSCOPE_API_KEY: str = ""

    # 向量相关（保留兼容）
    EMBEDDING_API_KEY: str = ""
    EMBEDDING_BASE_URL: str = "https://api.openai.com/v1"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIM: int = 1536
    CHROMA_PERSIST_PATH: str = "./data/chroma"
    KB_SQLSERVER_CONNECTION_STRING: str = ""

    # 审计日志（调用 .NET internal API 记录对话全链路）
    ENABLE_AUDIT_LOG: bool = True


settings = Settings()
