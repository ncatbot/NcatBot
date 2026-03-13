"""
NapCat API 实现

实现 IBotAPI 抽象接口，通过 NapCatProtocol 发送 OneBot v11 API 调用。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from ncatbot.core.api.interface import IBotAPI
from ncatbot.utils import get_log

from .protocol import NapCatProtocol

LOG = get_log("NapCatBotAPI")


class NapCatBotAPI(IBotAPI):
    """NapCat 平台的 IBotAPI 实现

    将标准 IBotAPI 调用转换为 OneBot v11 协议请求，
    通过 NapCatProtocol 发送并返回结果。
    """

    def __init__(self, protocol: NapCatProtocol):
        self._protocol = protocol

    async def _call(self, action: str, params: Optional[dict] = None) -> dict:
        """发送 API 请求"""
        resp = await self._protocol.send(action, params)
        return resp

    async def _call_data(self, action: str, params: Optional[dict] = None) -> Any:
        """发送 API 请求并返回 data 字段"""
        resp = await self._call(action, params)
        return resp.get("data")

    # ==================================================================
    # 消息操作
    # ==================================================================

    async def send_private_msg(
        self, user_id: Union[str, int], message: list, **kwargs
    ) -> dict:
        params: Dict[str, Any] = {"user_id": int(user_id), "message": message}
        params.update(kwargs)
        resp = await self._call("send_private_msg", params)
        return resp.get("data", {})

    async def send_group_msg(
        self, group_id: Union[str, int], message: list, **kwargs
    ) -> dict:
        params: Dict[str, Any] = {"group_id": int(group_id), "message": message}
        params.update(kwargs)
        resp = await self._call("send_group_msg", params)
        return resp.get("data", {})

    async def delete_msg(self, message_id: Union[str, int]) -> None:
        await self._call("delete_msg", {"message_id": int(message_id)})

    async def send_forward_msg(
        self,
        message_type: str,
        target_id: Union[str, int],
        messages: list,
        **kwargs,
    ) -> dict:
        params: Dict[str, Any] = {
            "message_type": message_type,
            "messages": messages,
        }
        # 根据 message_type 设置 target_id
        if message_type == "group":
            params["group_id"] = int(target_id)
        else:
            params["user_id"] = int(target_id)
        params.update(kwargs)
        resp = await self._call("send_forward_msg", params)
        return resp.get("data", {})

    # ==================================================================
    # 群管理
    # ==================================================================

    async def set_group_kick(
        self,
        group_id: Union[str, int],
        user_id: Union[str, int],
        reject_add_request: bool = False,
    ) -> None:
        await self._call(
            "set_group_kick",
            {
                "group_id": int(group_id),
                "user_id": int(user_id),
                "reject_add_request": reject_add_request,
            },
        )

    async def set_group_ban(
        self,
        group_id: Union[str, int],
        user_id: Union[str, int],
        duration: int = 30 * 60,
    ) -> None:
        await self._call(
            "set_group_ban",
            {
                "group_id": int(group_id),
                "user_id": int(user_id),
                "duration": duration,
            },
        )

    async def set_group_whole_ban(
        self, group_id: Union[str, int], enable: bool = True
    ) -> None:
        await self._call(
            "set_group_whole_ban",
            {"group_id": int(group_id), "enable": enable},
        )

    async def set_group_admin(
        self,
        group_id: Union[str, int],
        user_id: Union[str, int],
        enable: bool = True,
    ) -> None:
        await self._call(
            "set_group_admin",
            {
                "group_id": int(group_id),
                "user_id": int(user_id),
                "enable": enable,
            },
        )

    async def set_group_card(
        self,
        group_id: Union[str, int],
        user_id: Union[str, int],
        card: str = "",
    ) -> None:
        await self._call(
            "set_group_card",
            {
                "group_id": int(group_id),
                "user_id": int(user_id),
                "card": card,
            },
        )

    async def set_group_name(self, group_id: Union[str, int], name: str) -> None:
        await self._call(
            "set_group_name",
            {"group_id": int(group_id), "group_name": name},
        )

    async def set_group_leave(
        self, group_id: Union[str, int], is_dismiss: bool = False
    ) -> None:
        await self._call(
            "set_group_leave",
            {"group_id": int(group_id), "is_dismiss": is_dismiss},
        )

    async def set_group_special_title(
        self,
        group_id: Union[str, int],
        user_id: Union[str, int],
        special_title: str = "",
    ) -> None:
        await self._call(
            "set_group_special_title",
            {
                "group_id": int(group_id),
                "user_id": int(user_id),
                "special_title": special_title,
            },
        )

    # ==================================================================
    # 账号操作
    # ==================================================================

    async def set_friend_add_request(
        self, flag: str, approve: bool = True, remark: str = ""
    ) -> None:
        await self._call(
            "set_friend_add_request",
            {"flag": flag, "approve": approve, "remark": remark},
        )

    async def set_group_add_request(
        self,
        flag: str,
        sub_type: str,
        approve: bool = True,
        reason: str = "",
    ) -> None:
        await self._call(
            "set_group_add_request",
            {
                "flag": flag,
                "sub_type": sub_type,
                "approve": approve,
                "reason": reason,
            },
        )

    # ==================================================================
    # 信息查询
    # ==================================================================

    async def get_login_info(self) -> dict:
        return await self._call_data("get_login_info") or {}

    async def get_stranger_info(self, user_id: Union[str, int]) -> dict:
        return (
            await self._call_data("get_stranger_info", {"user_id": int(user_id)}) or {}
        )

    async def get_friend_list(self) -> List[dict]:
        return await self._call_data("get_friend_list") or []

    async def get_group_info(self, group_id: Union[str, int]) -> dict:
        return (
            await self._call_data("get_group_info", {"group_id": int(group_id)}) or {}
        )

    async def get_group_list(self) -> list:
        return await self._call_data("get_group_list") or []

    async def get_group_member_info(
        self,
        group_id: Union[str, int],
        user_id: Union[str, int],
    ) -> dict:
        return (
            await self._call_data(
                "get_group_member_info",
                {"group_id": int(group_id), "user_id": int(user_id)},
            )
            or {}
        )

    async def get_group_member_list(self, group_id: Union[str, int]) -> list:
        return (
            await self._call_data("get_group_member_list", {"group_id": int(group_id)})
            or []
        )

    async def get_msg(self, message_id: Union[str, int]) -> dict:
        return await self._call_data("get_msg", {"message_id": int(message_id)}) or {}

    async def get_forward_msg(self, message_id: Union[str, int]) -> dict:
        return (
            await self._call_data("get_forward_msg", {"message_id": int(message_id)})
            or {}
        )

    # ==================================================================
    # 文件操作
    # ==================================================================

    async def upload_group_file(
        self,
        group_id: Union[str, int],
        file: str,
        name: str,
        folder_id: str = "",
    ) -> None:
        await self._call(
            "upload_group_file",
            {
                "group_id": int(group_id),
                "file": file,
                "name": name,
                "folder_id": folder_id,
            },
        )

    async def get_group_root_files(self, group_id: Union[str, int]) -> dict:
        return (
            await self._call_data("get_group_root_files", {"group_id": int(group_id)})
            or {}
        )

    async def get_group_file_url(self, group_id: Union[str, int], file_id: str) -> str:
        data = await self._call_data(
            "get_group_file_url",
            {"group_id": int(group_id), "file_id": file_id},
        )
        return (data or {}).get("url", "")

    async def delete_group_file(self, group_id: Union[str, int], file_id: str) -> None:
        await self._call(
            "delete_group_file",
            {"group_id": int(group_id), "file_id": file_id},
        )

    # ==================================================================
    # 辅助功能
    # ==================================================================

    async def send_like(self, user_id: Union[str, int], times: int = 1) -> None:
        await self._call(
            "send_like",
            {"user_id": int(user_id), "times": times},
        )

    async def send_poke(
        self,
        group_id: Union[str, int],
        user_id: Union[str, int],
    ) -> None:
        await self._call(
            "group_poke",
            {"group_id": int(group_id), "user_id": int(user_id)},
        )
