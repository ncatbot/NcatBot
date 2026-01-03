"""
私聊音乐消息发送 API

提供私聊音乐分享等特殊消息功能。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal, Optional, Union

from ..utils import (
    APIComponent,
    APIReturnStatus,
    MessageAPIReturnStatus,
)

if TYPE_CHECKING:
    pass


# =============================================================================
# 私聊音乐消息 Mixin
# =============================================================================


class PrivateMusicMixin(APIComponent):
    """私聊音乐消息和特殊消息相关方法"""

    async def send_private_music(
        self,
        user_id: Union[str, int],
        type: Literal["qq", "163"],
        id: Union[int, str],
    ) -> str:
        """
        发送私聊音乐分享

        Args:
            user_id: 用户 QQ 号
            type: 音乐平台 ("qq", "163")
            id: 音乐 ID

        Returns:
            str: 消息 ID
        """
        from ncatbot.core import Music

        music = Music(type=type, id=id)
        result = await self._request_raw(
            "/send_private_msg",
            {"user_id": user_id, "message": [music.to_dict()]},
        )
        status = MessageAPIReturnStatus(result)
        return status.message_id

    async def send_private_custom_music(
        self,
        user_id: Union[str, int],
        url: str,
        title: str,
        image: str,
        audio: Optional[str] = None,
        content: Optional[str] = None,
    ) -> str:
        """
        发送私聊自定义音乐分享

        Args:
            user_id: 用户 QQ 号
            url: 跳转链接
            title: 标题
            image: 封面图片
            audio: 音频链接
            content: 描述内容

        Returns:
            str: 消息 ID
        """
        from ncatbot.core import Music

        music = Music(
            type="custom",
            id=None,
            url=url,
            audio=audio,
            title=title,
            content=content,
            image=image,
        )
        result = await self._request_raw(
            "/send_private_msg",
            {"user_id": user_id, "message": [music.to_dict()]},
        )
        status = MessageAPIReturnStatus(result)
        return status.message_id

    async def friend_poke(self, user_id: Union[str, int]) -> None:
        """
        好友戳一戳

        Args:
            user_id: 目标用户 QQ 号
        """
        result = await self._request_raw(
            "/friend_poke",
            {"user_id": user_id},
        )
        APIReturnStatus.raise_if_failed(result)
