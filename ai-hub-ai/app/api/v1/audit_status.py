"""审计状态自检接口：用于排查「域名访问客服无审计记录」"""
import httpx
from fastapi import APIRouter

from app.audit.audit_client import get_audit_client

router = APIRouter(tags=["审计"])


@router.get("/audit-status")
async def audit_status():
    """
    返回当前实例的审计配置与 .NET 连通性，便于排查「域名访问时无审计记录」。
    部署后访问：https://域名:4013/python-api/audit-status
    """
    client = get_audit_client()
    base_url = getattr(client, "_base_url", "") or ""

    # 未启用或未配置 token 时直接返回
    if not getattr(client, "_enabled", True):
        return {
            "audit_enabled": False,
            "reason": "disabled_by_config",
            "message": "ENABLE_AUDIT_LOG 为 false，审计未开启",
            "dotnet_base_url": _redact_url(base_url),
            "dotnet_reachable": None,
        }
    if not getattr(client, "_token", ""):
        return {
            "audit_enabled": False,
            "reason": "token_missing",
            "message": "INTERNAL_TOKEN 未配置，审计不会写入",
            "dotnet_base_url": _redact_url(base_url),
            "dotnet_reachable": None,
        }

    # 检查是否能连上 .NET（只访问根路径，不涉及 internal API）
    dotnet_reachable = None
    try:
        async with httpx.AsyncClient() as http_client:
            r = await http_client.get(base_url, timeout=2.0)
            dotnet_reachable = r.status_code in (200, 302, 404)
    except Exception:
        dotnet_reachable = False

    return {
        "audit_enabled": client.is_enabled,
        "reason": "ok",
        "message": "审计已开启" if client.is_enabled else "审计未开启（请检查 INTERNAL_TOKEN）",
        "dotnet_base_url": _redact_url(base_url),
        "dotnet_reachable": dotnet_reachable,
    }


def _redact_url(url: str) -> str:
    """只保留协议和主机，不暴露端口和路径，便于排查又不过度暴露"""
    if not url:
        return ""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.hostname or parsed.netloc}"
    except Exception:
        return "(无效)"
