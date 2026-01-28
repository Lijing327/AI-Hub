"""Excel 导入相关 DTO"""
from typing import List, Any
from pydantic import BaseModel


class ExcelRowFailure(BaseModel):
    """Excel 行处理失败信息"""
    row_index: int
    reason: str


class ExcelImportResponse(BaseModel):
    """Excel 导入响应"""
    total_rows: int
    success_count: int
    failure_count: int
    article_ids: List[int]
    failures: List[dict]  # 兼容原有 dict 结构，元素形态等同 ExcelRowFailure
