"""
MockBotAPI — IQQAPIClient 的内存 Mock 实现

所有 API 调用通过 _record(action, key=val) 以命名参数形式录制。
"""

from __future__ import annotations

from typing import List, Union

from ncatbot.api.qq import IQQAPIClient
from ncatbot.types.napcat import (
    BotStatus,
    DownloadResult,
    EmojiLikeInfo,
    FileData,
    FriendInfo,
    ForwardMessageData,
    GroupAtAllRemain,
    GroupFileList,
    GroupFileSystemInfo,
    GroupHonorInfo,
    GroupInfo,
    GroupInfoEx,
    GroupMemberInfo,
    GroupSystemMsg,
    LoginInfo,
    MessageData,
    MessageHistory,
    OcrResult,
    SendMessageResult,
    StrangerInfo,
    VersionInfo,
)

from .api_base import APICall, MockAPIBase

__all__ = ["MockBotAPI", "APICall"]


class MockBotAPI(MockAPIBase, IQQAPIClient):
    """IQQAPIClient 的完整 Mock 实现 — 命名参数录制"""

    def __init__(self) -> None:
        super().__init__(platform="qq")

    # ---- IMessaging ----

    async def send_private_msg(
        self, user_id: Union[str, int], message: list, **kwargs
    ) -> SendMessageResult:
        return self._record(
            "send_private_msg", user_id=user_id, message=message, **kwargs
        )

    async def send_group_msg(
        self, group_id: Union[str, int], message: list, **kwargs
    ) -> SendMessageResult:
        return self._record(
            "send_group_msg", group_id=group_id, message=message, **kwargs
        )

    # ---- Sugar（event.reply() 等需要） ----

    async def post_group_array_msg(
        self, group_id: Union[str, int], msg, *, strict: bool = False
    ) -> SendMessageResult:
        return self._record(
            "post_group_array_msg", group_id=group_id, msg=msg, strict=strict
        )

    async def post_private_array_msg(
        self, user_id: Union[str, int], msg, *, strict: bool = False
    ) -> SendMessageResult:
        return self._record(
            "post_private_array_msg", user_id=user_id, msg=msg, strict=strict
        )

    async def delete_msg(self, message_id: Union[str, int]) -> None:
        self._record("delete_msg", message_id=message_id)

    async def send_forward_msg(
        self, message_type: str, target_id: Union[str, int], messages: list, **kwargs
    ) -> SendMessageResult:
        return self._record(
            "send_forward_msg",
            message_type=message_type,
            target_id=target_id,
            messages=messages,
            **kwargs,
        )

    # ---- IGroupManage ----

    async def set_group_kick(
        self,
        group_id: Union[str, int],
        user_id: Union[str, int],
        reject_add_request: bool = False,
    ) -> None:
        self._record(
            "set_group_kick",
            group_id=group_id,
            user_id=user_id,
            reject_add_request=reject_add_request,
        )

    async def set_group_ban(
        self,
        group_id: Union[str, int],
        user_id: Union[str, int],
        duration: int = 1800,
    ) -> None:
        self._record(
            "set_group_ban", group_id=group_id, user_id=user_id, duration=duration
        )

    async def set_group_whole_ban(
        self,
        group_id: Union[str, int],
        enable: bool = True,
    ) -> None:
        self._record("set_group_whole_ban", group_id=group_id, enable=enable)

    async def set_group_admin(
        self,
        group_id: Union[str, int],
        user_id: Union[str, int],
        enable: bool = True,
    ) -> None:
        self._record(
            "set_group_admin", group_id=group_id, user_id=user_id, enable=enable
        )

    async def set_group_card(
        self,
        group_id: Union[str, int],
        user_id: Union[str, int],
        card: str = "",
    ) -> None:
        self._record("set_group_card", group_id=group_id, user_id=user_id, card=card)

    async def set_group_name(self, group_id: Union[str, int], name: str) -> None:
        self._record("set_group_name", group_id=group_id, name=name)

    async def set_group_leave(
        self,
        group_id: Union[str, int],
        is_dismiss: bool = False,
    ) -> None:
        self._record("set_group_leave", group_id=group_id, is_dismiss=is_dismiss)

    async def set_group_special_title(
        self,
        group_id: Union[str, int],
        user_id: Union[str, int],
        special_title: str = "",
    ) -> None:
        self._record(
            "set_group_special_title",
            group_id=group_id,
            user_id=user_id,
            special_title=special_title,
        )

    async def get_group_notice(self, group_id: Union[str, int]) -> list:
        return self._record("get_group_notice", group_id=group_id)

    async def send_group_notice(
        self,
        group_id: Union[str, int],
        content: str,
        image: str = "",
    ) -> None:
        self._record(
            "send_group_notice", group_id=group_id, content=content, image=image
        )

    async def delete_group_notice(
        self,
        group_id: Union[str, int],
        notice_id: str,
    ) -> None:
        self._record("delete_group_notice", group_id=group_id, notice_id=notice_id)

    async def set_essence_msg(self, message_id: Union[str, int]) -> None:
        self._record("set_essence_msg", message_id=message_id)

    async def delete_essence_msg(self, message_id: Union[str, int]) -> None:
        self._record("delete_essence_msg", message_id=message_id)

    async def set_group_kick_members(
        self,
        group_id: Union[str, int],
        user_ids: list,
        reject_add_request: bool = False,
    ) -> None:
        self._record(
            "set_group_kick_members",
            group_id=group_id,
            user_ids=user_ids,
            reject_add_request=reject_add_request,
        )

    async def set_group_remark(self, group_id: Union[str, int], remark: str) -> None:
        self._record("set_group_remark", group_id=group_id, remark=remark)

    async def set_group_sign(self, group_id: Union[str, int]) -> None:
        self._record("set_group_sign", group_id=group_id)

    async def set_group_todo(
        self,
        group_id: Union[str, int],
        message_id: Union[str, int],
    ) -> None:
        self._record("set_group_todo", group_id=group_id, message_id=message_id)

    async def set_group_portrait(self, group_id: Union[str, int], file: str) -> None:
        self._record("set_group_portrait", group_id=group_id, file=file)

    async def set_friend_add_request(
        self,
        flag: str,
        approve: bool = True,
        remark: str = "",
    ) -> None:
        self._record(
            "set_friend_add_request", flag=flag, approve=approve, remark=remark
        )

    async def set_group_add_request(
        self,
        flag: str,
        sub_type: str,
        approve: bool = True,
        reason: str = "",
    ) -> None:
        self._record(
            "set_group_add_request",
            flag=flag,
            sub_type=sub_type,
            approve=approve,
            reason=reason,
        )

    async def set_friend_remark(self, user_id: Union[str, int], remark: str) -> None:
        self._record("set_friend_remark", user_id=user_id, remark=remark)

    async def delete_friend(self, user_id: Union[str, int]) -> None:
        self._record("delete_friend", user_id=user_id)

    async def friend_poke(self, user_id: Union[str, int]) -> None:
        self._record("friend_poke", user_id=user_id)

    async def set_self_longnick(self, long_nick: str) -> None:
        self._record("set_self_longnick", long_nick=long_nick)

    async def set_qq_avatar(self, file: str) -> None:
        self._record("set_qq_avatar", file=file)

    async def set_qq_profile(
        self,
        nickname: str = "",
        company: str = "",
        email: str = "",
        college: str = "",
        personal_note: str = "",
    ) -> None:
        self._record(
            "set_qq_profile",
            nickname=nickname,
            company=company,
            email=email,
            college=college,
            personal_note=personal_note,
        )

    async def set_online_status(
        self,
        status: int,
        ext_status: int = 0,
        custom_status: str = "",
    ) -> None:
        self._record(
            "set_online_status",
            status=status,
            ext_status=ext_status,
            custom_status=custom_status,
        )

    # ---- IQuery ----

    async def ocr_image(self, image: str) -> OcrResult:
        return self._record("ocr_image", image=image)

    async def get_login_info(self) -> LoginInfo:
        return self._record("get_login_info")

    async def get_stranger_info(self, user_id: Union[str, int]) -> StrangerInfo:
        return self._record("get_stranger_info", user_id=user_id)

    async def get_friend_list(self) -> List[FriendInfo]:
        return self._record("get_friend_list")

    async def get_group_info(self, group_id: Union[str, int]) -> GroupInfo:
        return self._record("get_group_info", group_id=group_id)

    async def get_group_list(self) -> List[GroupInfo]:
        return self._record("get_group_list")

    async def get_group_member_info(
        self,
        group_id: Union[str, int],
        user_id: Union[str, int],
    ) -> GroupMemberInfo:
        return self._record("get_group_member_info", group_id=group_id, user_id=user_id)

    async def get_group_member_list(
        self, group_id: Union[str, int]
    ) -> List[GroupMemberInfo]:
        return self._record("get_group_member_list", group_id=group_id)

    async def get_msg(self, message_id: Union[str, int]) -> MessageData:
        return self._record("get_msg", message_id=message_id)

    async def get_forward_msg(self, message_id: Union[str, int]) -> ForwardMessageData:
        return self._record("get_forward_msg", message_id=message_id)

    async def get_essence_msg_list(self, group_id: Union[str, int]) -> list:
        return self._record("get_essence_msg_list", group_id=group_id)

    async def get_group_honor_info(
        self,
        group_id: Union[str, int],
        type: str = "all",
    ) -> GroupHonorInfo:
        return self._record("get_group_honor_info", group_id=group_id, type=type)

    async def get_group_at_all_remain(
        self, group_id: Union[str, int]
    ) -> GroupAtAllRemain:
        return self._record("get_group_at_all_remain", group_id=group_id)

    async def get_group_shut_list(self, group_id: Union[str, int]) -> list:
        return self._record("get_group_shut_list", group_id=group_id)

    async def get_group_system_msg(self) -> GroupSystemMsg:
        return self._record("get_group_system_msg")

    async def get_group_info_ex(self, group_id: Union[str, int]) -> GroupInfoEx:
        return self._record("get_group_info_ex", group_id=group_id)

    async def get_group_file_system_info(
        self, group_id: Union[str, int]
    ) -> GroupFileSystemInfo:
        return self._record("get_group_file_system_info", group_id=group_id)

    async def get_group_files_by_folder(
        self,
        group_id: Union[str, int],
        folder_id: str,
    ) -> GroupFileList:
        return self._record(
            "get_group_files_by_folder", group_id=group_id, folder_id=folder_id
        )

    async def get_private_file_url(self, user_id: Union[str, int], file_id: str) -> str:
        return self._record("get_private_file_url", user_id=user_id, file_id=file_id)

    async def get_group_msg_history(
        self,
        group_id: Union[str, int],
        message_seq: Union[str, int, None] = None,
        count: int = 20,
    ) -> MessageHistory:
        return self._record(
            "get_group_msg_history",
            group_id=group_id,
            message_seq=message_seq,
            count=count,
        )

    async def get_friend_msg_history(
        self,
        user_id: Union[str, int],
        message_seq: Union[str, int, None] = None,
        count: int = 20,
    ) -> MessageHistory:
        return self._record(
            "get_friend_msg_history",
            user_id=user_id,
            message_seq=message_seq,
            count=count,
        )

    async def get_file(self, file_id: str) -> FileData:
        return self._record("get_file", file_id=file_id)

    async def fetch_emoji_like(
        self,
        message_id: Union[str, int],
        emoji_id: str,
        emoji_type: str = "",
    ) -> EmojiLikeInfo:
        return self._record(
            "fetch_emoji_like",
            message_id=message_id,
            emoji_id=emoji_id,
            emoji_type=emoji_type,
        )

    async def get_emoji_likes(self, message_id: Union[str, int]) -> list:
        return self._record("get_emoji_likes", message_id=message_id)

    async def get_version_info(self) -> VersionInfo:
        return self._record("get_version_info")

    async def get_status(self) -> BotStatus:
        return self._record("get_status")

    async def get_recent_contact(self, count: int = 10) -> list:
        return self._record("get_recent_contact", count=count)

    # ---- IFileTransfer ----

    async def upload_group_file(
        self,
        group_id: Union[str, int],
        file: str,
        name: str,
        folder_id: str = "",
    ) -> None:
        self._record(
            "upload_group_file",
            group_id=group_id,
            file=file,
            name=name,
            folder_id=folder_id,
        )

    async def get_group_root_files(self, group_id: Union[str, int]) -> GroupFileList:
        return self._record("get_group_root_files", group_id=group_id)

    async def get_group_file_url(self, group_id: Union[str, int], file_id: str) -> str:
        return self._record("get_group_file_url", group_id=group_id, file_id=file_id)

    async def delete_group_file(self, group_id: Union[str, int], file_id: str) -> None:
        self._record("delete_group_file", group_id=group_id, file_id=file_id)

    async def create_group_file_folder(
        self,
        group_id: Union[str, int],
        name: str,
        parent_id: str = "",
    ) -> dict:
        return self._record(
            "create_group_file_folder",
            group_id=group_id,
            name=name,
            parent_id=parent_id,
        )

    async def delete_group_folder(
        self, group_id: Union[str, int], folder_id: str
    ) -> None:
        self._record("delete_group_folder", group_id=group_id, folder_id=folder_id)

    async def upload_private_file(
        self,
        user_id: Union[str, int],
        file: str,
        name: str,
    ) -> None:
        self._record("upload_private_file", user_id=user_id, file=file, name=name)

    async def download_file(
        self,
        url: str = "",
        file: str = "",
        headers: str = "",
    ) -> DownloadResult:
        return self._record("download_file", url=url, file=file, headers=headers)

    # ---- 消息扩展 ----

    async def set_msg_emoji_like(
        self,
        message_id: Union[str, int],
        emoji_id: str,
        set: bool = True,
    ) -> None:
        self._record(
            "set_msg_emoji_like", message_id=message_id, emoji_id=emoji_id, set=set
        )

    async def mark_group_msg_as_read(self, group_id: Union[str, int]) -> None:
        self._record("mark_group_msg_as_read", group_id=group_id)

    async def mark_private_msg_as_read(self, user_id: Union[str, int]) -> None:
        self._record("mark_private_msg_as_read", user_id=user_id)

    async def mark_all_as_read(self) -> None:
        self._record("mark_all_as_read")

    async def forward_friend_single_msg(
        self,
        user_id: Union[str, int],
        message_id: Union[str, int],
    ) -> None:
        self._record(
            "forward_friend_single_msg", user_id=user_id, message_id=message_id
        )

    async def forward_group_single_msg(
        self,
        group_id: Union[str, int],
        message_id: Union[str, int],
    ) -> None:
        self._record(
            "forward_group_single_msg", group_id=group_id, message_id=message_id
        )

    async def send_like(self, user_id: Union[str, int], times: int = 1) -> None:
        self._record("send_like", user_id=user_id, times=times)

    async def send_poke(
        self,
        group_id: Union[str, int],
        user_id: Union[str, int],
    ) -> None:
        self._record("send_poke", group_id=group_id, user_id=user_id)
