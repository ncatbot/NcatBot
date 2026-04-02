"""QQ 通知事件实体"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal, Optional

from ncatbot.types.qq import (
    GroupAdminNoticeEventData,
    GroupBanNoticeEventData,
    GroupDecreaseNoticeEventData,
    GroupIncreaseNoticeEventData,
    GroupMsgEmojiLikeNoticeEventData,
    GroupRecallNoticeEventData,
    GroupUploadNoticeEventData,
    FriendAddNoticeEventData,
    FriendRecallNoticeEventData,
    NoticeEventData,
    NoticeType,
)
from ncatbot.types.qq import (
    EmojiLike,
    FileInfo,
    HonorNotifyEventData,
    LuckyKingNotifyEventData,
    NotifyEventData,
    PokeNotifyEventData,
)

from ..common.base import BaseEvent
from ..common.mixins import GroupScoped, HasSender, Kickable

if TYPE_CHECKING:
    from ncatbot.api.qq import QQAPIClient

__all__ = [
    "NoticeEvent",
    "GroupUploadEvent",
    "GroupAdminEvent",
    "GroupDecreaseEvent",
    "GroupIncreaseEvent",
    "GroupBanEvent",
    "FriendAddEvent",
    "GroupRecallEvent",
    "FriendRecallEvent",
    "GroupMsgEmojiLikeEvent",
    "NotifyEvent",
    "PokeNotifyEvent",
    "LuckyKingNotifyEvent",
    "HonorNotifyEvent",
]


class NoticeEvent(BaseEvent, HasSender, GroupScoped):
    """QQ 通知事件实体"""

    _data: NoticeEventData
    _api: QQAPIClient

    @property
    def api(self) -> QQAPIClient:
        return self._api

    @property
    def notice_type(self) -> NoticeType:
        return self._data.notice_type

    @property
    def group_id(self) -> Optional[str]:
        return self._data.group_id

    @property
    def user_id(self) -> Optional[str]:
        return self._data.user_id


class GroupUploadEvent(NoticeEvent):
    """QQ 群文件上传事件"""

    _data: GroupUploadNoticeEventData

    @property
    def file(self) -> FileInfo:
        return self._data.file


class GroupAdminEvent(NoticeEvent):
    """QQ 群管理员变动事件"""

    _data: GroupAdminNoticeEventData

    @property
    def sub_type(self) -> str:
        return self._data.sub_type


class GroupDecreaseEvent(NoticeEvent):
    """QQ 群成员减少事件"""

    _data: GroupDecreaseNoticeEventData

    @property
    def sub_type(self) -> str:
        return self._data.sub_type

    @property
    def operator_id(self) -> str:
        return self._data.operator_id


class GroupIncreaseEvent(NoticeEvent, Kickable):
    """QQ 群成员增加事件"""

    _data: GroupIncreaseNoticeEventData

    @property
    def sub_type(self) -> str:
        return self._data.sub_type

    @property
    def operator_id(self) -> str:
        return self._data.operator_id

    async def kick(self, reject_add_request: bool = False) -> Any:
        return await self._api.set_group_kick(
            self._data.group_id, self._data.user_id, reject_add_request
        )


class GroupBanEvent(NoticeEvent):
    """QQ 群禁言事件"""

    _data: GroupBanNoticeEventData

    @property
    def sub_type(self) -> str:
        return self._data.sub_type

    @property
    def operator_id(self) -> str:
        return self._data.operator_id

    @property
    def duration(self) -> int:
        return self._data.duration


class FriendAddEvent(NoticeEvent):
    """QQ 好友添加事件"""

    _data: FriendAddNoticeEventData


class GroupRecallEvent(NoticeEvent):
    """QQ 群消息撤回事件"""

    _data: GroupRecallNoticeEventData

    @property
    def operator_id(self) -> str:
        return self._data.operator_id

    @property
    def message_id(self) -> str:
        return self._data.message_id


class FriendRecallEvent(NoticeEvent):
    """QQ 好友消息撤回事件"""

    _data: FriendRecallNoticeEventData

    @property
    def message_id(self) -> str:
        return self._data.message_id


class GroupMsgEmojiLikeEvent(NoticeEvent):
    """QQ 群消息表情回应事件"""

    _data: GroupMsgEmojiLikeNoticeEventData

    @property
    def message_id(self) -> str:
        return self._data.message_id

    @property
    def likes(self) -> list[EmojiLike]:
        return self._data.likes

    @property
    def message_seq(self) -> int | None:
        return self._data.message_seq

    @property
    def is_add(self) -> bool | None:
        return self._data.is_add


# --- Notify 子类 ---


class NotifyEvent(NoticeEvent):
    """QQ Notify 通知事件基类"""

    _data: NotifyEventData

    @property
    def sub_type(self) -> str:
        return self._data.sub_type


class PokeNotifyEvent(NotifyEvent):
    """QQ 戳一戳事件"""

    _data: PokeNotifyEventData

    @property
    def target_id(self) -> str:
        return self._data.target_id


class LuckyKingNotifyEvent(NotifyEvent):
    """QQ 运气王事件"""

    _data: LuckyKingNotifyEventData

    @property
    def target_id(self) -> str:
        return self._data.target_id


class HonorNotifyEvent(NotifyEvent):
    """QQ 群荣誉事件"""

    _data: HonorNotifyEventData

    @property
    def honor_type(self) -> Literal["talkative", "performer", "emotion"]:
        return self._data.honor_type
