"""
群信息查询 API

提供群信息、成员信息、荣誉信息、精华消息等查询功能。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Literal, Union

from ..utils import APIComponent, APIReturnStatus

if TYPE_CHECKING:
    pass

from .models import (
    EssenceMessage,
    GroupChatActivity,
    GroupInfo,
    GroupMemberInfo,
    GroupMemberList,
)


# =============================================================================
# 信息查询 Mixin
# =============================================================================


class GroupInfoMixin(APIComponent):
    """群信息查询相关方法"""

    # -------------------------------------------------------------------------
    # 精华消息
    # -------------------------------------------------------------------------

    async def set_essence_msg(self, message_id: Union[str, int]) -> None:
        """
        设置精华消息

        Args:
            message_id: 消息 ID
        """
        result = await self._request_raw(
            "/set_essence_msg",
            {"message_id": message_id},
        )
        APIReturnStatus.raise_if_failed(result)

    async def delete_essence_msg(self, message_id: Union[str, int]) -> None:
        """
        删除精华消息

        Args:
            message_id: 消息 ID
        """
        result = await self._request_raw(
            "/delete_essence_msg",
            {"message_id": message_id},
        )
        APIReturnStatus.raise_if_failed(result)

    async def get_essence_msg_list(
        self, group_id: Union[str, int]
    ) -> List[EssenceMessage]:
        """
        获取精华消息列表

        .. warning::
            此 API 在某些群可能会返回错误（NapCat 服务端 bug），
            例如 ``Cannot read properties of undefined (reading 'msg_seq')``。
            如果群内没有精华消息，则返回空列表。

        Args:
            group_id: 群号

        Returns:
            List[EssenceMessage]: 精华消息列表

        Raises:
            NapCatAPIError: 如果 NapCat 处理此群的精华消息时出错
        """
        result = await self._request_raw(
            "/get_essence_msg_list",
            {"group_id": group_id},
        )
        status = APIReturnStatus(result)
        return [EssenceMessage(**msg) for msg in status.data]

    # -------------------------------------------------------------------------
    # 群荣誉信息
    # -------------------------------------------------------------------------

    async def get_group_honor_info(
        self,
        group_id: Union[str, int],
        type: Literal["talkative", "performer", "legend", "emotion", "all"],
    ) -> GroupChatActivity:
        """
        获取群荣誉信息

        Args:
            group_id: 群号
            type: 荣誉类型

        Returns:
            GroupChatActivity: 群活跃信息
        """
        result = await self._request_raw(
            "/get_group_honor_info",
            {"group_id": group_id, "type": type},
        )
        status = APIReturnStatus(result)
        return GroupChatActivity(status.data)

    # -------------------------------------------------------------------------
    # 群基础信息
    # -------------------------------------------------------------------------

    async def get_group_info(self, group_id: Union[str, int]) -> GroupInfo:
        """
        获取群信息

        Args:
            group_id: 群号

        Returns:
            GroupInfo: 群信息
        """
        result = await self._request_raw(
            "/get_group_info",
            {"group_id": group_id},
        )
        status = APIReturnStatus(result)
        return GroupInfo(**status.data)

    async def get_group_info_ex(self, group_id: Union[str, int]) -> dict:
        """
        获取群扩展信息

        Args:
            group_id: 群号

        Returns:
            dict: 群扩展信息
        """
        result = await self._request_raw(
            "/get_group_info_ex",
            {"group_id": group_id},
        )
        status = APIReturnStatus(result)
        return status.data

    async def get_group_list(self, info: bool = False) -> List[Union[str, dict]]:
        """
        获取群列表

        Args:
            info: 是否返回详细信息

        Returns:
            List: 群列表（ID 列表或信息字典列表）
        """
        result = await self._request_raw(
            "/get_group_list",
            {"next_token": ""},
        )
        status = APIReturnStatus(result)
        if status.is_success:
            if info:
                return status.data
            return [str(group.get("group_id")) for group in status.data]
        return []

    # -------------------------------------------------------------------------
    # 成员信息
    # -------------------------------------------------------------------------

    async def get_group_member_info(
        self, group_id: Union[str, int], user_id: Union[str, int]
    ) -> GroupMemberInfo:
        """
        获取群成员信息

        Args:
            group_id: 群号
            user_id: 用户 QQ 号

        Returns:
            GroupMemberInfo: 成员信息
        """
        result = await self._request_raw(
            "/get_group_member_info",
            {"group_id": group_id, "user_id": user_id},
        )
        status = APIReturnStatus(result)
        return GroupMemberInfo(**status.data)

    async def get_group_member_list(self, group_id: Union[str, int]) -> GroupMemberList:
        """
        获取群成员列表

        Args:
            group_id: 群号

        Returns:
            GroupMemberList: 成员列表
        """
        result = await self._request_raw(
            "/get_group_member_list",
            {"group_id": group_id},
        )
        status = APIReturnStatus(result)
        return GroupMemberList(status.data)

    async def get_group_shut_list(self, group_id: Union[str, int]) -> GroupMemberList:
        """
        获取群禁言列表

        Args:
            group_id: 群号

        Returns:
            GroupMemberList: 被禁言成员列表
        """
        result = await self._request_raw(
            "/get_group_shut_list",
            {"group_id": group_id},
        )
        status = APIReturnStatus(result)
        return GroupMemberList.from_shut_list(status.data)
