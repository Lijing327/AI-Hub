"""从 SQL Server 读 kb_article 和 kb_asset，不直接写 SQL 在 service 里"""
from typing import Optional, List, Dict, Any
from app.infra.db.sqlserver import SqlServer, execute_query
from app.schemas.kb_article import KbArticle
from app.core.logging_config import get_logger

logger = get_logger(__name__)


def get_assets_by_article_id(article_id: int) -> List[Dict[str, Any]]:
    """
    获取知识条目的附件列表
    返回格式：[{"id": 1, "name": "xxx.mp4", "type": "video", "url": "...", "size": 1024, "duration": 60}]
    """
    sql = """
    SELECT id, file_name, asset_type, url, size, duration
    FROM dbo.kb_asset
    WHERE article_id = ? AND deleted_at IS NULL
    ORDER BY id ASC
    """
    rows = execute_query(sql, (article_id,))
    assets = []
    for r in rows:
        # 映射 asset_type 到前端友好的类型
        asset_type = r.get("asset_type", "other") or "other"
        if asset_type in ("image", "video", "document", "pdf"):
            display_type = asset_type
        elif asset_type in ("jpg", "jpeg", "png", "gif", "webp"):
            display_type = "image"
        elif asset_type in ("mp4", "avi", "mov", "wmv"):
            display_type = "video"
        elif asset_type in ("doc", "docx", "pdf", "xls", "xlsx"):
            display_type = "document"
        else:
            display_type = "other"
        
        assets.append({
            "id": r.get("id"),
            "name": r.get("file_name") or "",
            "type": display_type,
            "url": r.get("url") or "",
            "size": r.get("size"),
            "duration": r.get("duration"),
        })
    return assets


class KbArticleRepository:
    def __init__(self, db: SqlServer) -> None:
        self._db = db

    def get_by_id(self, article_id: int) -> KbArticle | None:
        """按 id 取单条"""
        sql = """
        SELECT
            id, tenant_id, title, question_text, cause_text, solution_text, tags, status, version
        FROM dbo.kb_article
        WHERE id = ? AND deleted_at IS NULL
        """
        row = self._db.fetch_one(sql, (article_id,))
        if not row:
            return None
        return KbArticle(**row)

    def count_ids(self, tenant_id: str, status: str | None = None) -> int:
        """
        统计符合条件的 article 数量（用于调试：确认库中是否有数据）
        """
        if status:
            sql = """
            SELECT COUNT(*) AS cnt FROM dbo.kb_article
            WHERE tenant_id = ? AND status = ? AND deleted_at IS NULL
            """
            row = self._db.fetch_one(sql, (tenant_id, status))
        else:
            sql = """
            SELECT COUNT(*) AS cnt FROM dbo.kb_article
            WHERE tenant_id = ? AND deleted_at IS NULL
            """
            row = self._db.fetch_one(sql, (tenant_id,))
        if not row:
            return 0
        return int(row.get("cnt", 0) or 0)

    def list_ids(self, tenant_id: str, status: str | None = None, limit: int | None = None) -> list[int]:
        """
        拉取 article id 列表（用于全量 ingest）
        status 如果传入（比如 'published'），会过滤
        limit 用于安全限制（开发阶段）
        """
        logger.info(
            "list_ids 调用: tenant_id=%r, status=%r, limit=%s",
            tenant_id, status, limit,
        )
        top = f"TOP ({limit})" if limit and limit > 0 else ""
        if status:
            sql = f"""
            SELECT {top} id
            FROM dbo.kb_article
            WHERE tenant_id = ? AND status = ? AND deleted_at IS NULL
            ORDER BY id ASC
            """
            rows = self._db.fetch_all(sql, (tenant_id, status))
        else:
            sql = f"""
            SELECT {top} id
            FROM dbo.kb_article
            WHERE tenant_id = ? AND deleted_at IS NULL
            ORDER BY id ASC
            """
            rows = self._db.fetch_all(sql, (tenant_id,))
        ids = [int(r["id"]) for r in rows]
        logger.info("list_ids 返回: %d 条 (tenant_id=%r)", len(ids), tenant_id)
        return ids


# 兼容旧代码的函数式接口
def get_article(article_id: int, tenant_id: Optional[str] = None) -> Optional[KbArticle]:
    """按 id 取单条，可选按 tenant_id 过滤"""
    if tenant_id:
        rows = execute_query(
            "SELECT id, tenant_id, title, question_text, cause_text, solution_text, tags, status, version "
            "FROM kb_article WHERE id = ? AND tenant_id = ? AND deleted_at IS NULL",
            (article_id, tenant_id),
        )
    else:
        rows = execute_query(
            "SELECT id, tenant_id, title, question_text, cause_text, solution_text, tags, status, version "
            "FROM kb_article WHERE id = ? AND deleted_at IS NULL",
            (article_id,),
        )
    if not rows:
        return None
    r = rows[0]
    return KbArticle(
        id=r["id"],
        tenant_id=r["tenant_id"] or "default",
        title=r.get("title"),
        question_text=r.get("question_text"),
        cause_text=r.get("cause_text"),
        solution_text=r.get("solution_text"),
        tags=r.get("tags"),
        status=r.get("status") or 1,
        version=int(r.get("version") or 1),
    )


def list_articles(
    tenant_id: str,
    ids: Optional[List[int]] = None,
    updated_after: Optional[str] = None,
) -> List[KbArticle]:
    """列表：按 tenant_id，可选 ids 或 updated_after（ISO 时间串）"""
    if ids:
        placeholders = ",".join("?" * len(ids))
        sql = (
            "SELECT id, tenant_id, title, question_text, cause_text, solution_text, tags, status, version "
            "FROM kb_article WHERE tenant_id = ? AND id IN ({}) AND deleted_at IS NULL"
        ).format(placeholders)
        params: tuple = (tenant_id, *ids)
    elif updated_after:
        sql = (
            "SELECT id, tenant_id, title, question_text, cause_text, solution_text, tags, status, version "
            "FROM kb_article WHERE tenant_id = ? AND (updated_at >= ? OR created_at >= ?) AND deleted_at IS NULL"
        )
        params = (tenant_id, updated_after, updated_after)
    else:
        sql = (
            "SELECT id, tenant_id, title, question_text, cause_text, solution_text, tags, status, version "
            "FROM kb_article WHERE tenant_id = ? AND deleted_at IS NULL"
        )
        params = (tenant_id,)
    rows = execute_query(sql, params)
    return [
        KbArticle(
            id=r["id"],
            tenant_id=r["tenant_id"] or "default",
            title=r.get("title"),
            question_text=r.get("question_text"),
            cause_text=r.get("cause_text"),
            solution_text=r.get("solution_text"),
            tags=r.get("tags"),
            status=r.get("status") or 1,
            version=int(r.get("version") or 1),
        )
        for r in rows
    ]
