"""
AI Hub Excel 导入服务
FastAPI 服务，用于处理 Excel 导入并调用 .NET 后端 API
"""
import os
import traceback
from typing import List, Optional
from io import BytesIO
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import pandas as pd
import httpx
from pathlib import Path
import json
import re
import logging
from urllib.parse import quote

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Hub Excel 导入服务",
    description="处理 Excel 文件导入，转换为知识条目",
    version="1.0.0"
)

# 配置（从环境变量读取）
DOTNET_BASE_URL = os.getenv("DOTNET_BASE_URL", "http://localhost:5000")
INTERNAL_TOKEN = os.getenv("INTERNAL_TOKEN", "your-internal-token-change-in-production")
DEFAULT_TENANT = os.getenv("DEFAULT_TENANT", "default")
ATTACHMENT_BASE_PATH = os.getenv("ATTACHMENT_BASE_PATH", "")
ATTACHMENT_BASE_URL = os.getenv("ATTACHMENT_BASE_URL", "http://localhost:5000/uploads")

# 加载 .env 文件（如果存在）
try:
    from dotenv import load_dotenv
    load_dotenv()
    # 重新读取环境变量（.env 文件中的值会覆盖上面的默认值）
    DOTNET_BASE_URL = os.getenv("DOTNET_BASE_URL", DOTNET_BASE_URL)
    INTERNAL_TOKEN = os.getenv("INTERNAL_TOKEN", INTERNAL_TOKEN)
    DEFAULT_TENANT = os.getenv("DEFAULT_TENANT", DEFAULT_TENANT)
    ATTACHMENT_BASE_PATH = os.getenv("ATTACHMENT_BASE_PATH", ATTACHMENT_BASE_PATH)
    ATTACHMENT_BASE_URL = os.getenv("ATTACHMENT_BASE_URL", ATTACHMENT_BASE_URL)
    logger.info(f"配置加载完成: DOTNET_BASE_URL={DOTNET_BASE_URL}, DEFAULT_TENANT={DEFAULT_TENANT}, ATTACHMENT_BASE_PATH={ATTACHMENT_BASE_PATH}")
except ImportError:
    logger.warning("python-dotenv 未安装，将使用环境变量或默认值")


class ExcelImportResponse(BaseModel):
    """Excel 导入响应"""
    total_rows: int
    success_count: int
    failure_count: int
    article_ids: List[int]
    failures: List[dict]


class ExcelRowFailure(BaseModel):
    """Excel 行处理失败信息"""
    row_index: int
    reason: str


def format_as_reasons(text: Optional[str]) -> Optional[str]:
    """格式化为原因列表（原因 1：...）"""
    if not text or not text.strip():
        return None
    
    # 按换行符或分号分割
    reasons = [r.strip() for r in re.split(r'[\n\r；;]', text) if r.strip()]
    
    if not reasons:
        return None
    
    # 如果已经是"原因 X："格式，直接返回
    if any(re.match(r'^原因\s*\d+[：:]', r) for r in reasons):
        return '\n'.join(reasons)
    
    # 否则添加编号
    return '\n'.join([f"原因 {i + 1}：{r}" for i, r in enumerate(reasons)])


def format_as_steps(text: Optional[str]) -> Optional[str]:
    """格式化为步骤列表（步骤 1：...）"""
    if not text or not text.strip():
        return None
    
    # 按换行符或分号分割
    steps = [s.strip() for s in re.split(r'[\n\r；;]', text) if s.strip()]
    
    if not steps:
        return None
    
    # 如果已经是"步骤 X："格式，直接返回
    if any(re.match(r'^步骤\s*\d+[：:]', s) for s in steps):
        return '\n'.join(steps)
    
    # 否则添加编号
    return '\n'.join([f"步骤 {i + 1}：{s}" for i, s in enumerate(steps)])


