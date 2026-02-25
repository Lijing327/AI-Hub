"""
Excel 解析与行映射的纯函数工具
供 excel_import_service 调用
"""
import json
import os
import re
from pathlib import Path
from typing import List, Optional

import pandas as pd

from app.services.attachment_service import AttachmentService, extract_filename_from_reference
from app.core.logging_config import get_logger

logger = get_logger(__name__)


def extract_video_names_from_ref(video_ref: str) -> list[str]:
    """
    从「维修视频」列文本中提取所有视频名称，供加入 question_text 以便按视频名检索。
    支持格式：参考"xxx"、参考：xxx、参考 xxx；多引用用换行或分号分隔。
    """
    if not video_ref or not isinstance(video_ref, str):
        return []
    names: list[str] = []
    seen: set[str] = set()
    for line in video_ref.split("\n"):
        for part in re.split(r"[；;]", line.strip()):
            part = part.strip()
            if not part:
                continue
            # 处理 参考"xxx" 或 参考"xxx" 参考"yyy" 在同一行
            if part.count("参考") > 1 or '"' in part or '"' in part or '"' in part:
                matches = re.findall(r'参考["""""]([^"""""]+)["""""]', part)
                for m in matches:
                    n = m.strip().strip('"""\'""\'')
                    if n and n.lower() != "nan" and n not in seen:
                        seen.add(n)
                        names.append(n)
                continue
            fn = extract_filename_from_reference(part)
            if fn:
                fn = fn.strip('"""\'""\'《》【】[]()（）').strip()
                if fn and fn not in seen:
                    seen.add(fn)
                    names.append(fn)
    return names


def clean_bracketed_labels(text: str) -> str:
    """
    清理文本中的中括号标签和列标题
    移除：【序号】、【现象（问题）】、【检查点（原因）】等
    """
    if not text or not isinstance(text, str):
        return text if text else ""
    patterns_to_remove = [
        r"【[^】]*序号[^】]*】",
        r"【[^】]*现象[^】]*问题[^】]*】",
        r"【[^】]*现象[^】]*】",
        r"【[^】]*问题[^】]*】",
        r"【[^】]*检查点[^】]*原因[^】]*】",
        r"【[^】]*检查点[^】]*】",
        r"【[^】]*原因[^】]*】",
        r"【[^】]*维修对策[^】]*解决办法[^】]*】",
        r"【[^】]*维修对策[^】]*】",
        r"【[^】]*解决办法[^】]*】",
        r"【[^】]*维修视频[^】]*附件[^】]*】",
        r"【[^】]*维修视频[^】]*】",
        r"【[^】]*附件[^】]*】",
        r"【[^】]*YH400[^】]*YH500[^】]*】",
        r"【[^】]*YH400[^】]*】",
        r"【[^】]*YH500[^】]*】",
        r"\[[^\]]*序号[^\]]*\]",
        r"\[[^\]]*现象[^\]]*问题[^\]]*\]",
        r"\[[^\]]*检查点[^\]]*原因[^\]]*\]",
        r"\[[^\]]*维修对策[^\]]*解决办法[^\]]*\]",
        r"\[[^\]]*维修视频[^\]]*附件[^\]]*\]",
        r"\[[^\]]*YH400[^\]]*YH500[^\]]*\]",
        r"\[[^\]]*YH400[^\]]*\]",
        r"\[[^\]]*YH500[^\]]*\]",
    ]
    cleaned = text
    for _ in range(5):
        old = cleaned
        for pat in patterns_to_remove:
            cleaned = re.sub(pat, "", cleaned, flags=re.IGNORECASE)
        if cleaned == old:
            break
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    lines = [ln.strip() for ln in cleaned.split("\n")]
    cleaned = re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()
    return cleaned


def find_column_by_variants(row: pd.Series, variants: List[str]) -> Optional[str]:
    """通过多种列名变体查找列值，支持忽略空格和大小写"""
    for col_name in variants:
        if col_name in row.index:
            val = row.get(col_name)
            if pd.notna(val) and val is not None:
                s = str(val).strip()
                if s and s.lower() != "nan":
                    return s
    normalized = {str(c).strip().lower(): c for c in row.index}
    for v in variants:
        nv = v.strip().lower()
        if nv in normalized:
            val = row.get(normalized[nv])
            if pd.notna(val) and val is not None:
                s = str(val).strip()
                if s and s.lower() != "nan":
                    return s
    return None


