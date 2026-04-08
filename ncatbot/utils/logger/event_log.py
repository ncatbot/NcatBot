"""事件日志级别解析。"""

import json
import logging
from typing import Dict, Optional


def resolve_event_log_level(
    event_type: str,
    overrides: Dict[str, str],
) -> Optional[int]:
    """根据事件类型字符串和配置覆盖表，返回应使用的日志级别。

    匹配策略：精确匹配优先 → 前缀匹配（如 ``"meta_event"`` 匹配
    ``"meta_event.heartbeat"``）。无匹配时返回 ``logging.INFO``。

    Args:
        event_type: 事件类型字符串，如 ``"meta_event.heartbeat"``。
        overrides:  配置映射，键为事件类型（前缀），值为级别字符串。
                    值已由 Pydantic 验证器归一化为大写。

    Returns:
        日志级别整数值，``None`` 表示不记录（对应 ``"NONE"``）。
    """
    if not overrides:
        return logging.INFO

    # 精确匹配
    if event_type in overrides:
        return _to_level(overrides[event_type])

    # 前缀匹配：按键长度降序，取最长匹配
    best: Optional[str] = None
    for key in overrides:
        if event_type.startswith(key + ".") or event_type == key:
            if best is None or len(key) > len(best):
                best = key
    if best is not None:
        return _to_level(overrides[best])

    return logging.INFO


def _to_level(level_str: str) -> Optional[int]:
    """将级别字符串转换为 logging 整数值，'NONE' 返回 None。"""
    if level_str == "NONE":
        return None
    return getattr(logging, level_str, logging.INFO)


def format_event_summary(raw_data: dict) -> str:
    """将原始事件数据格式化为人类可读摘要。

    根据 ``post_type`` 分发到不同格式模板。字段缺失时优雅降级。
    输入为 dict 而非数据模型，以保持对平台的通用性。

    Args:
        raw_data: 原始事件字典，至少包含 ``post_type`` 键。

    Returns:
        格式化后的摘要字符串。
    """
    post_type = raw_data.get("post_type", "")

    if post_type in ("message", "message_sent"):
        return _format_message(raw_data)
    if post_type == "notice":
        return _format_notice(raw_data)
    if post_type == "request":
        return _format_request(raw_data)
    if post_type == "meta_event":
        return _format_meta(raw_data)

    # 未知事件类型降级

    preview = json.dumps(raw_data, ensure_ascii=False)
    if len(preview) > 200:
        preview = preview[:200] + "..."
    return f"[事件] {post_type}: {preview}"


def _format_message(data: dict) -> str:
    message_type = data.get("message_type", "")
    sender = data.get("sender") or {}
    nickname = sender.get("nickname") or ""
    user_id = data.get("user_id", "")
    raw_message = data.get("raw_message", "")

    if len(raw_message) > 100:
        raw_message = raw_message[:100] + "..."

    if message_type == "group":
        group_id = data.get("group_id", "")
        group_name = data.get("group_name", "")
        if group_name:
            group_part = f"{group_name}({group_id})"
        else:
            group_part = group_id
        if nickname:
            user_part = f"{nickname}({user_id})"
        else:
            user_part = user_id
        return f"[群消息] {group_part} {user_part}: {raw_message}"

    # private 或其他
    if nickname:
        user_part = f"{nickname}({user_id})"
    else:
        user_part = user_id
    return f"[私聊消息] {user_part}: {raw_message}"


def _format_notice(data: dict) -> str:
    notice_type = data.get("notice_type", "unknown")
    sub_type = data.get("sub_type")
    if sub_type:
        notice_type = f"{notice_type}.{sub_type}"

    group_id = data.get("group_id")
    user_id = data.get("user_id", "")

    parts = [f"[通知] {notice_type}"]
    if group_id:
        parts.append(f"群:{group_id}")
    parts.append(f"用户:{user_id}")
    return " ".join(parts)


def _format_request(data: dict) -> str:
    request_type = data.get("request_type", "unknown")
    user_id = data.get("user_id", "")
    group_id = data.get("group_id")

    parts = [f"[请求] {request_type}"]
    if group_id:
        parts.append(f"群:{group_id}")
    parts.append(f"用户:{user_id}")
    return " ".join(parts)


def _format_meta(data: dict) -> str:
    meta_type = data.get("meta_event_type", "unknown")
    return f"[元事件] {meta_type}"
