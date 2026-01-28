"""
全局中间件
例如：请求日志、耗时统计、CORS 等（若需在应用内实现）
"""
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging_config import get_logger

logger = get_logger(__name__)


class RequestLogMiddleware(BaseHTTPMiddleware):
    """请求日志中间件：记录请求方法、路径及耗时"""

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        elapsed = time.perf_counter() - start
        logger.info("%s %s -> %d (%.3fs)", request.method, request.url.path, response.status_code, elapsed)
        return response
