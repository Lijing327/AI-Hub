"""
应用配置
环境切换方式：
1. 【推荐】修改下面的 IS_TEST 变量：True=测试环境，False=生产环境
2. 通过 APP_ENV 环境变量：test/production/development
"""
from pathlib import Path
import os

from pydantic_settings import BaseSettings, SettingsConfigDict

# =====================================================
# 【环境切换开关】修改这里来切换环境
# =====================================================
# True = 测试环境（使用 .env.test）
# False = 生产环境（使用 .env.production）
IS_TEST = True
# =====================================================

# 项目根目录：app/core/config.py -> app -> 项目根
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# 环境切换逻辑
APP_ENV = os.getenv("APP_ENV", "").lower()

if APP_ENV == "test":
    _ENV_FILE = str(_PROJECT_ROOT / ".env.test")
elif APP_ENV == "production":
    _ENV_FILE = str(_PROJECT_ROOT / ".env.production")
elif APP_ENV == "development":
    _ENV_FILE = str(_PROJECT_ROOT / ".env")
else:
    # 使用代码开关：IS_TEST 优先
    if IS_TEST:
        _ENV_FILE = str(_PROJECT_ROOT / ".env.test")
        APP_ENV = "test"
    else:
        _ENV_FILE = str(_PROJECT_ROOT / ".env.production")
        APP_ENV = "production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
    )

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

    # 服务端口（与 main.py 中 uvicorn 的 port 一致，用于启动时打开 Swagger）
    PORT: int = 8000

    # 启动时自动打开 Swagger（测试/开发环境建议 true，生产可设 false）
    OPEN_SWAGGER_ON_STARTUP: bool = True

    # JWT 认证（与 .NET 后端保持一致）
    JWT_SECRET: str = "your-super-secret-jwt-key-123456789"
    JWT_ISSUER: str = "ai-hub"
    JWT_AUDIENCE: str = "ai-hub-clients"


settings = Settings()

# 开发/测试环境：附件地址走前端 dev 代理（localhost:3000），由 Vite 转发到 .NET 5000，避免直连 5000 导致地址/跨域不对
if APP_ENV != "production" and getattr(settings, "ATTACHMENT_BASE_URL", None):
    base = settings.ATTACHMENT_BASE_URL
    if base and ("localhost:5000" in base or "127.0.0.1:5000" in base):
        settings.ATTACHMENT_BASE_URL = base.replace("localhost:5000", "localhost:3000").replace("127.0.0.1:5000", "127.0.0.1:3000")
