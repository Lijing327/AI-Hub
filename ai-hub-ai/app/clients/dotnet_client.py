"""
.NET 后端 API 客户端
封装对 ai-hub-service 的 HTTP 调用
"""
from typing import List, Dict, Any, Optional
import httpx

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class DotnetClient:
    """调用 .NET 后端接口的客户端"""

    def __init__(
        self,
        base_url: Optional[str] = None,
        tenant_id: Optional[str] = None,
        internal_token: Optional[str] = None,
        timeout: float = 30.0,
    ):
        self.base_url = (base_url or settings.DOTNET_BASE_URL).rstrip("/")
        self.tenant_id = tenant_id or settings.DEFAULT_TENANT
        self.internal_token = internal_token or settings.INTERNAL_TOKEN
        self.timeout = timeout

    def _headers(self, use_internal_token: bool = False, user_id: Optional[str] = None) -> Dict[str, str]:
        """请求头：租户 ID 必带，内部接口需带 Internal-Token，用户认证接口需带 Bearer token"""
        h = {
            "Content-Type": "application/json",
            "X-Tenant-Id": self.tenant_id,
        }
        if use_internal_token:
            h["X-Internal-Token"] = self.internal_token
        if user_id:
            # 如果是JWT token格式，添加Bearer前缀
            if user_id.startswith("jwt_"):
                h["Authorization"] = f"Bearer {user_id[4:]}"
            else:
                h["X-User-ID"] = user_id
        return h

    async def batch_create_articles(self, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        批量创建知识条目（草稿）
        POST /api/ai/kb/articles/batch
        """
        url = f"{self.base_url}/api/ai/kb/articles/batch"
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json={"articles": articles},
                headers=self._headers(use_internal_token=True),
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()

    async def batch_create_assets(self, assets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        批量创建附件记录
        POST /api/ai/kb/articles/assets/batch
        """
        url = f"{self.base_url}/api/ai/kb/articles/assets/batch"
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json={"assets": assets},
                headers=self._headers(use_internal_token=True),
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()

    async def search_knowledge(
        self,
        keyword: str,
        page_index: int = 1,
        page_size: int = 10,
        status: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        搜索知识条目
        GET /api/knowledgeitems/search
        """
        url = f"{self.base_url}/api/knowledgeitems/search"
        params: Dict[str, Any] = {
            "keyword": keyword,
            "pageIndex": page_index,
            "pageSize": page_size,
        }
        if status is not None:
            params["status"] = status
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                params=params,
                headers=self._headers(use_internal_token=False, user_id=user_id),
                timeout=10.0,
            )
            response.raise_for_status()
            return response.json()
