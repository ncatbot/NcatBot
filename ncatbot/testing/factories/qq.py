"""
QQ 事件工厂 — 快速构建测试用 QQ 平台 BaseEventData 实例

所有 factory 方法产出经过 model_validate 的合法数据模型，
可直接喂入 TestHarness.inject()。
"""

from __future__ import annotations

import time
from itertools import count
from typing import Any, Dict, List, Optional

from ncatbot.types.qq import (
    GroupMessageEventData,
    PrivateMessageEventData,
    FriendRequestEventData,
    GroupRequestEventData,
    GroupIncreaseNoticeEventData,
    GroupDecreaseNoticeEventData,
    GroupBanNoticeEventData,
    GroupMsgEmojiLikeNoticeEventData,
    GroupUploadNoticeEventData,
    GroupAdminNoticeEventData,
    FriendAddNoticeEventData,
    GroupRecallNoticeEventData,
    FriendRecallNoticeEventData,
)
from ncatbot.types.qq import (
    PokeNotifyEventData,
    LuckyKingNotifyEventData,
    HonorNotifyEventData,
)

_msg_id_counter = count(1)
_SELF_ID = "10001"


def _next_msg_id() -> str:
    return str(next(_msg_id_counter))


def _now() -> int:
    return int(time.time())


def _text_segments(text: str) -> List[Dict[str, Any]]:
    return [{"type": "text", "data": {"text": text}}]


def group_message(
    text: str = "hello",
    *,
    group_id: str = "100200",
    user_id: str = "99999",
    nickname: str = "测试用户",
    message_id: Optional[str] = None,
    self_id: str = _SELF_ID,
    message: Optional[list] = None,
    raw_message: Optional[str] = None,
    sub_type: str = "normal",
    **extra: Any,
) -> GroupMessageEventData:
    """构造群消息事件"""
    data = {
        "time": _now(),
        "self_id": self_id,
        "platform": "qq",
        "post_type": "message",
        "message_type": "group",
        "sub_type": sub_type,
        "message_id": message_id or _next_msg_id(),
        "group_id": group_id,
        "user_id": user_id,
        "message": message or _text_segments(text),
        "raw_message": raw_message or text,
        "font": 0,
        "sender": {
            "user_id": user_id,
            "nickname": nickname,
            "card": nickname,
            "role": "member",
        },
        **extra,
    }
    return GroupMessageEventData.model_validate(data)


def private_message(
    text: str = "hello",
    *,
    user_id: str = "99999",
    nickname: str = "测试用户",
    message_id: Optional[str] = None,
    self_id: str = _SELF_ID,
    message: Optional[list] = None,
    raw_message: Optional[str] = None,
    sub_type: str = "friend",
    **extra: Any,
) -> PrivateMessageEventData:
    """构造私聊消息事件"""
    data = {
        "time": _now(),
        "self_id": self_id,
        "platform": "qq",
        "post_type": "message",
        "message_type": "private",
        "sub_type": sub_type,
        "message_id": message_id or _next_msg_id(),
        "user_id": user_id,
        "message": message or _text_segments(text),
        "raw_message": raw_message or text,
        "font": 0,
        "sender": {
            "user_id": user_id,
            "nickname": nickname,
        },
        **extra,
    }
    return PrivateMessageEventData.model_validate(data)


def friend_request(
    user_id: str = "99999",
    comment: str = "请求加好友",
    flag: str = "flag_123",
    *,
    self_id: str = _SELF_ID,
    **extra: Any,
) -> FriendRequestEventData:
    """构造好友请求事件"""
    data = {
        "time": _now(),
        "self_id": self_id,
        "platform": "qq",
        "post_type": "request",
        "request_type": "friend",
        "user_id": user_id,
        "comment": comment,
        "flag": flag,
        **extra,
    }
    return FriendRequestEventData.model_validate(data)


def group_request(
    user_id: str = "99999",
    group_id: str = "100200",
    comment: str = "请求加群",
    flag: str = "flag_456",
    sub_type: str = "add",
    *,
    self_id: str = _SELF_ID,
    **extra: Any,
) -> GroupRequestEventData:
    """构造加群请求事件"""
    data = {
        "time": _now(),
        "self_id": self_id,
        "platform": "qq",
        "post_type": "request",
        "request_type": "group",
        "sub_type": sub_type,
        "group_id": group_id,
        "user_id": user_id,
        "comment": comment,
        "flag": flag,
        **extra,
    }
    return GroupRequestEventData.model_validate(data)