def extract_filename_from_reference(text: str) -> Optional[str]:
    """
    从文本引用中提取文件名
    支持格式：
    - 参考"xxx" 或 参考"xxx"（中文引号）
    - 参考：xxx
    - 见附件：xxx
    - 参考 xxx
    """
    if not text or not text.strip():
        return None
    
    text = text.strip()
    
    # 匹配：参考"xxx" 或 参考"xxx"（支持中文引号 "" 和英文引号 ""）
    # 匹配：参考"xxx"、参考"xxx"、参考"xxx"
    match = re.search(r'参考["""""]([^"""""]+)["""""]', text)
    if match:
        filename = match.group(1).strip()
        # 去除可能残留的引号
        filename = filename.strip('"""\'"')
        return filename if filename else None
    
    # 匹配：参考：xxx 或 参考:xxx
    match = re.search(r'参考[：:]\s*(.+)', text)
    if match:
        filename = match.group(1).strip()
        # 去除可能的前后引号
        filename = filename.strip('"""\'"')
        return filename if filename else None
    
    # 匹配：见附件：xxx
    match = re.search(r'见附件[：:]\s*(.+)', text)
    if match:
        filename = match.group(1).strip()
        filename = filename.strip('"""\'"')
        return filename if filename else None
    
    # 匹配：参考 xxx（空格分隔）
    match = re.search(r'参考\s+(.+)', text)
    if match:
        filename = match.group(1).strip()
        filename = filename.strip('"""\'"')
        return filename if filename else None
    
    # 如果都不匹配，返回原文（去除"参考"等前缀）
    filename = re.sub(r'^(参考|见附件)[：:\s]*', '', text)
    filename = filename.strip('"""\'"')
    return filename.strip() if filename.strip() else None


