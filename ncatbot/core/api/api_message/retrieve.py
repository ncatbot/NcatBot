"""
消息获取 API

提供消息历史记录、消息详情、媒体文件获取等功能。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Literal, Optional, Union

from ..utils import APIComponent, APIReturnStatus, check_exclusive_argument

if TYPE_CHECKING:
    from ..client import IAPIClient
    from ncatbot.core import (
        GroupMessageEvent,
        PrivateMessageEvent,
        MessageEvent,
        Forward,
        Record,
        Image,
    )


# =============================================================================
# 消息获取 Mixin
# =============================================================================


class MessageRetrieveMixin(APIComponent):
    """消息获取相关方法"""

    async def get_group_msg_history(
        self,
        group_id: Union[str, int],
        message_seq: Optional[Union[str, int]] = None,
        count: int = 20,
        reverse_order: bool = False,
    ) -> List["GroupMessageEvent"]:
        """
        获取群消息历史

        Args:
            group_id: 群号
            message_seq: 起始消息序号
            count: 获取数量
            reverse_order: 是否倒序

        Returns:
            List[GroupMessageEvent]: 消息列表
        """
        from ncatbot.core import GroupMessageEvent

        data = {
            "group_id": group_id,
            "count": count,
            "reverseOrder": reverse_order,
        }
        if message_seq is not None:
            data["message_seq"] = message_seq

        result = await self._request_raw("/get_group_msg_history", data)
        status = APIReturnStatus(result)
        return [GroupMessageEvent(**data) for data in status.data.get("messages", [])]

    async def get_msg(self, message_id: Union[str, int]) -> "MessageEvent":
        """
        获取消息详情

        Args:
            message_id: 消息 ID

        Returns:
            MessageEvent: 消息事件对象
        """
        from ncatbot.core import GroupMessageEvent, PrivateMessageEvent

        result = await self._request_raw(
            "/get_msg",
            {"message_id": message_id},
        )
        status = APIReturnStatus(result)
        data = status.data
        
        # 根据 message_type 选择正确的事件类型
        if data.get("message_type") == "private":
            return PrivateMessageEvent(**data)
        return GroupMessageEvent(**data)

    async def get_forward_msg(self, message_id: Union[str, int]) -> "Forward":
        """
        获取合并转发消息内容

        Args:
            message_id: 消息 ID

        Returns:
            Forward: 合并转发消息对象
        """
        from ncatbot.core import Forward

        result = await self._request_raw(
            "/get_forward_msg",
            {"message_id": message_id},
        )
        status = APIReturnStatus(result)
        return Forward.from_dict({"type": "forward", "data": {"id": str(message_id), "content": status.data.get("messages")}})

    async def get_friend_msg_history(
        self,
        user_id: Union[str, int],
        message_seq: Union[str, int],
        count: int = 20,
        reverse_order: bool = False,
    ) -> List["PrivateMessageEvent"]:
        """
        获取好友消息历史

        Args:
            user_id: 用户 QQ 号
            message_seq: 起始消息序号
            count: 获取数量
            reverse_order: 是否倒序

        Returns:
            List[PrivateMessageEvent]: 消息列表
        """
        from ncatbot.core import PrivateMessageEvent

        result = await self._request_raw(
            "/get_friend_msg_history",
            {
                "user_id": user_id,
                "message_seq": message_seq,
                "count": count,
                "reverseOrder": reverse_order,
            },
        )
        status = APIReturnStatus(result)
        # 处理 post_type='message_sent' (历史消息可能返回此值)
        messages = []
        for data in status.data.get("messages", []):
            if data.get("post_type") == "message_sent":
                data["post_type"] = "message"
            messages.append(PrivateMessageEvent(**data))
        return messages

    async def get_record(
        self,
        file: Optional[str] = None,
        file_id: Optional[str] = None,
        out_format: Literal[
            "mp3", "amr", "wma", "m4a", "ogg", "wav", "flac", "spx"
        ] = "mp3",
    ) -> "Record":
        """
        获取语音文件

        Args:
            file: 文件标识（与 file_id 二选一）
            file_id: 文件 ID（与 file 二选一）
            out_format: 输出格式

        Returns:
            Record: 语音消息段对象
        """
        from ncatbot.core import Record

        check_exclusive_argument(file, file_id, names=["file", "file_id"])
        result = await self._request_raw(
            "/get_record",
            {"file": file, "file_id": file_id, "out_format": out_format},
        )
        status = APIReturnStatus(result)
        segment = Record.from_dict({"type": "record", "data": status.data})
        return segment  # type: ignore

    async def get_image(
        self,
        file: Optional[str] = None,
        file_id: Optional[str] = None,
    ) -> "Image":
        """
        获取图片文件

        Args:
            file: 文件标识（与 file_id 二选一）
            file_id: 文件 ID（与 file 二选一）

        Returns:
            Image: 图片消息段对象
        """
        from ncatbot.core import Image

        check_exclusive_argument(file, file_id, names=["file", "file_id"])
        result = await self._request_raw(
            "/get_image",
            {"file": file, "file_id": file_id},
        )
        status = APIReturnStatus(result)
        segment = Image.from_dict({"type": "image", "data": status.data})
        return segment  # type: ignore

    async def fetch_emoji_like(
        self,
        message_id: Union[str, int],
        emoji_id: Union[str, int],
        emoji_type: Union[str, int],
    ) -> dict:
        """
        获取贴表情详情

        Args:
            message_id: 消息 ID
            emoji_id: 表情 ID
            emoji_type: 表情类型

        Returns:
            dict: 表情详情
        """
        result = await self._request_raw(
            "/fetch_emoji_like",
            {
                "message_id": message_id,
                "emojiId": emoji_id,
                "emojiType": emoji_type,
            },
        )
        status = APIReturnStatus(result)
        return status.data
