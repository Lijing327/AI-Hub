"""
统一异常定义
便于在异常处理中间件中区分业务异常与系统异常
"""
from typing import Any, Optional


class AppError(Exception):
    """业务异常基类"""
    pass


class AppException(Exception):
    """应用层基础异常（兼容旧代码）"""

    def __init__(
        self,
        message: str = "应用异常",
        status_code: int = 500,
        detail: Optional[Any] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.detail = detail
        super().__init__(self.message)


class ExternalServiceError(AppException):
    """外部服务（如 .NET 后端）调用失败"""

    def __init__(self, message: str = "外部服务调用失败", detail: Optional[Any] = None):
        super().__init__(message=message, status_code=503, detail=detail)


class ValidationError(AppException):
    """参数或业务校验失败"""

    def __init__(self, message: str = "校验失败", detail: Optional[Any] = None):
        super().__init__(message=message, status_code=400, detail=detail)