def find_attachment_file(filename: str) -> Optional[dict]:
    """
    在固定目录中递归查找附件文件（支持文件夹嵌套）
    返回：{ "path": 文件路径, "url": 访问URL, "type": 文件类型, "size": 文件大小, "file_name": 文件名 }
    """
    if not ATTACHMENT_BASE_PATH or not ATTACHMENT_BASE_PATH.strip():
        logger.debug(f"ATTACHMENT_BASE_PATH 未配置，跳过文件查找: {filename}")
        return None
    
    base_path = Path(ATTACHMENT_BASE_PATH.strip())
    if not base_path.exists():
        logger.debug(f"附件基础路径不存在: {base_path}，跳过文件查找: {filename}")
        return None
    
    # 清理文件名：去除所有类型的引号和前后空格
    clean_filename = filename.strip()
    # 去除各种引号（中文引号、英文引号）
    clean_filename = clean_filename.strip('"""\'"《》【】[]()（）')
    clean_filename = clean_filename.strip()
    
    # 如果文件名已经包含扩展名，先提取基础名称
    if '.' in clean_filename:
        clean_filename = Path(clean_filename).stem
    
    # 支持的扩展名和对应的文件类型
    extensions_map = {
        'video': ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv'],
        'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'],
        'pdf': ['.pdf'],
        'other': ['.doc', '.docx', '.xls', '.xlsx', '.txt', '.ppt', '.pptx']
    }
    
    # 尝试不同的扩展名，递归搜索所有子文件夹
    for asset_type, extensions in extensions_map.items():
        for ext in extensions:
            # 1. 先尝试精确匹配（文件名完全匹配，包括扩展名）
            full_filename = clean_filename + ext
            
            # 递归搜索：从根目录开始，遍历所有子文件夹
            for file_path in base_path.rglob(full_filename):
                if file_path.is_file():
                    file_size = file_path.stat().st_size
                    # 计算相对路径用于生成 URL
                    relative_path = file_path.relative_to(base_path)
                    # URL 格式：{ATTACHMENT_BASE_URL}/{相对路径}，对路径进行URL编码以支持中文
                    relative_path_str = str(relative_path).replace(os.sep, '/')
                    # 对路径的每一部分进行编码，但保留斜杠
                    encoded_path = '/'.join(quote(part, safe='') for part in relative_path_str.split('/'))
                    file_url = f"{ATTACHMENT_BASE_URL.rstrip('/')}/{encoded_path}"
                    logger.info(f"找到附件文件（精确匹配）: {clean_filename} -> {file_path.name} (路径: {relative_path})")
                    return {
                        "path": str(file_path),
                        "url": file_url,
                        "type": asset_type,
                        "size": file_size,
                        "file_name": file_path.name
                    }
            
            # 2. 如果精确匹配失败，尝试模糊匹配（文件名包含关键字）
            # 例如：filename="下芯机比例阀拆解"，可能匹配 "下芯机比例阀拆解.mp4" 或 "下芯机比例阀拆装.mp4"
            pattern = f"*{clean_filename}*{ext}"
            matches = list(base_path.rglob(pattern))
            if matches:
                # 优先选择文件名最接近的（包含完整关键字）
                best_match = None
                for file_path in matches:
                    if file_path.is_file():
                        file_name_lower = file_path.stem.lower()
                        clean_lower = clean_filename.lower()
                        # 如果文件名包含完整的关键字，优先选择
                        if clean_lower in file_name_lower:
                            best_match = file_path
                            break
                
                # 如果没有完全匹配的，选择第一个匹配的文件
                if not best_match and matches:
                    for file_path in matches:
                        if file_path.is_file():
                            best_match = file_path
                            break
                
                if best_match and best_match.is_file():
                    file_size = best_match.stat().st_size
                    relative_path = best_match.relative_to(base_path)
                    relative_path_str = str(relative_path).replace(os.sep, '/')
                    encoded_path = '/'.join(quote(part, safe='') for part in relative_path_str.split('/'))
                    file_url = f"{ATTACHMENT_BASE_URL.rstrip('/')}/{encoded_path}"
                    logger.info(f"找到附件文件（模糊匹配）: {clean_filename} -> {best_match.name} (路径: {relative_path})")
                    return {
                        "path": str(best_match),
                        "url": file_url,
                        "type": asset_type,
                        "size": file_size,
                        "file_name": best_match.name
                    }
    
    # 3. 如果文件匹配失败，尝试匹配文件夹名称
    # 例如：Excel 引用 "加砂球阀清挤砂"，匹配文件夹 "加砂球阀清挤砂"，返回文件夹内的第一个文件
    logger.debug(f"文件匹配失败，尝试匹配文件夹名称: {clean_filename}")
    clean_lower = clean_filename.lower()
    
    # 收集所有匹配的文件夹（优先完全匹配）
    matched_folders = []
    for folder_path in base_path.rglob("*"):
        if folder_path.is_dir():
            folder_name = folder_path.name
            folder_lower = folder_name.lower()
            
            # 完全匹配优先
            if clean_lower == folder_lower:
                matched_folders.insert(0, (folder_path, folder_name, 1))  # 优先级 1：完全匹配
            # 包含匹配
            elif clean_lower in folder_lower or folder_lower in clean_lower:
                matched_folders.append((folder_path, folder_name, 2))  # 优先级 2：包含匹配
    
    # 按优先级排序，优先处理完全匹配的文件夹
    matched_folders.sort(key=lambda x: x[2])
    
    # 在匹配的文件夹中查找文件
    for folder_path, folder_name, priority in matched_folders:
        # 按文件类型优先级查找（视频 > 图片 > PDF > 其他）
        type_priority = ['video', 'image', 'pdf', 'other']
        for asset_type in type_priority:
            if asset_type in extensions_map:
                for ext in extensions_map[asset_type]:
                    for file_path in folder_path.glob(f"*{ext}"):
                        if file_path.is_file():
                            file_size = file_path.stat().st_size
                            relative_path = file_path.relative_to(base_path)
                            relative_path_str = str(relative_path).replace(os.sep, '/')
                            encoded_path = '/'.join(quote(part, safe='') for part in relative_path_str.split('/'))
                            file_url = f"{ATTACHMENT_BASE_URL.rstrip('/')}/{encoded_path}"
                            match_type = "完全匹配" if priority == 1 else "包含匹配"
                            logger.info(f"找到附件文件（文件夹{match_type}）: {clean_filename} -> 文件夹[{folder_name}]/{file_path.name} (路径: {relative_path})")
                            return {
                                "path": str(file_path),
                                "url": file_url,
                                "type": asset_type,
                                "size": file_size,
                                "file_name": file_path.name
                            }
    
    logger.debug(f"未找到附件文件: {filename} (清理后: {clean_filename}, 搜索路径: {base_path})")
    return None


