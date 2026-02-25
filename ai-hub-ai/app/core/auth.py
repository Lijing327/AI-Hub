"""认证相关功能 - JWT Token 验证"""
import jwt
from jwt.exceptions import PyJWTError
from fastapi import Request, HTTPException, status, Depends
from typing import Optional
from functools import lru_cache

from app.core.config import settings


class JWTSettings:
    """JWT 配置类 - 与 .NET 后端保持一致"""
    # 从配置文件读取，如果未配置则使用默认值（必须与 .NET 后端的 Jwt 配置一致）
    SECRET = getattr(settings, 'JWT_SECRET', None) or "your-super-secret-jwt-key-123456789"
    ISSUER = getattr(settings, 'JWT_ISSUER', None) or "ai-hub"
    AUDIENCE = getattr(settings, 'JWT_AUDIENCE', None) or "ai-hub-clients"


@lru_cache
def get_jwt_settings() -> JWTSettings:
    """获取 JWT 配置（单例缓存）"""
    return JWTSettings()


def verify_jwt_token(token: str, jwt_settings: Optional[JWTSettings] = None) -> Optional[dict]:
    """
    验证 JWT token 并解析 payload

    Args:
        token: JWT token 字符串
        jwt_settings: JWT 配置，不传则使用默认配置

    Returns:
        解析后的 payload dict，如果验证失败则返回 None
    """
    if jwt_settings is None:
        jwt_settings = get_jwt_settings()

    try:
        # 解析并验证 JWT token
        payload = jwt.decode(
            token,
            jwt_settings.SECRET,
            algorithms=["HS256"],
            issuer=jwt_settings.ISSUER,
            audience=jwt_settings.AUDIENCE,
            options={"verify_exp": True}
        )
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except PyJWTError:
        return None


async def get_current_user(request: Request) -> Optional[str]:
    """
    从请求中获取当前用户 ID
    1. 优先从 Authorization: Bearer <token> 中获取
    2. 如果没有 token，尝试从 X-User-ID 头获取

    Returns:
        用户 ID，如果没有认证则返回 None
    """
    # 从 Authorization 头获取 JWT token
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]

        # 验证并解析 token
        payload = verify_jwt_token(token)
        if payload:
            # .NET 后端 ClaimTypes.NameIdentifier 映射为 sub
            # 同时尝试多种可能的 claim 名称
            return (payload.get("sub") or
                    payload.get("user_id") or
                    payload.get("nameid") or
                    payload.get("http://schemas.xmlsoap.org/ws/2005/05/identity/claims/nameidentifier"))

    # 从 X-User-ID 头获取用户 ID（兼容旧的实现）
    user_id = request.headers.get("X-User-ID")
    if user_id:
        return user_id

    return None


async def get_current_user_payload(request: Request) -> Optional[dict]:
    """
    从请求中获取当前用户的完整 payload 信息

    Returns:
        用户 payload dict，包含 user_id, phone 等信息，如果没有认证则返回 None
    """
    # 从 Authorization 头获取 JWT token
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]

        # 验证并解析 token
        payload = verify_jwt_token(token)
        if payload:
            return payload

    return None


async def require_auth(request: Request) -> str:
    """
    要求必须认证，否则抛出 401 错误

    Returns:
        用户 ID

    Raises:
        HTTPException: 401 未授权
    """
    user_id = await get_current_user(request)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="需要认证",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return user_id


async def get_current_user_id(request: Request) -> str:
    """
    依赖注入：获取当前用户 ID，必须认证

    用法：
        @app.get("/protected")
        async def protected_route(user_id: str = Depends(get_current_user_id)):
            return {"user_id": user_id}
    """
    return await require_auth(request)


async def get_current_user_info(request: Request) -> dict:
    """
    依赖注入：获取当前用户完整信息，必须认证

    用法：
        @app.get("/protected")
        async def protected_route(user_info: dict = Depends(get_current_user_info)):
            return {"user_id": user_info.get("sub"), "phone": user_info.get("phone")}
    """
    payload = await get_current_user_payload(request)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="需要认证",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return payload
