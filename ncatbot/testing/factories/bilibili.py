"""
Bilibili 事件工厂 — 快速构建测试用 B 站平台 BaseEventData 实例
"""

from __future__ import annotations

import time
from typing import Any, Optional

from ncatbot.types.bilibili.events import (
    DanmuMsgEventData,
    SuperChatEventData,
    GiftEventData,
    BiliPrivateMessageEventData,
    BiliCommentEventData,
    BiliDynamicEventData,
)


def _now() -> int:
    return int(time.time())


def danmu(
    text: str = "弹幕内容",
    *,
    room_id: str = "12345",
    user_id: str = "88888",
    user_name: str = "测试弹幕用户",
    **extra: Any,
) -> DanmuMsgEventData:
    """构造弹幕消息事件"""
    data = {
        "time": _now(),
        "self_id": "bili_bot",
        "platform": "bilibili",
        "post_type": "live",
        "live_event_type": "DANMU_MSG",
        "room_id": room_id,
        "user_id": user_id,
        "user_name": user_name,
        "message": [{"type": "text", "data": {"text": text}}],
        "sender": {"user_id": user_id, "nickname": user_name},
        **extra,
    }
    return DanmuMsgEventData.model_validate(data)


def super_chat(
    content: str = "SC 内容",
    price: int = 30,
    *,
    room_id: str = "12345",
    user_id: str = "88888",
    user_name: str = "SC 用户",
    duration: int = 60,
    **extra: Any,
) -> SuperChatEventData:
    """构造醒目留言事件"""
    data = {
        "time": _now(),
        "self_id": "bili_bot",
        "platform": "bilibili",
        "post_type": "live",
        "live_event_type": "SUPER_CHAT_MESSAGE",
        "room_id": room_id,
        "user_id": user_id,
        "user_name": user_name,
        "content": content,
        "price": price,
        "duration": duration,
        "sender": {"user_id": user_id, "nickname": user_name},
        **extra,
    }
    return SuperChatEventData.model_validate(data)


def gift(
    gift_name: str = "辣条",
    num: int = 1,
    *,
    room_id: str = "12345",
    user_id: str = "88888",
    user_name: str = "送礼用户",
    gift_id: str = "1",
    price: int = 100,
    coin_type: str = "silver",
    **extra: Any,
) -> GiftEventData:
    """构造礼物事件"""
    data = {
        "time": _now(),
        "self_id": "bili_bot",
        "platform": "bilibili",
        "post_type": "live",
        "live_event_type": "SEND_GIFT",
        "room_id": room_id,
        "user_id": user_id,
        "user_name": user_name,
        "gift_name": gift_name,
        "gift_id": gift_id,
        "num": num,
        "price": price,
        "coin_type": coin_type,
        "sender": {"user_id": user_id, "nickname": user_name},
        **extra,
    }
    return GiftEventData.model_validate(data)


def private_message(
    text: str = "私信内容",
    *,
    user_id: str = "88888",
    user_name: str = "私信用户",
    **extra: Any,
) -> BiliPrivateMessageEventData:
    """构造 B 站私信消息事件"""
    data = {
        "time": _now(),
        "self_id": "bili_bot",
        "platform": "bilibili",
        "post_type": "message",
        "message_type": "private",
        "user_id": user_id,
        "user_name": user_name,
        "message": [{"type": "text", "data": {"text": text}}],
        "sender": {"user_id": user_id, "nickname": user_name},
        **extra,
    }
    return BiliPrivateMessageEventData.model_validate(data)


def comment(
    content: str = "评论内容",
    *,
    resource_id: str = "BV1234",
    resource_type: str = "video",
    comment_id: str = "c_001",
    user_id: str = "88888",
    user_name: str = "评论用户",
    **extra: Any,
) -> BiliCommentEventData:
    """构造评论事件"""
    data = {
        "time": _now(),
        "self_id": "bili_bot",
        "platform": "bilibili",
        "post_type": "comment",
        "comment_event_type": "NEW_REPLY",
        "resource_id": resource_id,
        "resource_type": resource_type,
        "comment_id": comment_id,
        "user_id": user_id,
        "user_name": user_name,
        "content": content,
        "sender": {"user_id": user_id, "nickname": user_name},
        **extra,
    }
    return BiliCommentEventData.model_validate(data)


def dynamic(
    text: Optional[str] = "动态内容",
    *,
    uid: str = "88888",
    user_name: str = "动态用户",
    dynamic_id: str = "dyn_001",
    dynamic_type: str = "DYNAMIC_TYPE_WORD",
    **extra: Any,
) -> BiliDynamicEventData:
    """构造动态事件"""
    data = {
        "time": _now(),
        "self_id": "bili_bot",
        "platform": "bilibili",
        "post_type": "dynamic",
        "dynamic_event_type": "NEW_DYNAMIC",
        "dynamic_status": "new",
        "dynamic_id": dynamic_id,
        "dynamic_type": dynamic_type,
        "uid": uid,
        "user_name": user_name,
        "text": text,
        "sender": {"user_id": uid, "nickname": user_name},
        **extra,
    }
    return BiliDynamicEventData.model_validate(data)