def map_excel_row_to_article(row: pd.Series, source_file_name: str, sheet_name: str, row_index: int) -> Optional[dict]:
    """
    将 Excel 行映射为知识条目 DTO（忠实还原原文档模式）
    
    表头：序号 | 现象（问题） | 检查点（原因） | 维修对策（解决办法） | 维修视频（附件）
    """
    # 读取字段（原样保留，不修改）
    # 注意：pandas 读取时，列名可能包含前后空格或特殊字符
    # 支持多种列名格式（带括号和不带括号）
    serial_number = ""
    for col_name in ["序号"]:
        if col_name in row.index and pd.notna(row.get(col_name)):
            serial_number = str(row.get(col_name)).strip()
            break
    
    phenomenon = ""
    # 尝试多种可能的列名（包括带括号和不带括号的变体）
    for col_name in ["现象（问题）", "现象(问题)", "现象 （问题）", "现象 (问题)", "现象", "问题"]:
        if col_name in row.index and pd.notna(row.get(col_name)):
            val = row.get(col_name)
            if val is not None and str(val).strip():
                phenomenon = str(val).strip()
                break
    
    checkpoints = ""
    for col_name in ["检查点（原因）", "检查点(原因)", "检查点 （原因）", "检查点 (原因)", "检查点", "原因"]:
        if col_name in row.index and pd.notna(row.get(col_name)):
            val = row.get(col_name)
            if val is not None and str(val).strip():
                checkpoints = str(val).strip()
                break
    
    solution = ""
    for col_name in ["维修对策（解决办法）", "维修对策(解决办法)", "维修对策 （解决办法）", "维修对策 (解决办法)", "对策", "维修对策", "解决办法", "解决方法"]:
        if col_name in row.index and pd.notna(row.get(col_name)):
            val = row.get(col_name)
            if val is not None and str(val).strip():
                solution = str(val).strip()
                break
    
    video_reference = ""
    for col_name in ["维修视频（附件）", "维修视频(附件)", "维修视频 （附件）", "维修视频 (附件)", "维修视频", "附件", "备注"]:
        if col_name in row.index and pd.notna(row.get(col_name)):
            val = row.get(col_name)
            if val is not None and str(val).strip():
                video_reference = str(val).strip()
                break
    
    # 跳过空行（必须有现象（问题））
    if not phenomenon:
        return None
    
    # 1) title = 【YH400/YH500】 + 现象（问题）
    title = f"【YH400/YH500】{phenomenon}".strip()
    if not title:
        return None
    
    # 2) question_text 必须保留原字段名与原文
    question_parts = []
    if serial_number:
        question_parts.append(f"【序号】{serial_number}")
    if phenomenon:
        question_parts.append(f"【现象（问题）】{phenomenon}")
    question_text = "\n".join(question_parts) if question_parts else None
    
    # 3) cause_text = 原样写入 检查点（原因）（保留编号/换行）
    cause_text = None
    if checkpoints:
        cause_text = f"【检查点（原因）】\n{checkpoints}"
    
    # 4) solution_text = 原样写入 维修对策（解决办法）（保留编号/换行）
    solution_parts = []
    if solution:
        solution_parts.append(f"【维修对策（解决办法）】\n{solution}")
    
    # 5) 维修视频（附件）：如果是文本，追加到 solution_text
    if video_reference:
        solution_parts.append(f"【维修视频（附件）】\n{video_reference}")
    
    solution_text = "\n\n".join(solution_parts) if solution_parts else None
    
    # 6) scope_json 必须包含：设备系列、来源文件、sheet、行号
    scope_data = {
        "设备系列": "YH400/YH500",
        "来源文件": source_file_name,
        "sheet": sheet_name,
        "行号": row_index
    }
    scope_json = json.dumps(scope_data, ensure_ascii=False)
    
    # 7) tags 至少包含：YH400, YH500, 来源:{文件名}
    tags = ["YH400", "YH500"]
    file_name_without_ext = Path(source_file_name).stem
    if file_name_without_ext:
        tags.append(f"来源:{file_name_without_ext}")
    
    # 如果现象/原因中包含关键字也可追加（简单关键词提取）
    text_content = f"{phenomenon} {checkpoints} {solution}".lower()
    if "yh400" in text_content and "YH400" not in tags:
        # 已经在tags中，跳过
        pass
    if "yh500" in text_content and "YH500" not in tags:
        # 已经在tags中，跳过
        pass
    
    # 提取附件信息（用于后续创建 kb_asset）
    # 支持一个单元格包含多个引用（用换行符、分号等分隔），每个引用都尝试匹配并创建附件记录
    attachment_info_list = []  # 改为列表，支持多个附件
    has_attachment_reference = False  # 标记是否有附件引用（无论是否找到文件）
    if video_reference:
        has_attachment_reference = True
        # 先按换行符分割，然后对每一行再按分号、中文分号等分割
        # 这样可以处理多种格式：换行分隔、分号分隔、或混合
        all_references = []
        for line in video_reference.split('\n'):
            line = line.strip()
            if not line:
                continue
            # 按分号、中文分号分割
            parts = re.split(r'[；;]', line)
            for part in parts:
                part = part.strip()
                if part:
                    all_references.append(part)
        
        # 如果按分隔符分割后只有一个，尝试从文本中提取所有"参考"xxx""格式的引用
        if len(all_references) == 1:
            # 使用正则表达式提取所有"参考"xxx""格式的引用
            pattern = r'参考["""""]([^"""""]+)["""""]'
            matches = re.findall(pattern, video_reference)
            if matches:
                all_references = [f'参考"{m}"' for m in matches]
        
        if len(all_references) > 1:
            logger.info(f"检测到 {len(all_references)} 个引用，将尝试匹配所有引用")
        else:
            logger.debug(f"提取到 {len(all_references)} 个引用: {all_references}")
        
        for ref_line in all_references:
            extracted_filename = extract_filename_from_reference(ref_line)
            if extracted_filename:
                # 再次清理文件名（确保去除所有引号）
                clean_extracted = extracted_filename.strip('"""\'"《》【】[]()（）').strip()
                if not clean_extracted:
                    continue
                
                file_info = find_attachment_file(clean_extracted)
                if file_info:
                    # 找到匹配的文件，添加到列表（不再 break，继续处理其他引用）
                    attachment_info_list.append({
                        "filename": clean_extracted,
                        "file_name": file_info.get("file_name", os.path.basename(file_info["path"])),
                        "url": file_info["url"],
                        "asset_type": file_info["type"],
                        "size": file_info["size"]
                    })
                    logger.info(f"✓ 找到附件文件: {clean_extracted} -> {file_info['url']}")
                else:
                    logger.debug(f"未找到附件文件: {clean_extracted} (原始引用: {ref_line[:50]}...)")
    
    # 如果只有一个附件，保持向后兼容（单个对象），如果有多个，使用列表
    attachment_info = attachment_info_list[0] if len(attachment_info_list) == 1 else (attachment_info_list if attachment_info_list else None)
    
    return {
        "title": title,
        "questionText": question_text,
        "causeText": cause_text,
        "solutionText": solution_text,
        "scopeJson": scope_json,
        "tags": ", ".join(tags),
        "createdBy": "系统导入",
        "_attachment_info": attachment_info  # 内部字段，用于后续创建附件
    }


