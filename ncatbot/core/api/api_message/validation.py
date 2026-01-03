"""
消息验证工具

提供消息格式验证功能。
"""

from __future__ import annotations

from typing import List

from ..utils import get_log

LOG = get_log("ncatbot.core.api.api_message.validation")


# =============================================================================
# 消息验证
# =============================================================================


SINGLE_MSG_ONLY = (
    "music",
    "forward",
    "file",
    "record",
    "video",
    "rps",
    "dice",
    "share",
    "poke",
    "contact",
    "location",
)
"""只能单独发送的消息类型"""


def _validate_msg(msg: List[dict]) -> str:
    """
    验证消息格式是否合法（内部方法）

    Args:
        msg: 消息列表

    Returns:
        str: 验证结果，"OK" 表示通过，其他为错误信息
    """
    if len(msg) == 0:
        return "消息不能为空"
    if len(msg) != 1:
        types = [m["type"] for m in msg if m.get("type")]
        first_single = next((m for m in types if m in SINGLE_MSG_ONLY), None)
        if first_single:
            if any(m.get("reply") == "reply" for m in msg):
                return f"{first_single} 不允许通过回复发送"
            return f"{first_single} 不允许与其他消息混合发送"
    return "OK"


def validate_msg(msg: List[dict]) -> bool:
    """
    验证消息格式是否合法

    Args:
        msg: 消息列表

    Returns:
        bool: 是否合法
    """
    res = _validate_msg(msg)
    if res != "OK":
        LOG.error(f"消息格式验证失败: {res}")
    return res == "OK"
