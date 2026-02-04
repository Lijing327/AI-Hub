"""
应用入口：仅做装配，不包含业务逻辑
- 创建 FastAPI 实例
- 加载配置、初始化日志
- 注册路由、中间件、全局异常处理
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
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

    # 注册 v1 路由（路径与原先保持一致，包含向量能力闭环）
    app.include_router(api_router)
    # 意图分流聊天入口：POST /chat
    app.include_router(chat_router)

    @app.on_event("startup")
    async def startup():
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
            "配置: DOTNET_BASE_URL=%s, DEFAULT_TENANT=%s, ATTACHMENT_BASE_PATH=%s",
            settings.DOTNET_BASE_URL,
            settings.DEFAULT_TENANT,
            settings.ATTACHMENT_BASE_PATH or "(未配置)",
        )

    return app


# 供 uvicorn 等使用：app.main:app
app = create_app()