def napcat_comment(answer: str, question: str = "问题") -> str:
    """构造 NapCat 格式的 comment 字符串。

    NapCat 适配器下 event.comment 的实际格式为 ``问题：xxx\\n答案：yyy``，
    而非纯答案文本。此函数用于在测试中快捷构造该格式。
    """
    return f"问题：{question}\n答案：{answer}"


def group_increase(
    user_id: str = "99999",
    group_id: str = "100200",
    operator_id: str = "10001",
    sub_type: str = "approve",
    *,
    self_id: str = _SELF_ID,
    **extra: Any,
) -> GroupIncreaseNoticeEventData:
    """构造群成员增加通知"""
    data = {
        "time": _now(),
        "self_id": self_id,
        "platform": "qq",
        "post_type": "notice",
        "notice_type": "group_increase",
        "sub_type": sub_type,
        "group_id": group_id,
        "operator_id": operator_id,
        "user_id": user_id,
        **extra,
    }
    return GroupIncreaseNoticeEventData.model_validate(data)


def group_decrease(
    user_id: str = "99999",
    group_id: str = "100200",
    operator_id: str = "10001",
    sub_type: str = "kick",
    *,
    self_id: str = _SELF_ID,
    **extra: Any,
) -> GroupDecreaseNoticeEventData:
    """构造群成员减少通知"""
    data = {
        "time": _now(),
        "self_id": self_id,
        "platform": "qq",
        "post_type": "notice",
        "notice_type": "group_decrease",
        "sub_type": sub_type,
        "group_id": group_id,
        "operator_id": operator_id,
        "user_id": user_id,
        **extra,
    }
    return GroupDecreaseNoticeEventData.model_validate(data)


def group_ban(
    user_id: str = "99999",
    group_id: str = "100200",
    operator_id: str = "10001",
    duration: int = 600,
    sub_type: str = "ban",
    *,
    self_id: str = _SELF_ID,
    **extra: Any,
) -> GroupBanNoticeEventData:
    """构造群禁言通知"""
    data = {
        "time": _now(),
        "self_id": self_id,
        "platform": "qq",
        "post_type": "notice",
        "notice_type": "group_ban",
        "sub_type": sub_type,
        "group_id": group_id,
        "operator_id": operator_id,
        "user_id": user_id,
        "duration": duration,
        **extra,
    }
    return GroupBanNoticeEventData.model_validate(data)


def group_msg_emoji_like(
    user_id: str = "99999",
    group_id: str = "100200",
    message_id: Optional[str] = None,
    likes: Optional[List[Dict[str, Any]]] = None,
    is_add: bool = True,
    message_seq: Optional[int] = None,
    *,
    self_id: str = _SELF_ID,
    **extra: Any,
) -> GroupMsgEmojiLikeNoticeEventData:
    """构造群消息表情回应通知"""
    data = {
        "time": _now(),
        "self_id": self_id,
        "platform": "qq",
        "post_type": "notice",
        "notice_type": "group_msg_emoji_like",
        "group_id": group_id,
        "user_id": user_id,
        "message_id": message_id or _next_msg_id(),
        "likes": likes or [{"emoji_id": "128077", "count": 1}],
        "is_add": is_add,
        "message_seq": message_seq,
        **extra,
    }
    return GroupMsgEmojiLikeNoticeEventData.model_validate(data)


def poke(
    user_id: str = "99999",
    target_id: str = "10001",
    group_id: str = "100200",
    *,
    self_id: str = _SELF_ID,
    **extra: Any,
) -> PokeNotifyEventData:
    """构造戳一戳通知"""
    data = {
        "time": _now(),
        "self_id": self_id,
        "platform": "qq",
        "post_type": "notice",
        "notice_type": "notify",
        "sub_type": "poke",
        "group_id": group_id,
        "user_id": user_id,
        "target_id": target_id,
        **extra,
    }
    return PokeNotifyEventData.model_validate(data)


