"""
群音乐消息发送 API

提供群音乐分享和戳一戳等特殊消息功能。
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
# 群音乐消息 Mixin
# =============================================================================


class GroupMusicMixin(APIComponent):
    """群音乐消息和特殊消息相关方法"""

    async def send_group_music(
        self,
        group_id: Union[str, int],
        type: Literal["qq", "163"],
        id: Union[int, str],
    ) -> str:
        """
        发送群音乐分享

        Args:
            group_id: 群号
            type: 音乐平台 ("qq", "163")
            id: 音乐 ID

        Returns:
            str: 消息 ID
        """
        from ncatbot.core import Music

        music = Music(platform=type, id=str(id))
        result = await self._request_raw(
            "/send_group_msg",
            {"group_id": group_id, "message": [music.to_dict()]},
        )
        status = MessageAPIReturnStatus(result)
        return status.message_id

    async def send_group_custom_music(
        self,
        group_id: Union[str, int],
        url: str,
        title: str,
        image: str,
        audio: Optional[str] = None,
        content: Optional[str] = None,
    ) -> str:
        """
        发送群自定义音乐分享

        Args:
            group_id: 群号
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
            platform="custom",
            id=None,
            url=url,
            audio=audio,
            title=title,
            content=content,
            image=image,
        )
        result = await self._request_raw(
            "/send_group_msg",
            {"group_id": group_id, "message": [music.to_dict()]},
        )
        status = MessageAPIReturnStatus(result)
        return status.message_id

    async def group_poke(
        self,
        group_id: Union[str, int],
        user_id: Union[str, int],
    ) -> None:
        """
        群内戳一戳

        Args:
            group_id: 群号
            user_id: 目标用户 QQ 号
        """
        result = await self._request_raw(
            "/group_poke",
            {"group_id": group_id, "user_id": user_id},
        )
        APIReturnStatus.raise_if_failed(result)
