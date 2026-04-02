"""QQ 平台通知事件数据模型"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import Field

from ..common.base import BaseEventData
from .enums import PostType, NoticeType, NotifySubType
from .misc import FileInfo

__all__ = [
    "NoticeEventData",
    "GroupUploadNoticeEventData",
    "GroupAdminNoticeEventData",
    "GroupDecreaseNoticeEventData",
    "GroupIncreaseNoticeEventData",
    "GroupBanNoticeEventData",
    "FriendAddNoticeEventData",
    "GroupRecallNoticeEventData",
    "FriendRecallNoticeEventData",
    "NotifyEventData",
    "PokeNotifyEventData",
    "LuckyKingNotifyEventData",
    "HonorNotifyEventData",
]


class NoticeEventData(BaseEventData):
    platform: str = "qq"
    post_type: PostType = Field(default=PostType.NOTICE)
    notice_type: NoticeType
    sub_type: NotifySubType
    group_id: Optional[str] = None
    user_id: Optional[str] = None


class GroupUploadNoticeEventData(NoticeEventData):
    notice_type: NoticeType = Field(default=NoticeType.GROUP_UPLOAD)
    file: FileInfo


class GroupAdminNoticeEventData(NoticeEventData):
    notice_type: NoticeType = Field(default=NoticeType.GROUP_ADMIN)
    sub_type: str = Field(default="set")


class GroupDecreaseNoticeEventData(NoticeEventData):
    notice_type: NoticeType = Field(default=NoticeType.GROUP_DECREASE)
    sub_type: str = Field(default="leave")
    operator_id: str


class GroupIncreaseNoticeEventData(NoticeEventData):
    notice_type: NoticeType = Field(default=NoticeType.GROUP_INCREASE)
    sub_type: str = Field(default="approve")
    operator_id: str


class GroupBanNoticeEventData(NoticeEventData):
    notice_type: NoticeType = Field(default=NoticeType.GROUP_BAN)
    sub_type: str = Field(default="ban")
    operator_id: str
    duration: int


class FriendAddNoticeEventData(NoticeEventData):
    notice_type: NoticeType = Field(default=NoticeType.FRIEND_ADD)


class GroupRecallNoticeEventData(NoticeEventData):
    notice_type: NoticeType = Field(default=NoticeType.GROUP_RECALL)
    operator_id: str
    message_id: str


class FriendRecallNoticeEventData(NoticeEventData):
    notice_type: NoticeType = Field(default=NoticeType.FRIEND_RECALL)
    message_id: str


# --- Notify 子类 ---


class NotifyEventData(NoticeEventData):
    notice_type: NoticeType = Field(default=NoticeType.NOTIFY)
    sub_type: str

    def resolve_type(self) -> str:
        """Notify 事件使用 sub_type 作为二级类型。"""
        sub = self.sub_type
        if hasattr(sub, "value"):
            sub = sub.value
        sub = str(sub) if sub else ""
        if sub:
            return f"notice.{sub.lower()}"
        return "notice.notify"


class PokeNotifyEventData(NotifyEventData):
    sub_type: str = Field(default=NotifySubType.POKE)
    target_id: str


class LuckyKingNotifyEventData(NotifyEventData):
    sub_type: str = Field(default=NotifySubType.LUCKY_KING)
    target_id: str


class HonorNotifyEventData(NotifyEventData):
    sub_type: str = Field(default=NotifySubType.HONOR)
    honor_type: Literal["talkative", "performer", "emotion"]
