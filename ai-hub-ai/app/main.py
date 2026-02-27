"""
应用入口：仅做装配，不包含业务逻辑
- 创建 FastAPI 实例
- 加载配置、初始化日志
- 注册路由、中间件、全局异常处理
"""
import asyncio
import os
import webbrowser

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings, APP_ENV
from app.core.logging import setup_logging
from app.core.logging_config import setup_logging as setup_logging_old, get_logger
from app.core.exceptions import AppException
from app.core.middleware import RequestLogMiddleware
from app.api.v1.router import api_router
from app.api.chat import router as chat_router
from app.clients.deepseek_client import DeepSeekClient

# 初始化日志（在其它模块使用 logger 前执行）
setup_logging()
logger = get_logger(__name__)


def create_app() -> FastAPI:
    """工厂：创建并配置 FastAPI 应用"""
    app = FastAPI(
        title=settings.APP_NAME or getattr(settings, "APP_TITLE", "AI Hub 服务"),
        description=getattr(settings, "APP_DESCRIPTION", "处理 Excel 文件导入和智能客服问答"),
        version=getattr(settings, "APP_VERSION", "1.0.0"),
        docs_url="/docs",   # Swagger UI
        redoc_url="/redoc",
    )

    # 全局异常处理
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail or exc.message},
        )

    # 跨域：智能客服前端在 4013，请求本服务 6714 会跨域，必须允许
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "https://www.yonghongjituan.com:4013",
            "http://www.yonghongjituan.com:4013",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 中间件
    app.add_middleware(RequestLogMiddleware)

    # 注册 v1 路由：无前缀（智能客服 / 代理转发后为 /api/chat/search、/import/excel）+ 带 /python-api（知识库导入 4013 请求 /python-api/import/excel）
    app.include_router(api_router)
    app.include_router(api_router, prefix="/python-api")
    # 意图分流聊天入口：POST /chat
    app.include_router(chat_router)

    @app.on_event("startup")
    async def startup():
        # 显示当前环境
        env = APP_ENV or "default"
        logger.info("============================================================")
        logger.info("AI-Hub 服务启动 | 当前环境: %s", env)
        logger.info("============================================================")

        # 显示数据库和向量库配置
        db_info = settings.SQLSERVER_DSN
        if "Database=" in db_info:
            db_name = db_info.split("Database=")[1].split(";")[0]
            logger.info("数据库: %s", db_name)
        else:
            logger.info("数据库: (无法解析)")

        logger.info("向量库: %s (collection: %s)", settings.CHROMA_PERSIST_DIR, settings.CHROMA_COLLECTION)

        # 对话 LLM：百炼兼容 或 DeepSeek 直连
        chat_client = DeepSeekClient()
        if chat_client.is_available:
            if getattr(chat_client, "_use_dashscope", False):
                logger.info(
                    "对话 LLM（百炼兼容）: 已配置 BaseURL=%s, Model=%s",
                    settings.LLM_BASE_URL,
                    settings.LLM_MODEL,
                )
            else:
                logger.info(
                    "对话 LLM（DeepSeek 直连）: 已配置 BaseURL=%s, Model=%s",
                    settings.DEEPSEEK_BASE_URL,
                    settings.DEEPSEEK_MODEL,
                )
        else:
            logger.info(
                "对话 LLM: 未配置（百炼: LLM_BASE_URL+LLM_MODEL+DASHSCOPE_API_KEY；或 DEEPSEEK_API_KEY）"
            )
        logger.info(
            "配置: DOTNET_BASE_URL=%s, DEFAULT_TENANT=%s, ATTACHMENT_BASE_PATH=%s, ATTACHMENT_BASE_URL=%s, ATTACHMENT_FILES_API_BASE_URL=%s",
            settings.DOTNET_BASE_URL,
            settings.DEFAULT_TENANT,
            settings.ATTACHMENT_BASE_PATH or "(未配置)",
            settings.ATTACHMENT_BASE_URL or "(未配置)",
            settings.ATTACHMENT_FILES_API_BASE_URL or "(未配置)",
        )
        logger.info("============================================================")

        # 启动时自动打开 Swagger（可通过 OPEN_SWAGGER_ON_STARTUP=false 关闭）
        if getattr(settings, "OPEN_SWAGGER_ON_STARTUP", True):
            port = int(os.getenv("PORT", str(getattr(settings, "PORT", 8000))))
            swagger_url = f"http://127.0.0.1:{port}/docs"

            async def _open_swagger():
                await asyncio.sleep(1)
                try:
                    webbrowser.open(swagger_url)
                    logger.info("已自动打开 Swagger: %s", swagger_url)
                except Exception as e:
                    logger.warning("自动打开 Swagger 失败: %s，请手动访问 %s", e, swagger_url)

            asyncio.create_task(_open_swagger())

    return app


# 供 uvicorn 等使用：app.main:app
app = create_app()
