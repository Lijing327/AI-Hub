"""
附件查找与元数据构建
在固定目录中根据引用名查找文件，并构建可供 .NET 批量创建用的元数据
支持两种模式：本地目录（ATTACHMENT_BASE_PATH）或远程 API（api/files/list）
"""
import os
import re
import unicodedata
from pathlib import Path
from typing import Any, List, Optional
from urllib.parse import quote

import httpx
from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


def _normalize_for_match(s: str) -> str:
    """
    用于匹配时的规范化：小写、去空白、Unicode 正规化、去掉不可见字符。
    解决 Excel/引用与磁盘文件名在全角/半角、不可见字符上的差异。
    """
    if not s or not isinstance(s, str):
        return ""
    # 去掉零宽字符、不可见字符
    s = "".join(c for c in s if unicodedata.category(c) != "Cf" and c not in "\u200b\u200c\u200d\ufeff")
    s = unicodedata.normalize("NFKC", s).strip().lower()
    return s


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


def _is_local_url(u: str) -> bool:
    """判断 URL 是否为本地地址（不应作为生产附件外链）"""
    if not u:
        return False
    return "localhost" in u or "127.0.0.1" in u


def rewrite_attachment_url_to_remote(url: str) -> str:
    """
    将数据库/接口里存的本地或相对附件 URL 重写为生产可访问地址，
    避免前端点击附件跳转到 localhost。
    优先使用 ATTACHMENT_FILES_API_BASE_URL + ATTACHMENT_REMOTE_PATH；
    否则用 ATTACHMENT_BASE_URL（如 https://域名:4023/uploads）拼出可访问链接。
    若当前配置仍是本地地址，则优先用 ATTACHMENT_FILES_API_BASE_URL 再拼一次，避免漏配。
    """
    if not url or not isinstance(url, str):
        return url or ""
    from urllib.parse import unquote
    url = url.strip()
    # 判断是否为“本地/需重写”的 URL
    is_local = (
        "localhost" in url
        or url.startswith("http://127.0.0.1")
        or (url.startswith("/uploads/") or url.startswith("uploads/"))
    )
    if not is_local:
        return url

    parts = url.rstrip("/").replace("\\", "/").split("/")
    filename = unquote(parts[-1]) if parts else ""
    if not filename:
        return url

    remote_path = (settings.ATTACHMENT_REMOTE_PATH or "").replace("\\", "/").strip().strip("/")
    encoded_name = quote(filename, safe="")

    # 优先：ATTACHMENT_FILES_API_BASE_URL + ATTACHMENT_REMOTE_PATH（且 base 非本地）
    base = (settings.ATTACHMENT_FILES_API_BASE_URL or "").strip()
    if base and not _is_local_url(base):
        if remote_path:
            encoded_path = "/".join(quote(p, safe="") for p in remote_path.split("/"))
            return f"{base.rstrip('/')}/uploads/{encoded_path}/{encoded_name}"
        return f"{base.rstrip('/')}/uploads/{encoded_name}"

    # 兜底：ATTACHMENT_BASE_URL（且非本地）拼出可访问地址
    attachment_base = (settings.ATTACHMENT_BASE_URL or "").strip()
    if attachment_base and not _is_local_url(attachment_base):
        if remote_path:
            encoded_path = "/".join(quote(p, safe="") for p in remote_path.split("/"))
            return f"{attachment_base.rstrip('/')}/{encoded_path}/{encoded_name}"
        return f"{attachment_base.rstrip('/')}/{encoded_name}"

    # 配置里仍是本地或未配：若通过环境变量单独设置了 FILES_API_BASE_URL（非本地），仍用其拼写
    if base and not _is_local_url(base):
        if remote_path:
            encoded_path = "/".join(quote(p, safe="") for p in remote_path.split("/"))
            return f"{base.rstrip('/')}/uploads/{encoded_path}/{encoded_name}"
        return f"{base.rstrip('/')}/uploads/{encoded_name}"

    return url


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


def _parse_remote_file_list(response_data: Any, base_url: str) -> List[dict]:
    """
    解析 api/files/list 返回的 JSON，统一为 [{"file_name","url","relative_path","type","size","directory"}]
    接口格式：{ "code": 0, "message": "操作成功", "data": [ { "name", "relativePath", "directory", "size" } ] }
    """
    base_url = (base_url or "").rstrip("/")
    items: List[dict] = []
    if isinstance(response_data, list):
        items = response_data
    elif isinstance(response_data, dict):
        items = response_data.get("data") or response_data.get("files") or response_data.get("list") or []
    if not items:
        return []
    result = []
    for it in items:
        if not isinstance(it, dict):
            continue
        name = it.get("name") or it.get("fileName") or it.get("filename") or ""
        # relativePath 可能为 "diyi\\永红造型线维修视频\\xxx.jpg"
        raw_path = it.get("path") or it.get("relativePath") or name
        relative_path = raw_path.replace("\\", "/") if isinstance(raw_path, str) else str(raw_path)
        if not name and relative_path:
            name = relative_path.split("/")[-1]
        if not name:
            continue
        # 无 url 时用 base_url + 编码后的路径拼出访问地址
        if it.get("url"):
            url = it["url"]
        elif base_url and relative_path:
            encoded = "/".join(quote(part, safe="") for part in relative_path.split("/"))
            url = f"{base_url.rstrip('/')}/uploads/{encoded}"
        else:
            url = ""
        ext = Path(name).suffix.lower()
        is_dir = it.get("directory", False)
        result.append({
            "path": relative_path,
            "url": url,
            "type": _guess_asset_type_by_ext(ext) if not is_dir else "directory",
            "size": it.get("size") or it.get("fileSize") or 0,
            "file_name": name,
            "relative_path": relative_path,
            "directory": is_dir,
        })
    return result