def map_excel_row_to_article(
    row: pd.Series,
    source_file_name: str,
    sheet_name: str,
    row_index: int,
    attachment_service: AttachmentService,
) -> Optional[dict]:
    """
    将 Excel 行映射为知识条目（含 _attachment_info、_has_attachment_reference）
    表头：序号 | 现象（问题） | 检查点（原因） | 维修对策（解决办法） | 维修视频（附件）
    """
    serial = find_column_by_variants(row, ["序号"]) or ""
    phenomenon = find_column_by_variants(
        row,
        ["现象（问题）", "现象(问题)", "现象 （问题）", "现象 (问题)", "现象", "问题", "故障现象"],
    ) or ""
    checkpoints = find_column_by_variants(
        row,
        ["检查点（原因）", "检查点(原因)", "检查点 （原因）", "检查点 (原因)", "检查点", "原因"],
    ) or ""
    solution = find_column_by_variants(
        row,
        [
            "维修对策（解决办法）",
            "维修对策(解决办法)",
            "维修对策 （解决办法）",
            "维修对策 (解决办法)",
            "对策",
            "维修对策",
            "解决办法",
            "解决方法",
        ],
    ) or ""
    video_ref = find_column_by_variants(
        row,
        ["维修视频（附件）", "维修视频(附件)", "维修视频 （附件）", "维修视频 (附件)", "维修视频", "附件", "备注"],
    ) or ""

    if not phenomenon:
        return None
    title_keywords = [
        "现象", "问题", "检查点", "原因", "维修对策", "解决办法", "维修视频", "附件", "序号", "型号",
    ]
    if phenomenon in title_keywords or any(
        k in phenomenon for k in ["现象（问题）", "现象(问题)", "检查点（原因）", "维修对策（解决办法）"]
    ):
        return None

    def clean(s: str) -> str:
        if not s or str(s).lower() == "nan":
            return ""
        return clean_bracketed_labels(str(s))

    serial = clean(serial)
    phenomenon = clean(phenomenon)
    checkpoints = clean(checkpoints)
    solution = clean(solution)
    video_ref = clean(video_ref)

    title = clean_bracketed_labels(phenomenon.strip())
    if not title:
        return None
    # 现象 + 维修视频名称，使视频名也能像「现象」一样被检索
    question_parts = [clean(phenomenon.strip())] if phenomenon.strip() else []
    video_names = extract_video_names_from_ref(video_ref)
    if video_names:
        question_parts.append(" ".join(video_names))
    question_text = "\n".join(question_parts) if question_parts else None
    cause_text = clean(checkpoints.strip()) if checkpoints.strip() else None

    solution_parts = [clean(solution)] if solution.strip() else []
    if video_ref.strip():
        solution_parts.append(clean(video_ref.strip()))
    solution_text = "\n\n".join(solution_parts) if solution_parts else None
    if solution_text:
        solution_text = clean_bracketed_labels(solution_text)

    scope_json = json.dumps(
        {"设备系列": "YH400/YH500", "来源文件": source_file_name, "sheet": sheet_name, "行号": row_index},
        ensure_ascii=False,
    )
    tags = ["YH400", "YH500"]
    stem = Path(source_file_name).stem
    if stem:
        tags.append(f"来源:{stem}")
    tags_str = ", ".join(tags)

    # 附件：从“维修视频（附件）”解析引用并查找文件
    attachment_info_list: List[dict] = []
    has_attachment_reference = bool(video_ref)
    if video_ref:
        all_refs: List[str] = []
        for line in video_ref.split("\n"):
            for part in re.split(r"[；;]", line.strip()):
                if part.strip():
                    all_refs.append(part.strip())
        if video_ref.count("参考") > 1 or len(all_refs) == 1:
            matches = re.findall(r'参考["""""]([^"""""]+)["""""]', video_ref)
            if matches:
                all_refs = [f'参考"{m}"' for m in matches]
        for ref_line in all_refs:
            fn = extract_filename_from_reference(ref_line)
            if not fn:
                continue
            fn = fn.strip('"""\'""\'《》【】[]()（）').strip()
            if not fn:
                continue
            infos = attachment_service.find_attachment_files(fn)
            for info in infos:
                attachment_info_list.append({
                    "filename": fn,
                    "file_name": info.get("file_name", info.get("path", "").split(os.sep)[-1]),
                    "url": info["url"],
                    "asset_type": info["type"],
                    "size": info["size"],
                    "relative_path": info.get("relative_path"),
                    "source_ref": fn,
                })
        # 去重
        seen = set()
        unique = []
        for att in attachment_info_list:
            key = att.get("url") or att.get("relative_path")
            if key and key not in seen:
                seen.add(key)
                unique.append(att)
        attachment_info_list = unique

    attachment_info = attachment_info_list if attachment_info_list else None
    final_title = clean_bracketed_labels(title)
    final_question_text = clean_bracketed_labels(question_text) if question_text else None
    final_cause_text = clean_bracketed_labels(cause_text) if cause_text else None
    final_solution_text = clean_bracketed_labels(solution_text) if solution_text else None

    return {
        "title": final_title,
        "questionText": final_question_text,
        "causeText": final_cause_text,
        "solutionText": final_solution_text,
        "scopeJson": scope_json,
        "tags": tags_str,
        "createdBy": "系统导入",
        "_attachment_info": attachment_info,
        "_has_attachment_reference": has_attachment_reference,
    }
