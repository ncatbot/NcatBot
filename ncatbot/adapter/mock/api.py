"""
MockBotAPI — IQQAPIClient 的内存实现

记录所有 API 调用，返回可配置的模拟响应，不进行任何网络通信。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

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


@dataclass
class APICall:
    """一次 API 调用的记录"""

    action: str
    args: tuple
    kwargs: dict


class MockBotAPI(IQQAPIClient):
    """IQQAPIClient 的完整 Mock 实现

    使用方式::

        api = MockBotAPI()

        # 设置特定 action 的返回值
        api.set_response("send_group_msg", {"message_id": "123"})

        # 执行调用
        result = await api.send_group_msg(12345, [{"type": "text", "data": {"text": "hi"}}])

        # 检查调用记录
        assert api.called("send_group_msg")
        assert api.call_count("send_group_msg") == 1
    """

    def __init__(self) -> None:
        self._calls: List[APICall] = []
        self._responses: Dict[str, Any] = {}
        self._default_response: dict = {}

    # ---- 调用记录与断言 ----

    def set_response(self, action: str, response: Any) -> None:
        """预设某个 action 的返回值"""
        self._responses[action] = response

    def _record(self, action: str, *args: Any, **kwargs: Any) -> Any:
        self._calls.append(APICall(action=action, args=args, kwargs=kwargs))
        return self._responses.get(action, self._default_response)

    @property
    def calls(self) -> List[APICall]:
        return list(self._calls)

    def called(self, action: str) -> bool:
        return any(c.action == action for c in self._calls)

    def call_count(self, action: str) -> int:
        return sum(1 for c in self._calls if c.action == action)

    def get_calls(self, action: str) -> List[APICall]:
        return [c for c in self._calls if c.action == action]

    def last_call(self, action: Optional[str] = None) -> Optional[APICall]:
        if action:
            matching = self.get_calls(action)
            return matching[-1] if matching else None
        return self._calls[-1] if self._calls else None

    def reset(self) -> None:
        self._calls.clear()

    @property
    def platform(self) -> str:
        return "qq"

    async def call(self, action: str, params: dict | None = None) -> Any:
        return self._record(action, **(params or {}))

    # ---- IQQAPIClient 实现 ----

    async def send_private_msg(
        self, user_id: Union[str, int], message: list, **kwargs
    ) -> SendMessageResult:
        return self._record("send_private_msg", user_id, message, **kwargs)

    async def send_group_msg(
        self, group_id: Union[str, int], message: list, **kwargs
    ) -> SendMessageResult:
        return self._record("send_group_msg", group_id, message, **kwargs)

    async def delete_msg(self, message_id: Union[str, int]) -> None:
        self._record("delete_msg", message_id)

    async def send_forward_msg(
        self, message_type: str, target_id: Union[str, int], messages: list, **kwargs
    ) -> SendMessageResult:
        return self._record(
            "send_forward_msg", message_type, target_id, messages, **kwargs
        )

    async def set_group_kick(
        self,
        group_id: Union[str, int],
        user_id: Union[str, int],
        reject_add_request: bool = False,
    ) -> None:
        self._record("set_group_kick", group_id, user_id, reject_add_request)

    async def set_group_ban(
        self,
        group_id: Union[str, int],
        user_id: Union[str, int],
        duration: int = 1800,
    ) -> None:
        self._record("set_group_ban", group_id, user_id, duration)

    async def set_group_whole_ban(
        self, group_id: Union[str, int], enable: bool = True
    ) -> None:
        self._record("set_group_whole_ban", group_id, enable)

    async def set_group_admin(
        self,
        group_id: Union[str, int],
        user_id: Union[str, int],
        enable: bool = True,
    ) -> None:
        self._record("set_group_admin", group_id, user_id, enable)

    async def set_group_card(
        self,
        group_id: Union[str, int],
        user_id: Union[str, int],
        card: str = "",
    ) -> None:
        self._record("set_group_card", group_id, user_id, card)

    async def set_group_name(self, group_id: Union[str, int], name: str) -> None:
        self._record("set_group_name", group_id, name)

    async def set_group_leave(
        self, group_id: Union[str, int], is_dismiss: bool = False
    ) -> None:
        self._record("set_group_leave", group_id, is_dismiss)

    async def set_group_special_title(
        self,
        group_id: Union[str, int],
        user_id: Union[str, int],
        special_title: str = "",
    ) -> None:
        self._record("set_group_special_title", group_id, user_id, special_title)

    async def get_group_notice(self, group_id: Union[str, int]) -> list:
        return self._record("get_group_notice", group_id)

    async def send_group_notice(
        self, group_id: Union[str, int], content: str, image: str = ""
    ) -> None:
        self._record("send_group_notice", group_id, content, image)

    async def delete_group_notice(
        self, group_id: Union[str, int], notice_id: str
    ) -> None:
        self._record("delete_group_notice", group_id, notice_id)

    async def set_essence_msg(self, message_id: Union[str, int]) -> None:
        self._record("set_essence_msg", message_id)

    async def delete_essence_msg(self, message_id: Union[str, int]) -> None:
        self._record("delete_essence_msg", message_id)

    async def set_group_kick_members(
        self,
        group_id: Union[str, int],
        user_ids: list,
        reject_add_request: bool = False,
    ) -> None:
        self._record("set_group_kick_members", group_id, user_ids, reject_add_request)

    async def set_group_remark(self, group_id: Union[str, int], remark: str) -> None:
        self._record("set_group_remark", group_id, remark)

    async def set_group_sign(self, group_id: Union[str, int]) -> None:
        self._record("set_group_sign", group_id)

    async def set_group_todo(
        self, group_id: Union[str, int], message_id: Union[str, int]
    ) -> None:
        self._record("set_group_todo", group_id, message_id)

    async def set_group_portrait(self, group_id: Union[str, int], file: str) -> None:
        self._record("set_group_portrait", group_id, file)

    async def set_friend_add_request(
        self, flag: str, approve: bool = True, remark: str = ""
    ) -> None:
        self._record("set_friend_add_request", flag, approve, remark)

    async def set_group_add_request(
        self, flag: str, sub_type: str, approve: bool = True, reason: str = ""
    ) -> None:
        self._record("set_group_add_request", flag, sub_type, approve, reason)

    async def set_friend_remark(self, user_id: Union[str, int], remark: str) -> None:
        self._record("set_friend_remark", user_id, remark)

    async def delete_friend(self, user_id: Union[str, int]) -> None:
        self._record("delete_friend", user_id)

    async def friend_poke(self, user_id: Union[str, int]) -> None:
        self._record("friend_poke", user_id)

    async def set_self_longnick(self, long_nick: str) -> None:
        self._record("set_self_longnick", long_nick)

    async def set_qq_avatar(self, file: str) -> None:
        self._record("set_qq_avatar", file)

    async def set_qq_profile(
        self,
        nickname: str = "",
        company: str = "",
        email: str = "",
        college: str = "",
        personal_note: str = "",
    ) -> None:
        self._record("set_qq_profile", nickname, company, email, college, personal_note)

    async def set_online_status(
        self, status: int, ext_status: int = 0, custom_status: str = ""
    ) -> None:
        self._record("set_online_status", status, ext_status, custom_status)

    async def ocr_image(self, image: str) -> OcrResult:
        return self._record("ocr_image", image)

    async def get_login_info(self) -> LoginInfo:
        return self._record("get_login_info")

    async def get_stranger_info(self, user_id: Union[str, int]) -> StrangerInfo:
        return self._record("get_stranger_info", user_id)

    async def get_friend_list(self) -> List[FriendInfo]:
        return self._record("get_friend_list")

    async def get_group_info(self, group_id: Union[str, int]) -> GroupInfo:
        return self._record("get_group_info", group_id)

    async def get_group_list(self) -> List[GroupInfo]:
        return self._record("get_group_list")

    async def get_group_member_info(
        self, group_id: Union[str, int], user_id: Union[str, int]
    ) -> GroupMemberInfo:
        return self._record("get_group_member_info", group_id, user_id)

    async def get_group_member_list(
        self, group_id: Union[str, int]
    ) -> List[GroupMemberInfo]:
        return self._record("get_group_member_list", group_id)

    async def get_msg(self, message_id: Union[str, int]) -> MessageData:
        return self._record("get_msg", message_id)

    async def get_forward_msg(self, message_id: Union[str, int]) -> ForwardMessageData:
        return self._record("get_forward_msg", message_id)

    async def get_essence_msg_list(self, group_id: Union[str, int]) -> list:
        return self._record("get_essence_msg_list", group_id)

    async def get_group_honor_info(
        self, group_id: Union[str, int], type: str = "all"
    ) -> GroupHonorInfo:
        return self._record("get_group_honor_info", group_id, type)

    async def get_group_at_all_remain(
        self, group_id: Union[str, int]
    ) -> GroupAtAllRemain:
        return self._record("get_group_at_all_remain", group_id)

    async def get_group_shut_list(self, group_id: Union[str, int]) -> list:
        return self._record("get_group_shut_list", group_id)

    async def get_group_system_msg(self) -> GroupSystemMsg:
        return self._record("get_group_system_msg")

    async def get_group_info_ex(self, group_id: Union[str, int]) -> GroupInfoEx:
        return self._record("get_group_info_ex", group_id)

    async def get_group_file_system_info(
        self, group_id: Union[str, int]
    ) -> GroupFileSystemInfo:
        return self._record("get_group_file_system_info", group_id)

    async def get_group_files_by_folder(
        self, group_id: Union[str, int], folder_id: str
    ) -> GroupFileList:
        return self._record("get_group_files_by_folder", group_id, folder_id)

    async def get_private_file_url(self, user_id: Union[str, int], file_id: str) -> str:
        return self._record("get_private_file_url", user_id, file_id)

    async def get_group_msg_history(
        self,
        group_id: Union[str, int],
        message_seq: Union[str, int, None] = None,
        count: int = 20,
    ) -> MessageHistory:
        return self._record("get_group_msg_history", group_id, message_seq, count)

    async def get_friend_msg_history(
        self,
        user_id: Union[str, int],
        message_seq: Union[str, int, None] = None,
        count: int = 20,
    ) -> MessageHistory:
        return self._record("get_friend_msg_history", user_id, message_seq, count)

    async def get_file(self, file_id: str) -> FileData:
        return self._record("get_file", file_id)

    async def fetch_emoji_like(
        self, message_id: Union[str, int], emoji_id: str, emoji_type: str = ""
    ) -> EmojiLikeInfo:
        return self._record("fetch_emoji_like", message_id, emoji_id, emoji_type)

    async def get_emoji_likes(self, message_id: Union[str, int]) -> list:
        return self._record("get_emoji_likes", message_id)

    async def get_version_info(self) -> VersionInfo:
        return self._record("get_version_info")

    async def get_status(self) -> BotStatus:
        return self._record("get_status")

    async def get_recent_contact(self, count: int = 10) -> list:
        return self._record("get_recent_contact", count)

    async def upload_group_file(
        self, group_id: Union[str, int], file: str, name: str, folder_id: str = ""
    ) -> None:
        self._record("upload_group_file", group_id, file, name, folder_id)

    async def get_group_root_files(self, group_id: Union[str, int]) -> GroupFileList:
        return self._record("get_group_root_files", group_id)

    async def get_group_file_url(self, group_id: Union[str, int], file_id: str) -> str:
        return self._record("get_group_file_url", group_id, file_id)

    async def delete_group_file(self, group_id: Union[str, int], file_id: str) -> None:
        self._record("delete_group_file", group_id, file_id)

    async def create_group_file_folder(
        self, group_id: Union[str, int], name: str, parent_id: str = ""
    ) -> dict:
        return self._record("create_group_file_folder", group_id, name, parent_id)

    async def delete_group_folder(
        self, group_id: Union[str, int], folder_id: str
    ) -> None:
        self._record("delete_group_folder", group_id, folder_id)

    async def upload_private_file(
        self, user_id: Union[str, int], file: str, name: str
    ) -> None:
        self._record("upload_private_file", user_id, file, name)

    async def download_file(
        self, url: str = "", file: str = "", headers: str = ""
    ) -> DownloadResult:
        return self._record("download_file", url, file, headers)

    async def set_msg_emoji_like(
        self, message_id: Union[str, int], emoji_id: str, set: bool = True
    ) -> None:
        self._record("set_msg_emoji_like", message_id, emoji_id, set)

    async def mark_group_msg_as_read(self, group_id: Union[str, int]) -> None:
        self._record("mark_group_msg_as_read", group_id)

    async def mark_private_msg_as_read(self, user_id: Union[str, int]) -> None:
        self._record("mark_private_msg_as_read", user_id)

    async def mark_all_as_read(self) -> None:
        self._record("mark_all_as_read")

    async def forward_friend_single_msg(
        self, user_id: Union[str, int], message_id: Union[str, int]
    ) -> None:
        self._record("forward_friend_single_msg", user_id, message_id)

    async def forward_group_single_msg(
        self, group_id: Union[str, int], message_id: Union[str, int]
    ) -> None:
        self._record("forward_group_single_msg", group_id, message_id)

    async def send_like(self, user_id: Union[str, int], times: int = 1) -> None:
        self._record("send_like", user_id, times)

    async def send_poke(
        self, group_id: Union[str, int], user_id: Union[str, int]
    ) -> None:
        self._record("send_poke", group_id, user_id)
