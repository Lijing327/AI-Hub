"""
应用入口：仅做装配，不包含业务逻辑
- 创建 FastAPI 实例
- 加载配置、初始化日志
- 注册路由、中间件、全局异常处理
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.logging_config import setup_logging as setup_logging_old, get_logger
from app.core.exceptions import AppException
from app.core.middleware import RequestLogMiddleware
from app.api.v1.router import api_router
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

    # 中间件
    app.add_middleware(RequestLogMiddleware)

    # 注册 v1 路由（路径与原先保持一致，包含向量能力闭环）
    app.include_router(api_router)

    @app.on_event("startup")
    async def startup():
        # 检查 DeepSeek 配置状态
        deepseek_client = DeepSeekClient()
        deepseek_status = "已配置" if deepseek_client.is_available else "未配置（需在 .env 中设置 DEEPSEEK_API_KEY）"
        
        logger.info(
            "配置: DOTNET_BASE_URL=%s, DEFAULT_TENANT=%s, ATTACHMENT_BASE_PATH=%s",
            settings.DOTNET_BASE_URL,
            settings.DEFAULT_TENANT,
            settings.ATTACHMENT_BASE_PATH or "(未配置)",
        )
        logger.info(
            "DeepSeek AI 兜底: %s (BaseURL=%s, Model=%s)",
            deepseek_status,
            settings.DEEPSEEK_BASE_URL,
            settings.DEEPSEEK_MODEL,
        )

    return app


# 供 uvicorn 等使用：app.main:app
app = create_app()
