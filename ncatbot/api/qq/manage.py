"""QQManage — 群管理 + 账号操作功能分组"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Union

from ncatbot.types.qq import OnlineStatus

if TYPE_CHECKING:
    from .interface import IQQAPIClient


class QQManage:
    """群管理 + 账号设置 + 组合 sugar"""

    __slots__ = ("_api",)

    def __init__(self, api: IQQAPIClient) -> None:
        self._api = api

    # ---- 群管理 ----

    async def set_group_kick(
        self,
        group_id: Union[str, int],
        user_id: Union[str, int],
        reject_add_request: bool = False,
    ) -> None:
        await self._api.set_group_kick(group_id, user_id, reject_add_request)

    async def set_group_ban(
        self,
        group_id: Union[str, int],
        user_id: Union[str, int],
        duration: int = 1800,
    ) -> None:
        await self._api.set_group_ban(group_id, user_id, duration)

    async def set_group_whole_ban(
        self, group_id: Union[str, int], enable: bool = True
    ) -> None:
        await self._api.set_group_whole_ban(group_id, enable)

    async def set_group_admin(
        self,
        group_id: Union[str, int],
        user_id: Union[str, int],
        enable: bool = True,
    ) -> None:
        await self._api.set_group_admin(group_id, user_id, enable)

    async def set_group_card(
        self,
        group_id: Union[str, int],
        user_id: Union[str, int],
        card: str = "",
    ) -> None:
        await self._api.set_group_card(group_id, user_id, card)

    async def set_group_name(self, group_id: Union[str, int], name: str) -> None:
        await self._api.set_group_name(group_id, name)

    async def set_group_leave(
        self, group_id: Union[str, int], is_dismiss: bool = False
    ) -> None:
        await self._api.set_group_leave(group_id, is_dismiss)

    async def set_group_special_title(
        self,
        group_id: Union[str, int],
        user_id: Union[str, int],
        special_title: str = "",
    ) -> None:
        await self._api.set_group_special_title(group_id, user_id, special_title)

    # ---- 群公告 / 精华 / 扩展管理 ----

    async def send_group_notice(
        self, group_id: Union[str, int], content: str, image: str = ""
    ) -> None:
        await self._api.send_group_notice(group_id, content, image)

    async def delete_group_notice(
        self, group_id: Union[str, int], notice_id: str
    ) -> None:
        await self._api.delete_group_notice(group_id, notice_id)

    async def set_essence_msg(self, message_id: Union[str, int]) -> None:
        await self._api.set_essence_msg(message_id)

    async def delete_essence_msg(self, message_id: Union[str, int]) -> None:
        await self._api.delete_essence_msg(message_id)

    async def set_group_kick_members(
        self,
        group_id: Union[str, int],
        user_ids: list,
        reject_add_request: bool = False,
    ) -> None:
        await self._api.set_group_kick_members(group_id, user_ids, reject_add_request)

    async def set_group_remark(self, group_id: Union[str, int], remark: str) -> None:
        await self._api.set_group_remark(group_id, remark)

    async def set_group_sign(self, group_id: Union[str, int]) -> None:
        await self._api.set_group_sign(group_id)

    async def set_group_todo(
        self, group_id: Union[str, int], message_id: Union[str, int]
    ) -> None:
        await self._api.set_group_todo(group_id, message_id)

    async def set_group_portrait(self, group_id: Union[str, int], file: str) -> None:
        await self._api.set_group_portrait(group_id, file)

    # ---- 账号操作 ----

    async def set_friend_add_request(
        self, flag: str, approve: bool = True, remark: str = ""
    ) -> None:
        await self._api.set_friend_add_request(flag, approve, remark)

    async def set_group_add_request(
        self, flag: str, sub_type: str, approve: bool = True, reason: str = ""
    ) -> None:
        await self._api.set_group_add_request(flag, sub_type, approve, reason)

    # ---- 好友管理 ----

    async def set_friend_remark(self, user_id: Union[str, int], remark: str) -> None:
        await self._api.set_friend_remark(user_id, remark)

    async def delete_friend(self, user_id: Union[str, int]) -> None:
        await self._api.delete_friend(user_id)

    # ---- 个人资料 ----

    async def set_self_longnick(self, long_nick: str) -> None:
        await self._api.set_self_longnick(long_nick)

    async def set_qq_avatar(self, file: str) -> None:
        await self._api.set_qq_avatar(file)

    async def set_qq_profile(
        self,
        nickname: str = "",
        company: str = "",
        email: str = "",
        college: str = "",
        personal_note: str = "",
    ) -> None:
        await self._api.set_qq_profile(nickname, company, email, college, personal_note)

    async def set_online_status(
        self,
        status: OnlineStatus | int,
        ext_status: int = 0,
        custom_status: str = "",
        *,
        battery_status: int = 0,
    ) -> None:
        """设置 QQ 在线状态，推荐使用 OnlineStatus，也兼容普通整数。

        battery_status 仅限关键字传入，默认 0；保留旧 custom_status 位置参数。
        """
        await self._api.set_online_status(
            status, ext_status, custom_status, battery_status=battery_status
        )

    # ---- 组合 sugar ----

    async def kick_and_block(
        self,
        group_id: Union[str, int],
        user_id: Union[str, int],
        message_id: Optional[Union[str, int]] = None,
    ) -> None:
        """撤回 + 踢出 + 拒绝再加群"""
        if message_id is not None:
            await self._api.delete_msg(message_id)
        await self._api.set_group_kick(group_id, user_id, reject_add_request=True)
