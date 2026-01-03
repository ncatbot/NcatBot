"""
群成员管理 API

提供成员踢出、禁言、设置管理员、设置头衔等功能。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

from ..utils import APIComponent, APIReturnStatus

if TYPE_CHECKING:
    pass


# =============================================================================
# 成员管理 Mixin
# =============================================================================


class GroupMemberMixin(APIComponent):
    """群成员管理相关方法"""

    async def set_group_kick(
        self,
        group_id: Union[str, int],
        user_id: Union[str, int],
        reject_add_request: bool = False,
    ) -> None:
        """
        踢出群成员

        Args:
            group_id: 群号
            user_id: 要踢出的用户 QQ 号
            reject_add_request: 是否拒绝再次加群请求
        """
        result = await self._request_raw(
            "/set_group_kick",
            {
                "group_id": group_id,
                "user_id": user_id,
                "reject_add_request": reject_add_request,
            },
        )
        APIReturnStatus.raise_if_failed(result)

    async def set_group_ban(
        self,
        group_id: Union[str, int],
        user_id: Union[str, int],
        duration: int = 1800,
    ) -> None:
        """
        禁言群成员

        Args:
            group_id: 群号
            user_id: 要禁言的用户 QQ 号
            duration: 禁言时长（秒），0 表示取消禁言
        """
        result = await self._request_raw(
            "/set_group_ban",
            {"group_id": group_id, "user_id": user_id, "duration": duration},
        )
        APIReturnStatus.raise_if_failed(result)

    async def set_group_whole_ban(
        self, group_id: Union[str, int], enable: bool = True
    ) -> None:
        """
        设置全群禁言

        Args:
            group_id: 群号
            enable: True 开启禁言，False 关闭禁言
        """
        result = await self._request_raw(
            "/set_group_whole_ban",
            {"group_id": group_id, "enable": enable},
        )
        APIReturnStatus.raise_if_failed(result)

    async def set_group_admin(
        self,
        group_id: Union[str, int],
        user_id: Union[str, int],
        enable: bool = True,
    ) -> None:
        """
        设置群管理员

        Args:
            group_id: 群号
            user_id: 用户 QQ 号
            enable: True 设为管理员，False 取消管理员
        """
        result = await self._request_raw(
            "/set_group_admin",
            {"group_id": group_id, "user_id": user_id, "enable": enable},
        )
        APIReturnStatus.raise_if_failed(result)

    async def set_group_card(
        self,
        group_id: Union[str, int],
        user_id: Union[str, int],
        card: str = "",
    ) -> None:
        """
        设置群名片

        Args:
            group_id: 群号
            user_id: 用户 QQ 号
            card: 群名片内容（空字符串表示删除）
        """
        result = await self._request_raw(
            "/set_group_card",
            {"group_id": group_id, "user_id": user_id, "card": card},
        )
        APIReturnStatus.raise_if_failed(result)

    async def set_group_leave(
        self, group_id: Union[str, int], is_dismiss: bool = False
    ) -> None:
        """
        退出群聊

        Args:
            group_id: 群号
            is_dismiss: 是否解散群（仅群主）
        """
        result = await self._request_raw(
            "/set_group_leave",
            {"group_id": group_id, "is_dismiss": is_dismiss},
        )
        APIReturnStatus.raise_if_failed(result)

    async def set_group_special_title(
        self,
        group_id: Union[str, int],
        user_id: Union[str, int],
        special_title: str = "",
        duration: int = -1,
    ) -> None:
        """
        设置群头衔

        Args:
            group_id: 群号
            user_id: 用户 QQ 号
            special_title: 头衔内容
            duration: 有效期（秒），-1 表示永久
        """
        result = await self._request_raw(
            "/set_group_special_title",
            {
                "group_id": group_id,
                "user_id": user_id,
                "special_title": special_title,
                "duration": duration,
            },
        )
        APIReturnStatus.raise_if_failed(result)
