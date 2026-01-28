"""
附件查找与元数据构建
在固定目录中根据引用名查找文件，并构建可供 .NET 批量创建用的元数据
"""
import os
import re
from pathlib import Path
from typing import List, Optional
from urllib.parse import quote

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


def _guess_asset_type_by_ext(ext: str) -> str:
    """根据扩展名判断文件类型"""
    ext = ext.lower()
    if ext in [".mp4", ".avi", ".mov", ".wmv", ".flv", ".mkv"]:
        return "video"
    if ext in [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"]:
        return "image"
    if ext == ".pdf":
        return "pdf"
    if ext in [".doc", ".docx", ".xls", ".xlsx", ".txt", ".ppt", ".pptx"]:
        return "other"
    return "other"


def _should_skip_file(p: Path) -> bool:
    """过滤系统/临时文件"""
    name = p.name.lower()
    if name in ["thumbs.db", ".ds_store", "desktop.ini"]:
        return True
    if name.startswith("~$"):
        return True
    return False


def _build_file_info(base_path: Path, file_path: Path, base_url: str) -> dict:
    """构建单条文件信息字典（含 url、type、size、file_name、relative_path）"""
    file_size = file_path.stat().st_size
    relative_path = file_path.relative_to(base_path)
    relative_path_str = str(relative_path).replace(os.sep, "/")
    encoded_path = "/".join(quote(part, safe="") for part in relative_path_str.split("/"))
    file_url = f"{base_url.rstrip('/')}/{encoded_path}"
    return {
        "path": str(file_path),
        "url": file_url,
        "type": _guess_asset_type_by_ext(file_path.suffix),
        "size": file_size,
        "file_name": file_path.name,
        "relative_path": relative_path_str,
    }


def extract_filename_from_reference(text: str) -> Optional[str]:
    """
    从文本引用中提取文件名
    支持：参考"xxx"、参考：xxx、见附件：xxx、参考 xxx
    """
    if not text or not text.strip():
        return None
    text = text.strip()
    # 参考"xxx" / 参考"xxx"
    match = re.search(r'参考["""""]([^"""""]+)["""""]', text)
    if match:
        return match.group(1).strip().strip('"""\'""\'') or None
    match = re.search(r"参考[：:]\s*(.+)", text)
    if match:
        return match.group(1).strip().strip('"""\'""\'') or None
    match = re.search(r"见附件[：:]\s*(.+)", text)
    if match:
        return match.group(1).strip().strip('"""\'""\'') or None
    match = re.search(r"参考\s+(.+)", text)
    if match:
        return match.group(1).strip().strip('"""\'""\'') or None
    filename = re.sub(r"^(参考|见附件)[：:\s]*", "", text).strip('"""\'""\'')
    return filename.strip() or None


class AttachmentService:
    """附件查找服务，依赖配置中的 ATTACHMENT_BASE_PATH / ATTACHMENT_BASE_URL"""

    def __init__(
        self,
        base_path: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.base_path = (base_path or settings.ATTACHMENT_BASE_PATH or "").strip()
        self.base_url = base_url or settings.ATTACHMENT_BASE_URL or ""

    def find_attachment_files(self, filename: str) -> List[dict]:
        """
        在固定目录中递归查找附件
        - 命中文件：返回 1 条
        - 命中文件夹：返回该目录下所有文件（递归）
        - 未命中：返回 []
        返回元素形态：{"path","url","type","size","file_name","relative_path"}
        """
        if not self.base_path:
            logger.debug("ATTACHMENT_BASE_PATH 未配置，跳过文件查找: %s", filename)
            return []
        base_path = Path(self.base_path)
        if not base_path.exists():
            logger.debug("附件基础路径不存在: %s，跳过: %s", base_path, filename)
            return []

        clean_filename = filename.strip().strip('"""\'""\'《》【】[]()（）').strip()
        logger.debug("查找附件: 原始='%s', 清理后='%s'", filename, clean_filename)

        if "." in clean_filename:
            clean_filename = Path(clean_filename).stem

        extensions_map = {
            "video": [".mp4", ".avi", ".mov", ".wmv", ".flv", ".mkv"],
            "image": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"],
            "pdf": [".pdf"],
            "other": [".doc", ".docx", ".xls", ".xlsx", ".txt", ".ppt", ".pptx"],
        }

        # 1) 精确匹配
        for asset_type, exts in extensions_map.items():
            for ext in exts:
                full_name = clean_filename + ext
                root_file = base_path / full_name
                if root_file.is_file():
                    logger.info("找到附件（根目录精确）: %s -> %s", clean_filename, root_file.name)
                    info = _build_file_info(base_path, root_file, self.base_url)
                    info["type"] = asset_type
                    return [info]
                for fp in base_path.rglob(full_name):
                    if fp.is_file():
                        logger.info("找到附件（精确）: %s -> %s", clean_filename, fp.name)
                        info = _build_file_info(base_path, fp, self.base_url)
                        info["type"] = asset_type
                        return [info]

                # 2) 模糊匹配
                for pattern in [f"*{clean_filename}*{ext}", f"{clean_filename}*{ext}"]:
                    for fp in list(base_path.glob(pattern)) + list(base_path.rglob(pattern)):
                        if fp.is_file():
                            stem_lower = fp.stem.lower()
                            if stem_lower == clean_filename.lower() or clean_filename.lower() in stem_lower:
                                logger.info("找到附件（模糊）: %s -> %s", clean_filename, fp.name)
                                info = _build_file_info(base_path, fp, self.base_url)
                                info["type"] = asset_type
                                return [info]

        # 3) 文件夹匹配
        clean_lower = clean_filename.lower()
        for folder in base_path.rglob("*"):
            if not folder.is_dir():
                continue
            fn_lower = folder.name.lower()
            if clean_lower == fn_lower or clean_lower in fn_lower or fn_lower in clean_lower:
                files = [p for p in folder.rglob("*") if p.is_file() and not _should_skip_file(p)]
                files.sort(key=lambda p: str(p).lower())
                results = [_build_file_info(base_path, p, self.base_url) for p in files]
                logger.info("找到附件（文件夹）: %s -> %s 共 %d 个", clean_filename, folder.name, len(results))
                return results

        # 4) 兜底：按 stem 完全匹配
        for fp in base_path.iterdir():
            if fp.is_file() and not _should_skip_file(fp) and fp.stem.lower() == clean_lower:
                info = _build_file_info(base_path, fp, self.base_url)
                info["type"] = _guess_asset_type_by_ext(fp.suffix)
                return [info]
        for fp in base_path.rglob("*"):
            if fp.is_file() and not _should_skip_file(fp) and fp.stem.lower() == clean_lower:
                info = _build_file_info(base_path, fp, self.base_url)
                info["type"] = _guess_asset_type_by_ext(fp.suffix)
                return [info]

        logger.warning("未找到附件: %s (清理后: %s)", filename, clean_filename)
        return []
