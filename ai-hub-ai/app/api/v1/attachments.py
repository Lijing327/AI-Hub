"""
附件相关接口
当前 Excel 导入中的附件创建由 import_excel 内联完成；
本模块预留用于后续单独的附件上传、查询等接口
"""
from fastapi import APIRouter

router = APIRouter(prefix="/attachments", tags=["附件"])

# 预留：例如 GET /attachments/{article_id}、POST /attachments/upload 等
# 现有逻辑中附件随 Excel 导入在 ExcelImportService 内调用 DotnetClient.batch_create_assets 完成
