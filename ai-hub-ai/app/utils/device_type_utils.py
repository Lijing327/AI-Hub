"""设备类型解析工具"""
import json
import re
from typing import List, Optional
from app.core.logging_config import get_logger

logger = get_logger(__name__)

# 设备类型标准码映射
DEVICE_TYPE_MAPPING = {
    "造型机": "MOULDING_MACHINE",
    "浇注机": "POURING_MACHINE",
    "抛丸机": "SHOT_BLAST_MACHINE",
    "通用": "COMMON",
}

# 反向映射，用于标准码到中文
DEVICE_TYPE_REVERSE_MAPPING = {v: k for k, v in DEVICE_TYPE_MAPPING.items()}

# 设备型号到设备类型的映射（可根据实际情况扩展）
DEVICE_MODEL_MAPPING = {
    # 造型机系列
    "YH400": "MOULDING_MACHINE",
    "YH500": "MOULDING_MACHINE",
    "YH600": "MOULDING_MACHINE",
    # 浇注机系列
    "JZ-100": "POURING_MACHINE",
    "JZ-200": "POURING_MACHINE",
    "JZ-300": "POURING_MACHINE",
    # 抛丸机系列
    "PW-150": "SHOT_BLAST_MACHINE",
    "PW-250": "SHOT_BLAST_MACHINE",
    "PW-350": "SHOT_BLAST_MACHINE",
}

# 型号前缀 → 设备类型（与历史数据修复脚本一致，用于从 model 字符串推断）
DEVICE_MODEL_PREFIX = {
    "MOULDING_MACHINE": ["YH"],
    "POURING_MACHINE": ["JZ"],
    "SHOT_BLAST_MACHINE": ["PW"],
}


def parse_device_types_from_scope(scope_json: Optional[str]) -> List[str]:
    """
    从 scope_json 中解析设备类型并返回标准码列表

    Args:
        scope_json: JSON格式的适用范围字符串

    Returns:
        设备类型标准码列表，如 ["MOULDING_MACHINE", "POURING_MACHINE"]
    """
    if not scope_json or not scope_json.strip():
        return ["COMMON"]

    try:
        # 解析JSON
        scope_data = json.loads(scope_json.strip())
    except (json.JSONDecodeError, TypeError):
        logger.warning("scope_json 格式错误，解析失败: %s", scope_json)
        return ["COMMON"]

    # 获取设备类型字段
    device_types_raw = scope_data.get("设备类型", "")

    # 如果没有设备类型字段，返回通用
    if not device_types_raw or not str(device_types_raw).strip():
        return ["COMMON"]

    # 处理字符串格式的设备类型
    device_types_str = str(device_types_raw).strip()

    # 分割设备类型（支持中英文逗号、顿号、分号）
    device_type_parts = re.split(r"[,，、；;]", device_types_str)

    # 解析每个设备类型
    device_type_codes = []
    for part in device_type_parts:
        part = part.strip()
        if not part:
            continue

        if part == "抛瓦机":
            device_type_codes.append("SHOT_BLAST_MACHINE")
            continue

        # 尝试直接映射为标准码
        if part in DEVICE_TYPE_MAPPING:
            device_type_codes.append(DEVICE_TYPE_MAPPING[part])
        elif part in DEVICE_TYPE_REVERSE_MAPPING:
            device_type_codes.append(part)
        # 尝试通过设备型号映射
        elif part in DEVICE_MODEL_MAPPING:
            device_type_codes.append(DEVICE_MODEL_MAPPING[part])
        else:
            logger.warning("未知的设备类型: %s", part)
            continue

    # 如果没有有效的设备类型，返回通用
    if not device_type_codes:
        return ["COMMON"]

    # 去重并返回
    device_type_codes = list(set(device_type_codes))
    logger.debug("解析设备类型: %s -> %s", device_types_str, device_type_codes)

    return device_type_codes