@app.post("/import/excel", response_model=ExcelImportResponse)
async def import_excel(file: UploadFile = File(...)):
    """
    导入 Excel 文件为知识条目
    
    - 接收 .xlsx 文件
    - 使用 pandas 读取
    - 每行映射为一条知识草稿
    - 调用 .NET 的 /api/ai/kb/articles/batch 创建草稿
    - 如果找到附件文件，创建 kb_asset 记录（方案 B：元数据关联）
    """
    logger.info(f"收到 Excel 导入请求: {file.filename}")
    
    # 验证文件类型
    if not file.filename or not file.filename.endswith('.xlsx'):
        logger.warning(f"文件类型不正确: {file.filename}")
        raise HTTPException(status_code=400, detail="只支持 .xlsx 格式的 Excel 文件")
    
    try:
        # 读取 Excel 文件
        contents = await file.read()
        # 将 bytes 转换为 BytesIO 对象，pandas 才能读取
        excel_file = BytesIO(contents)
        
        # 先尝试从第一行读取表头
        df = pd.read_excel(excel_file, engine='openpyxl', header=0)
        
        # 验证必需字段（支持多种列名）
        # 故障现象列名可能为：故障现象、现象（问题）、现象、问题
        fault_phenomenon_columns = ["故障现象", "现象（问题）", "现象(问题)", "现象", "问题"]
        has_fault_phenomenon = any(col in df.columns for col in fault_phenomenon_columns)
        header_row = 0  # 记录 header 行号
        
        # 如果第一行没有找到必需字段，尝试从第二行读取（跳过标题行）
        if not has_fault_phenomenon:
            logger.info("第一行未找到必需字段，尝试从第二行读取表头（跳过标题行）")
            excel_file.seek(0)  # 重置文件指针
            df = pd.read_excel(excel_file, engine='openpyxl', header=1)
            header_row = 1  # 更新 header 行号
            
            # 再次验证
            has_fault_phenomenon = any(col in df.columns for col in fault_phenomenon_columns)
            if not has_fault_phenomenon:
                raise HTTPException(
                    status_code=400,
                    detail=f"缺少必需字段: 请包含以下任一列名 - {', '.join(fault_phenomenon_columns)}"
                )
        
        if df.empty:
            raise HTTPException(status_code=400, detail="Excel 文件为空")
        
        logger.info(f"读取到 {len(df)} 行数据")
        logger.info(f"列名: {list(df.columns)}")
        
        # 获取 sheet 名称（如果可能）
        sheet_name = "Sheet1"  # 默认值
        try:
            # 尝试从 Excel 文件中获取 sheet 名称
            excel_file.seek(0)
            import openpyxl
            wb = openpyxl.load_workbook(excel_file, read_only=True)
            if wb.sheetnames:
                sheet_name = wb.sheetnames[0]  # 使用第一个 sheet 的名称
            excel_file.seek(0)  # 重置文件指针
        except Exception as e:
            logger.warning(f"无法获取 sheet 名称，使用默认值: {str(e)}")
        
        # 确定 header 行号（用于计算 Excel 行号）
        header_row = 0 if has_fault_phenomenon else 1
        
        # 映射每行为知识条目 DTO
        articles = []  # 发送给后端的文章（不包含内部字段）
        articles_with_attachments = []  # 包含附件信息的完整文章数据
        failures = []
        skipped_rows = 0
        attachment_match_count = 0  # 附件匹配统计
        attachment_not_found_count = 0  # 附件未找到统计
        
        for idx, row in df.iterrows():
            try:
                # Excel 行号 = pandas index + header行数 + 1（Excel从1开始计数）
                # 如果 header=0，则 Excel行号 = idx + 2（第1行是表头，第2行开始是数据）
                # 如果 header=1，则 Excel行号 = idx + 3（第1行是标题，第2行是表头，第3行开始是数据）
                excel_row_number = int(idx) + header_row + 2
                
                # 调试：打印第一行的数据
                if idx == 0:
                    logger.info(f"第一行数据预览: {dict(row)}")
                
                article = map_excel_row_to_article(row, file.filename, sheet_name, excel_row_number)
                if article:
                    # 保存包含附件信息的原始 article
                    articles_with_attachments.append(article)
                    # 移除内部字段（不发送给后端）
                    article_for_api = {k: v for k, v in article.items() if not k.startswith("_")}
                    articles.append(article_for_api)
                else:
                    skipped_rows += 1
                    if idx < 3:  # 只记录前3行的跳过原因
                        logger.info(f"第 {excel_row_number} 行被跳过（空行或缺少必需字段）")
                # 如果返回 None，说明是空行，跳过
            except Exception as e:
                excel_row_number = int(idx) + header_row + 2
                logger.error(f"处理第 {excel_row_number} 行时出错: {str(e)}")
                failures.append({
                    "row_index": excel_row_number,
                    "reason": str(e)
                })
        
        # 统计附件匹配情况（支持多个附件）
        attachment_match_count = 0
        for a in articles_with_attachments:
            att_info = a.get("_attachment_info")
            if att_info:
                # 如果是列表，统计列表长度；如果是单个对象，计数为1
                if isinstance(att_info, list):
                    attachment_match_count += len(att_info)
                else:
                    attachment_match_count += 1
        
        attachment_total = sum(1 for a in articles_with_attachments if a.get("_has_attachment_reference", False))
        attachment_not_found_count = attachment_total - sum(1 for a in articles_with_attachments if a.get("_attachment_info"))
        
        logger.info(f"成功映射 {len(articles)} 条，跳过 {skipped_rows} 行，失败 {len(failures)} 行")
        if attachment_total > 0:
            match_rate = (attachment_match_count / attachment_total * 100) if attachment_total > 0 else 0
            logger.info(f"📎 附件匹配统计: 找到 {attachment_match_count}/{attachment_total} 个 ({match_rate:.1f}%)，未找到 {attachment_not_found_count} 个")
        
        if not articles:
            error_msg = f"没有有效的数据行。总行数: {len(df)}, 跳过: {skipped_rows}, 失败: {len(failures)}"
            if len(df) > 0:
                error_msg += f"\n列名: {list(df.columns)}"
                error_msg += f"\n第一行数据: {dict(df.iloc[0]) if len(df) > 0 else 'N/A'}"
            raise HTTPException(status_code=400, detail=error_msg)
        
        # 调用 .NET 后端批量创建接口
        logger.info(f"准备调用 .NET 后端: {DOTNET_BASE_URL}/api/ai/kb/articles/batch, 文章数量: {len(articles)}")
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{DOTNET_BASE_URL}/api/ai/kb/articles/batch",
                    json={"articles": articles},
                    headers={
                        "Content-Type": "application/json",
                        "X-Tenant-Id": DEFAULT_TENANT,
                        "X-Internal-Token": INTERNAL_TOKEN
                    },
                    timeout=30.0
                )
                
                logger.info(f".NET 后端响应状态码: {response.status_code}")
                
                if response.status_code != 200:
                    error_text = response.text
                    logger.error(f".NET 后端返回错误: {error_text}")
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f".NET 后端返回错误: {error_text}"
                    )
            except httpx.ConnectError as e:
                logger.error(f"无法连接到 .NET 后端 {DOTNET_BASE_URL}: {str(e)}")
                raise HTTPException(
                    status_code=503,
                    detail=f"无法连接到 .NET 后端服务，请确保服务已启动: {DOTNET_BASE_URL}"
                )
            except httpx.TimeoutException as e:
                logger.error(f"调用 .NET 后端超时: {str(e)}")
                raise HTTPException(
                    status_code=504,
                    detail="调用 .NET 后端超时，请稍后重试"
                )
            
            result = response.json()
            
            # 处理返回结果
            success_count = result.get("successCount", 0)
            failure_count = result.get("failureCount", 0)
            article_ids = []
            article_id_to_attachment = {}  # 映射 article_id -> attachment_info
            
            # 收集成功创建的 article IDs 和附件信息
            # 支持一个文章有多个附件（_attachment_info 可能是单个对象或列表）
            article_id_to_attachments = {}  # 改为映射到附件列表
            for i, item in enumerate(result.get("results", [])):
                if item.get("success") and item.get("articleId"):
                    article_id = item["articleId"]
                    article_ids.append(article_id)
                    
                    # 如果对应的 article 有附件信息，保存映射
                    if i < len(articles_with_attachments):
                        att_info = articles_with_attachments[i].get("_attachment_info")
                        if att_info:
                            # 如果是列表，直接使用；如果是单个对象，转换为列表
                            if isinstance(att_info, list):
                                article_id_to_attachments[article_id] = att_info
                            else:
                                article_id_to_attachments[article_id] = [att_info]
                elif not item.get("success"):
                    # 记录后端返回的失败信息
                    failures.append({
                        "row_index": item.get("index", -1) + (header_row + 2),  # 转换为 Excel 行号
                        "reason": item.get("error", "未知错误")
                    })
            
            # 批量创建附件（方案 B：元数据关联）
            if article_id_to_attachments:
                total_attachments = sum(len(atts) for atts in article_id_to_attachments.values())
                logger.info(f"准备创建 {total_attachments} 个附件记录（涉及 {len(article_id_to_attachments)} 篇文章）")
                
                # 记录每个文章的附件数量
                for article_id, att_info_list in article_id_to_attachments.items():
                    logger.info(f"  文章 ID {article_id}: {len(att_info_list)} 个附件")
                
                assets_to_create = []
                
                for article_id, att_info_list in article_id_to_attachments.items():
                    # 为每个附件创建记录
                    for att_info in att_info_list:
                        assets_to_create.append({
                            "articleId": article_id,
                            "assetType": att_info["asset_type"],
                            "fileName": att_info["file_name"],
                            "url": att_info["url"],
                            "size": att_info["size"],
                            "duration": None  # 视频时长暂不支持自动获取
                        })
                
                if assets_to_create:
                    try:
                        asset_response = await client.post(
                            f"{DOTNET_BASE_URL}/api/ai/kb/articles/assets/batch",
                            json={"assets": assets_to_create},
                            headers={
                                "Content-Type": "application/json",
                                "X-Tenant-Id": DEFAULT_TENANT,
                                "X-Internal-Token": INTERNAL_TOKEN
                            },
                            timeout=30.0
                        )
                        
                        if asset_response.status_code == 200:
                            asset_result = asset_response.json()
                            logger.info(f"成功创建 {asset_result.get('successCount', 0)} 个附件记录")
                        else:
                            logger.warning(f"创建附件失败: {asset_response.status_code} - {asset_response.text}")
                    except Exception as e:
                        logger.error(f"创建附件时出错: {str(e)}")
                        # 附件创建失败不影响主流程
            
            # 合并前端解析失败和后端创建失败
            total_failures = len(failures) + failure_count
            
            return ExcelImportResponse(
                total_rows=len(df),
                success_count=success_count,
                failure_count=total_failures,
                article_ids=article_ids,
                failures=failures
            )
    
    except pd.errors.EmptyDataError:
        logger.error("Excel 文件为空或格式不正确")
        raise HTTPException(status_code=400, detail="Excel 文件为空或格式不正确")
    except httpx.HTTPError as e:
        logger.error(f"调用 .NET 后端失败: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"调用 .NET 后端失败: {str(e)}"
        )
    except Exception as e:
        logger.error(f"导入失败: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"导入失败: {str(e)}"
        )


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "ok", "service": "ai-hub-ai"}


if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
