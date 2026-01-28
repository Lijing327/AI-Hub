"""向量 id 生成规则：{tenant_id}:kb:{article_id}:q|c|t"""
from typing import Literal

HitType = Literal["q", "c", "t"]


def make_vector_id(tenant_id: str, article_id: int, typ: str) -> str:
    """typ: q / c / t"""
    return f"{tenant_id}:kb:{article_id}:{typ}"


def vector_id(tenant_id: str, article_id: int, hit_type: HitType) -> str:
    """兼容旧代码：默认规则：{tenant_id}:kb:{article_id}:q"""
    return f"{tenant_id}:kb:{article_id}:{hit_type}"