def group_upload(
    user_id: str = "99999",
    group_id: str = "100200",
    *,
    file_id: str = "file_001",
    file_name: str = "test.txt",
    file_size: int = 1024,
    busid: int = 0,
    self_id: str = _SELF_ID,
    **extra: Any,
) -> GroupUploadNoticeEventData:
    """构造群文件上传通知"""
    data = {
        "time": _now(),
        "self_id": self_id,
        "platform": "qq",
        "post_type": "notice",
        "notice_type": "group_upload",
        "group_id": group_id,
        "user_id": user_id,
        "file": {
            "id": file_id,
            "name": file_name,
            "size": file_size,
            "busid": busid,
        },
        **extra,
    }
    return GroupUploadNoticeEventData.model_validate(data)


def group_admin(
    user_id: str = "99999",
    group_id: str = "100200",
    sub_type: str = "set",
    *,
    self_id: str = _SELF_ID,
    **extra: Any,
) -> GroupAdminNoticeEventData:
    """构造群管理员变动通知"""
    data = {
        "time": _now(),
        "self_id": self_id,
        "platform": "qq",
        "post_type": "notice",
        "notice_type": "group_admin",
        "sub_type": sub_type,
        "group_id": group_id,
        "user_id": user_id,
        **extra,
    }
    return GroupAdminNoticeEventData.model_validate(data)


def friend_add(
    user_id: str = "99999",
    *,
    self_id: str = _SELF_ID,
    **extra: Any,
) -> FriendAddNoticeEventData:
    """构造好友添加通知"""
    data = {
        "time": _now(),
        "self_id": self_id,
        "platform": "qq",
        "post_type": "notice",
        "notice_type": "friend_add",
        "user_id": user_id,
        **extra,
    }
    return FriendAddNoticeEventData.model_validate(data)


def group_recall(
    user_id: str = "99999",
    group_id: str = "100200",
    operator_id: str = "10001",
    message_id: Optional[str] = None,
    *,
    self_id: str = _SELF_ID,
    **extra: Any,
) -> GroupRecallNoticeEventData:
    """构造群消息撤回通知"""
    data = {
        "time": _now(),
        "self_id": self_id,
        "platform": "qq",
        "post_type": "notice",
        "notice_type": "group_recall",
        "group_id": group_id,
        "user_id": user_id,
        "operator_id": operator_id,
        "message_id": message_id or _next_msg_id(),
        **extra,
    }
    return GroupRecallNoticeEventData.model_validate(data)


def friend_recall(
    user_id: str = "99999",
    message_id: Optional[str] = None,
    *,
    self_id: str = _SELF_ID,
    **extra: Any,
) -> FriendRecallNoticeEventData:
    """构造好友消息撤回通知"""
    data = {
        "time": _now(),
        "self_id": self_id,
        "platform": "qq",
        "post_type": "notice",
        "notice_type": "friend_recall",
        "user_id": user_id,
        "message_id": message_id or _next_msg_id(),
        **extra,
    }
    return FriendRecallNoticeEventData.model_validate(data)


def lucky_king(
    user_id: str = "99999",
    target_id: str = "88888",
    group_id: str = "100200",
    *,
    self_id: str = _SELF_ID,
    **extra: Any,
) -> LuckyKingNotifyEventData:
    """构造运气王通知"""
    data = {
        "time": _now(),
        "self_id": self_id,
        "platform": "qq",
        "post_type": "notice",
        "notice_type": "notify",
        "sub_type": "lucky_king",
        "group_id": group_id,
        "user_id": user_id,
        "target_id": target_id,
        **extra,
    }
    return LuckyKingNotifyEventData.model_validate(data)


def honor(
    user_id: str = "99999",
    group_id: str = "100200",
    honor_type: str = "talkative",
    *,
    self_id: str = _SELF_ID,
    **extra: Any,
) -> HonorNotifyEventData:
    """构造群荣誉变更通知"""
    data = {
        "time": _now(),
        "self_id": self_id,
        "platform": "qq",
        "post_type": "notice",
        "notice_type": "notify",
        "sub_type": "honor",
        "group_id": group_id,
        "user_id": user_id,
        "honor_type": honor_type,
        **extra,
    }
    return HonorNotifyEventData.model_validate(data)
