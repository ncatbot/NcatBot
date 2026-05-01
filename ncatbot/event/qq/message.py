"""QQ 消息事件实体"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, Union

from ncatbot.types import BaseSender, MessageArray, Image, Video
from ncatbot.types.qq import (
    MessageType,
    GroupMessageEventData,
    MessageEventData,
    PrivateMessageEventData,
    GroupSender,
    Anonymous,
)

from ..common.base import BaseEvent
from ..common.mixins import (
    Bannable,
    Deletable,
    GroupScoped,
    HasAttachments,
    HasSender,
    Kickable,
    Replyable,
)

if TYPE_CHECKING:
    from ncatbot.api.qq import QQAPIClient
    from ncatbot.types.common import Attachment, AttachmentList

__all__ = [
    "MessageEvent",
    "PrivateMessageEvent",
    "GroupMessageEvent",
]


class MessageEvent(BaseEvent, Replyable, Deletable, HasSender, HasAttachments):
    """QQ 消息事件实体"""

    _data: MessageEventData
    _api: QQAPIClient

    @property
    def api(self) -> QQAPIClient:
        return self._api

    @property
    def message_type(self) -> MessageType:
        return self._data.message_type

    @property
    def sub_type(self) -> str:
        return self._data.sub_type

    @property
    def message_id(self) -> str:
        return self._data.message_id

    @property
    def user_id(self) -> str:
        return self._data.user_id

    @property
    def message(self) -> MessageArray:
        return self._data.message

    @property
    def raw_message(self) -> str:
        return self._data.raw_message

    @property
    def sender(self) -> BaseSender:
        return self._data.sender

    @property
    def font(self) -> int:
        return self._data.font

    def is_group_msg(self) -> bool:
        return self._data.message_type is MessageType.GROUP

    async def reply(
        self,
        text: Optional[str] = None,
        *,
        at: Optional[Union[str, int]] = None,
        image: Optional[Union[str, Image]] = None,
        video: Optional[Union[str, Video]] = None,
        rtf: Optional[MessageArray] = None,
        at_sender: bool = True,
    ) -> Any:
        msg = MessageArray()
        msg.add_reply(self._data.message_id)
        if self._data.message_type is MessageType.GROUP and at_sender:
            msg.add_at(self._data.user_id)
            msg.add_text(" ")
        if text is not None:
            msg.add_text(text)
        if at is not None:
            if isinstance(at, bool):
                raise TypeError(
                    "reply(at=) 需要 (str | int) 类型, 不接受 bool, "
                    "如需控制是否 @发送者, 请使用 at_sender参数"
                )
            msg.add_at(at)
        if image is not None:
            msg.add_image(image)
        if video is not None:
            msg.add_video(video)
        if rtf is not None:
            msg = msg + rtf
        if self._data.message_type is MessageType.GROUP:
            return await self._api.post_group_array_msg(
                group_id=self._data.group_id,  # type: ignore[attr-defined]
                msg=msg,
            )
        return await self._api.post_private_array_msg(
            user_id=self._data.user_id,
            msg=msg,
        )

    async def delete(self) -> Any:
        return await self._api.messaging.delete_msg(message_id=self._data.message_id)

    async def get_attachments(self) -> "AttachmentList[Attachment]":
        return self._data.message.get_attachments()


class PrivateMessageEvent(MessageEvent):
    """QQ 私聊消息事件"""

    _data: PrivateMessageEventData


class GroupMessageEvent(MessageEvent, GroupScoped, Kickable, Bannable):
    """QQ 群消息事件"""

    _data: GroupMessageEventData

    @property
    def group_id(self) -> str:
        return self._data.group_id

    @property
    def group_name(self) -> Optional[str]:
        return self._data.group_name

    @property
    def anonymous(self) -> Optional[Anonymous]:
        return self._data.anonymous

    @property
    def sender(self) -> GroupSender:  # type: ignore[override]
        return self._data.sender

    async def kick(self, reject_add_request: bool = False) -> Any:
        return await self._api.manage.set_group_kick(
            self._data.group_id, self._data.user_id, reject_add_request
        )

    async def ban(self, duration: int = 30 * 60) -> Any:
        return await self._api.manage.set_group_ban(
            self._data.group_id, self._data.user_id, duration
        )
