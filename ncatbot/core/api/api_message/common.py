"""
通用消息操作 API

提供消息的删除、贴表情、戳一戳等通用操作功能。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Union

from ..utils import APIComponent, APIReturnStatus
from ncatbot.utils import NcatBotValueError

if TYPE_CHECKING:
    pass


# =============================================================================
# 通用消息操作 Mixin
# =============================================================================


class CommonMessageMixin(APIComponent):
    """通用消息操作相关方法"""

    async def send_poke(
        self,
        user_id: Union[str, int],
        group_id: Optional[Union[str, int]] = None,
    ) -> None:
        """
        发送戳一戳

        Args:
            user_id: 目标用户 QQ 号
            group_id: 群号（提供则在群内戳，否则私聊戳）
        """
        if not user_id:
            raise NcatBotValueError("user_id", user_id, must_be=False)

        if group_id:
            result = await self._request_raw(
                "/group_poke",
                {"group_id": group_id, "user_id": user_id},
            )
        else:
            result = await self._request_raw(
                "/friend_poke",
                {"user_id": user_id},
            )
        APIReturnStatus.raise_if_failed(result)

    async def delete_msg(self, message_id: Union[str, int]) -> None:
        """
        撤回/删除消息

        Args:
            message_id: 消息 ID
        """
        result = await self._request_raw(
            "/delete_msg",
            {"message_id": message_id},
        )
        APIReturnStatus.raise_if_failed(result)

    async def set_msg_emoji_like(
        self,
        message_id: Union[str, int],
        emoji_id: Union[str, int],
        set: bool = True,
    ) -> None:
        """
        消息贴表情

        Args:
            message_id: 消息 ID
            emoji_id: 表情 ID
            set: True 贴表情，False 取消
        """
        result = await self._request_raw(
            "/set_msg_emoji_like",
            {
                "message_id": str(message_id),
                "emoji_id": int(emoji_id),
                "set": set,
            },
        )
        APIReturnStatus.raise_if_failed(result)

    async def forward_group_single_msg(
        self,
        group_id: Union[str, int],
        message_id: Union[str, int],
    ) -> None:
        """
        向群转发单条消息

        Args:
            group_id: 群号
            message_id: 消息 ID
        """
        result = await self._request_raw(
            "/forward_group_single_msg",
            {"group_id": group_id, "message_id": message_id},
        )
        APIReturnStatus.raise_if_failed(result)

    async def forward_private_single_msg(
        self,
        user_id: Union[str, int],
        message_id: Union[str, int],
    ) -> None:
        """
        向私聊转发单条消息

        Args:
            user_id: 用户 QQ 号
            message_id: 消息 ID
        """
        result = await self._request_raw(
            "/forward_private_single_msg",
            {"user_id": user_id, "message_id": message_id},
        )
        APIReturnStatus.raise_if_failed(result)