class AttachmentService:
    """附件查找服务：本地目录（ATTACHMENT_BASE_PATH）或远程 api/files/list 二选一"""

    def __init__(
        self,
        base_path: Optional[str] = None,
        base_url: Optional[str] = None,
        files_api_base_url: Optional[str] = None,
        remote_path: Optional[str] = None,
    ):
        self.base_path = (base_path or settings.ATTACHMENT_BASE_PATH or "").strip()
        self.base_url = (base_url or settings.ATTACHMENT_BASE_URL or "").strip()
        self.remote_base = (files_api_base_url or settings.ATTACHMENT_FILES_API_BASE_URL or "").strip()
        self.remote_path = (remote_path or settings.ATTACHMENT_REMOTE_PATH or "").strip()

    def _fetch_remote_file_list(self) -> List[dict]:
        """调用 GET api/files/list?path=... 获取远程文件列表"""
        if not self.remote_base or not self.remote_path:
            return []
        url = f"{self.remote_base.rstrip('/')}/api/files/list"
        params = {"path": self.remote_path}
        try:
            with httpx.Client(timeout=15.0) as client:
                resp = client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()
        except Exception as e:
            logger.warning("调用远程附件列表 API 失败: %s", e)
            return []
        return _parse_remote_file_list(data, self.remote_base)

    def _find_attachment_files_remote(self, filename: str) -> List[dict]:
        """基于远程 api/files/list 结果按文件名/路径匹配（只返回文件，不含 directory:true）"""
        clean_filename = filename.strip().strip('"""\'""\'《》【】[]()（）').strip()
        if "." in clean_filename:
            clean_filename = Path(clean_filename).stem
        norm_clean = _normalize_for_match(clean_filename)
        logger.debug("远程查找附件: 原始='%s', 清理后='%s', 规范化='%s'", filename, clean_filename, norm_clean)

        all_items = self._fetch_remote_file_list()
        if not all_items:
            logger.warning("远程附件列表为空: path=%s", self.remote_path)
            return []

        # 只参与匹配的文件（排除目录项）
        file_only = [f for f in all_items if not f.get("directory")]

        # 1) 精确匹配：文件名 stem 与 norm_clean 一致
        for f in file_only:
            stem = Path(f.get("file_name", "")).stem
            if _normalize_for_match(stem) == norm_clean:
                logger.info("找到远程附件（精确）: %s -> %s", clean_filename, f.get("file_name"))
                return [f]
        # 2) 路径中含“文件夹名”匹配：relative_path 的某一段与 norm_clean 一致，返回该路径下所有文件
        segment_matched = []
        for f in file_only:
            rp = (f.get("relative_path") or f.get("path") or "").replace("\\", "/")
            parts = rp.split("/")
            for part in parts:
                if _normalize_for_match(Path(part).stem) == norm_clean:
                    segment_matched.append(f)
                    break
        if segment_matched:
            logger.info("找到远程附件（路径段）: %s 共 %d 个", clean_filename, len(segment_matched))
            return segment_matched
        # 3) 模糊：stem 包含或被包含
        for f in file_only:
            stem = Path(f.get("file_name", "")).stem
            norm_stem = _normalize_for_match(stem)
            if norm_clean in norm_stem or norm_stem in norm_clean:
                logger.info("找到远程附件（模糊）: %s -> %s", clean_filename, f.get("file_name"))
                return [f]
        logger.warning("未找到远程附件: %s (清理后: %s)", filename, clean_filename)
        return []

    def find_attachment_files(self, filename: str) -> List[dict]:
        """
        在固定目录或远程 api/files/list 中查找附件
        - 命中文件：返回 1 条
        - 命中文件夹：返回该目录下所有文件（递归）
        - 未命中：返回 []
        返回元素形态：{"path","url","type","size","file_name","relative_path"}
        """
        # 优先使用远程 API（生产环境服务器附件）
        if self.remote_base and self.remote_path:
            return self._find_attachment_files_remote(filename)

        if not self.base_path:
            logger.debug("ATTACHMENT_BASE_PATH 未配置，跳过文件查找: %s", filename)
            return []
        base_path = Path(self.base_path)
        if not base_path.exists():
            logger.debug("附件基础路径不存在: %s，跳过: %s", base_path, filename)
            return []

        clean_filename = filename.strip().strip('"""\'""\'《》【】[]()（）').strip()
        if "." in clean_filename:
            clean_filename = Path(clean_filename).stem
        norm_clean = _normalize_for_match(clean_filename)
        logger.debug("查找附件: 原始='%s', 清理后='%s', 规范化='%s'", filename, clean_filename, norm_clean)

        extensions_map = {
            "video": [".mp4", ".avi", ".mov", ".wmv", ".flv", ".mkv"],
            "image": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"],
            "pdf": [".pdf"],
            "other": [".doc", ".docx", ".xls", ".xlsx", ".txt", ".ppt", ".pptx"],
        }
        all_exts = set()
        for exts in extensions_map.values():
            all_exts.update(e.lower() for e in exts)

        # 0) 按“实际文件名”遍历匹配（避免路径拼接导致的编码/全角差异）
        for fp in base_path.iterdir():
            if fp.is_file() and not _should_skip_file(fp) and fp.suffix.lower() in all_exts:
                if _normalize_for_match(fp.stem) == norm_clean:
                    logger.info("找到附件（根目录-规范化匹配）: %s -> %s", clean_filename, fp.name)
                    info = _build_file_info(base_path, fp, self.base_url)
                    info["type"] = _guess_asset_type_by_ext(fp.suffix)
                    return [info]
        for fp in base_path.rglob("*"):
            if fp.is_file() and not _should_skip_file(fp) and fp.suffix.lower() in all_exts:
                if _normalize_for_match(fp.stem) == norm_clean:
                    logger.info("找到附件（全目录-规范化匹配）: %s -> %s", clean_filename, fp.name)
                    info = _build_file_info(base_path, fp, self.base_url)
                    info["type"] = _guess_asset_type_by_ext(fp.suffix)
                    return [info]

        # 1) 精确匹配（路径拼接）
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

                # 2) 模糊匹配（使用规范化比较）
                for pattern in [f"*{clean_filename}*{ext}", f"{clean_filename}*{ext}"]:
                    for fp in list(base_path.glob(pattern)) + list(base_path.rglob(pattern)):
                        if fp.is_file():
                            norm_stem = _normalize_for_match(fp.stem)
                            if norm_stem == norm_clean or norm_clean in norm_stem or norm_stem in norm_clean:
                                logger.info("找到附件（模糊）: %s -> %s", clean_filename, fp.name)
                                info = _build_file_info(base_path, fp, self.base_url)
                                info["type"] = asset_type
                                return [info]

        # 3) 文件夹匹配（使用规范化比较）
        for folder in base_path.rglob("*"):
            if not folder.is_dir():
                continue
            norm_folder = _normalize_for_match(folder.name)
            if norm_clean == norm_folder or norm_clean in norm_folder or norm_folder in norm_clean:
                files = [p for p in folder.rglob("*") if p.is_file() and not _should_skip_file(p)]
                files.sort(key=lambda p: str(p).lower())
                results = [_build_file_info(base_path, p, self.base_url) for p in files]
                logger.info("找到附件（文件夹）: %s -> %s 共 %d 个", clean_filename, folder.name, len(results))
                return results

        # 4) 兜底：按规范化 stem 完全匹配
        for fp in base_path.iterdir():
            if fp.is_file() and not _should_skip_file(fp) and _normalize_for_match(fp.stem) == norm_clean:
                info = _build_file_info(base_path, fp, self.base_url)
                info["type"] = _guess_asset_type_by_ext(fp.suffix)
                return [info]
        for fp in base_path.rglob("*"):
            if fp.is_file() and not _should_skip_file(fp) and _normalize_for_match(fp.stem) == norm_clean:
                info = _build_file_info(base_path, fp, self.base_url)
                info["type"] = _guess_asset_type_by_ext(fp.suffix)
                return [info]

        # 5) 兜底：规范化后“包含”匹配（取 stem 最短的，避免误匹配）
        candidates = []
        for fp in base_path.iterdir():
            if fp.is_file() and not _should_skip_file(fp) and fp.suffix.lower() in all_exts:
                norm_stem = _normalize_for_match(fp.stem)
                if norm_clean in norm_stem or norm_stem in norm_clean:
                    candidates.append((len(fp.stem), fp))
        for fp in base_path.rglob("*"):
            if fp.is_file() and not _should_skip_file(fp) and fp.suffix.lower() in all_exts:
                norm_stem = _normalize_for_match(fp.stem)
                if norm_clean in norm_stem or norm_stem in norm_clean:
                    candidates.append((len(fp.stem), fp))
        if candidates:
            candidates.sort(key=lambda x: (x[0], str(x[1]).lower()))
            _, best = candidates[0]
            logger.info("找到附件（兜底-包含匹配）: %s -> %s", clean_filename, best.name)
            info = _build_file_info(base_path, best, self.base_url)
            info["type"] = _guess_asset_type_by_ext(best.suffix)
            return [info]

        logger.warning("未找到附件: %s (清理后: %s)", filename, clean_filename)
        return []
