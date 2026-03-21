"""向量 id 生成规则：{tenant_id}:kb:{article_id}:q|c|t[:device_type]"""
from typing import Literal, Optional

HitType = Literal["q", "c", "t"]


def make_vector_id(
    tenant_id: str,
    article_id: int,
    typ: str,
    device_type_code: Optional[str] = None
) -> str:
    """typ: q / c / t, 可选 device_type_code"""
    if device_type_code:
        return f"{tenant_id}:kb:{article_id}:{typ}:{device_type_code}"
    return f"{tenant_id}:kb:{article_id}:{typ}"


def vector_id(tenant_id: str, article_id: int, hit_type: HitType) -> str:
    """兼容旧代码：默认规则：{tenant_id}:kb:{article_id}:q"""
    return f"{tenant_id}:kb:{article_id}:{hit_type}"
