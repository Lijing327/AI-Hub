"""文本清洗、截断、拼接"""
import re
from typing import Optional


def clean_text(text: str | None) -> str:
    """清洗文本：去空白、换行规整"""
    if not text:
        return ""
    return " ".join(text.strip().split())


def truncate(text: str, max_len: int = 2000) -> str:
    """向量化文本别太长（按你后续模型再调）"""
    if len(text) <= max_len:
        return text
    return text[:max_len]


def clean(text: Optional[str]) -> str:
    """兼容旧代码：去空白、换行规整"""
    if text is None:
        return ""
    s = re.sub(r"\s+", " ", str(text).strip())
    return s.strip()


def concat(parts: list[str], sep: str = " ") -> str:
    """拼接多段文本，过滤空串"""
    return sep.join(p for p in parts if p and p.strip())