def normalize_device_type_name(name: str) -> Optional[str]:
    """
    将中文设备名称或标准码映射为标准码

    Args:
        name: 设备名称，可以是中文或标准码

    Returns:
        标准码，如果无法识别则返回None
    """
    if not name or not str(name).strip():
        return None

    name = str(name).strip()

    # 常见笔误：瓦 / 丸
    if name == "抛瓦机":
        return "SHOT_BLAST_MACHINE"

    # 直接是标准码
    if name in DEVICE_TYPE_MAPPING.values():
        return name

    # 中文映射
    if name in DEVICE_TYPE_MAPPING:
        return DEVICE_TYPE_MAPPING[name]

    # 设备型号映射
    if name in DEVICE_MODEL_MAPPING:
        return DEVICE_MODEL_MAPPING[name]

    logger.warning("无法识别的设备类型名称: %s", name)
    return None


def infer_device_type_from_model_or_label(text: str) -> Optional[str]:
    """
    从设备型号或展示名称推断标准码（精确表映射 → 型号前缀 → 关键词）。
    """
    if not text or not str(text).strip():
        return None
    raw = str(text).strip()
    mapped = normalize_device_type_name(raw)
    if mapped:
        return mapped
    lower = raw.lower()
    for dtype, prefixes in DEVICE_MODEL_PREFIX.items():
        for p in prefixes:
            pl = p.lower()
            if lower.startswith(pl) or pl in lower:
                return dtype
    return extract_device_type_from_text(raw)


def scope_label_for_excel_import(raw: Optional[str]) -> Optional[str]:
    """
    Excel 导入时可选的「设备类型」：空表示沿用旧版导入逻辑（不写 设备类型 字段）；
    非空则校验并返回写入 scope_json 的中文名（造型机/浇注机/抛丸机/通用）。
    """
    if raw is None or not str(raw).strip():
        return None
    s = str(raw).strip()
    code = normalize_device_type_name(s)
    if not code:
        raise ValueError(f"无效的设备类型: {s}")
    return DEVICE_TYPE_REVERSE_MAPPING[code]


def resolve_device_type_for_query(
    device_type_code: Optional[str],
    device_model: Optional[str],
) -> Optional[str]:
    """
    解析聊天检索用的设备类型：显式 code 优先，否则根据型号推断；均无法识别则 None（走全量检索）。
    """
    if device_type_code and str(device_type_code).strip():
        c = str(device_type_code).strip()
        if c in DEVICE_TYPE_MAPPING.values():
            return c
        mapped = normalize_device_type_name(c)
        if mapped:
            return mapped
    if device_model and str(device_model).strip():
        return infer_device_type_from_model_or_label(str(device_model).strip())
    return None


def is_common_device_type(device_type_codes: List[str]) -> bool:
    """
    判断是否属于通用知识

    Args:
        device_type_codes: 设备类型标准码列表

    Returns:
        如果只包含COMMON或为空，返回True
    """
    if not device_type_codes:
        return True

    return all(code == "COMMON" for code in device_type_codes)


def format_device_types_for_display(device_type_codes: List[str]) -> str:
    """
    将设备类型标准码转换为友好的中文显示

    Args:
        device_type_codes: 设备类型标准码列表

    Returns:
        中文显示字符串
    """
    if not device_type_codes:
        return "通用"

    # 映射回中文
    chinese_names = []
    for code in device_type_codes:
        if code in DEVICE_TYPE_REVERSE_MAPPING:
            chinese_names.append(DEVICE_TYPE_REVERSE_MAPPING[code])
        else:
            chinese_names.append(code)

    # 去重
    chinese_names = list(set(chinese_names))

    if len(chinese_names) == 1:
        return chinese_names[0]
    else:
        return "、".join(chinese_names)


def extract_device_type_from_text(text: str) -> Optional[str]:
    """
    从文本中提取可能的设备类型（用于历史数据修复）

    Args:
        text: 要分析的文本（通常是标题或问题）

    Returns:
        最可能的设备类型标准码
    """
    if not text:
        return None

    text = text.lower()

    # 简单的关键词匹配
    if any(keyword in text for keyword in ["造型", "射砂", "震实", "起模"]):
        return "MOULDING_MACHINE"
    elif any(keyword in text for keyword in ["浇注", "保温", "熔炉", "液态"]):
        return "POURING_MACHINE"
    elif any(keyword in text for keyword in ["抛丸", "清理", "喷砂", "打磨"]):
        return "SHOT_BLAST_MACHINE"

    return None