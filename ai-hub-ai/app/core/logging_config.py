"""
日志配置
统一配置应用日志格式与级别
"""
import logging
import sys
from typing import Optional


def setup_logging(
    level: int = logging.INFO,
    format_string: Optional[str] = None,
) -> None:
    """
    初始化根日志配置
    :param level: 日志级别
    :param format_string: 格式串，默认带时间、模块、级别、消息
    """
    if format_string is None:
        format_string = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"

    # 避免重复添加 handler
    root = logging.getLogger()
    if root.handlers:
        return

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    formatter = logging.Formatter(format_string, datefmt="%Y-%m-%d %H:%M:%S")
    handler.setFormatter(formatter)
    root.addHandler(handler)
    root.setLevel(level)


def get_logger(name: str) -> logging.Logger:
    """获取指定名称的 Logger"""
    return logging.getLogger(name)
