"""Excel 导入接口"""
import traceback
from typing import Optional
from fastapi import APIRouter, UploadFile, File, HTTPException

from app.schemas.excel import ExcelImportResponse
from app.services.excel_import_service import ExcelImportService
from app.core.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["Excel 导入"])


# 服务实例（可后续改为依赖注入）
_excel_service: Optional[ExcelImportService] = None


def get_excel_service() -> ExcelImportService:
    """获取 Excel 导入服务单例"""
    global _excel_service
    if _excel_service is None:
        _excel_service = ExcelImportService()
    return _excel_service


@router.post("/import/excel", response_model=ExcelImportResponse)
async def import_excel(file: UploadFile = File(...)):
    """
    导入 Excel 文件为知识条目
    - 接收 .xlsx 文件
    - 每行映射为一条知识草稿
    - 调用 .NET 批量创建文章与附件
    """
    logger.info("收到 Excel 导入请求: %s", file.filename or "")
    service = get_excel_service()
    try:
        contents = await file.read()
        return await service.import_excel(contents, file.filename or "unknown.xlsx")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("导入失败: %s\n%s", e, traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")
