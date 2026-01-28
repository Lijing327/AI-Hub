"""SQL Server 连接与执行"""
import pyodbc
from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class SqlServer:
    def __init__(self) -> None:
        # 优先用新配置，兼容旧配置
        self._dsn = settings.SQLSERVER_DSN or settings.KB_SQLSERVER_CONNECTION_STRING or ""

    def fetch_one(self, sql: str, params: tuple) -> dict | None:
        """执行查询，返回单行 dict 或 None"""
        try:
            with pyodbc.connect(self._dsn) as conn:
                conn.setencoding(encoding="utf-8")
                cursor = conn.cursor()
                row = cursor.execute(sql, params).fetchone()
                if not row:
                    return None
                columns = [c[0] for c in cursor.description]
                return dict(zip(columns, row))
        except Exception as e:
            logger.warning("SQL Server 查询失败: %s", e)
            raise

    def fetch_all(self, sql: str, params: tuple = ()) -> list[dict]:
        """查询多行"""
        try:
            with pyodbc.connect(self._dsn) as conn:
                conn.setencoding(encoding="utf-8")
                cursor = conn.cursor()
                rows = cursor.execute(sql, params).fetchall()
                if not rows:
                    return []
                columns = [c[0] for c in cursor.description]
                return [dict(zip(columns, r)) for r in rows]
        except Exception as e:
            logger.warning(f"SQL Server 查询失败: {e}")
            raise


# 兼容旧代码的函数式接口
def _get_connection():
    try:
        import pyodbc
        dsn = settings.SQLSERVER_DSN or settings.KB_SQLSERVER_CONNECTION_STRING
        return pyodbc.connect(dsn)
    except Exception as e:
        logger.warning("SQL Server 连接失败: %s", e)
        raise


from contextlib import contextmanager
from typing import List, Dict, Any, Optional


@contextmanager
def get_connection():
    """上下文内使用连接，用毕关闭"""
    conn = _get_connection()
    try:
        yield conn
    finally:
        conn.close()


def execute_query(
    sql: str,
    params: Optional[tuple] = None,
) -> List[Dict[str, Any]]:
    """
    执行查询，返回行列表，每行为 dict（列名小写）。
    仅做 SELECT，不做写操作。
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(sql, params or ())
            columns = [c[0].lower() for c in cursor.description]
            rows = []
            for row in cursor.fetchall():
                rows.append(dict(zip(columns, row)))
            return rows
        finally:
            cursor.close()
