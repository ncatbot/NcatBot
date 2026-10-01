"""IQQAPIClient — QQ 平台完整 API 接口

组合 IAPIClient + 通用 traits + QQ/OB11 专用方法。
由 NapCatBotAPI 实现。
"""

from __future__ import annotations

from abc import abstractmethod
from typing import List, Union

from ncatbot.types.qq import OnlineStatus

from ..base import IAPIClient
from ..traits import IMessaging, IGroupManage, IQuery, IFileTransfer
from ncatbot.types.napcat import (
    BotStatus,
    CreateFolderResult,
    DownloadResult,
    EmojiLikeInfo,
    EmojiLikesResult,
    EssenceMessage,
    FileData,
    FriendInfo,
    GroupAtAllRemain,
    GroupFileList,
    GroupFileSystemInfo,
    GroupHonorInfo,
    GroupInfo,
    GroupInfoEx,
    GroupMemberInfo,
    GroupNotice,
    GroupShutInfo,
    GroupSystemMsg,
    LoginInfo,
    MessageData,
    MessageHistory,
    ForwardMessageData,
    OcrResult,
    RecentContact,
    SendMessageResult,
    StrangerInfo,
    VersionInfo,
)


class IQQAPIClient(IAPIClient, IMessaging, IGroupManage, IQuery, IFileTransfer):
    """QQ 平台 Bot API 接口

    组合:
    - IAPIClient: platform + call
    - IMessaging: send_private_msg, send_group_msg, delete_msg, send_forward_msg
    - IGroupManage: set_group_kick, set_group_ban, ...
    - IQuery: get_login_info, get_friend_list, ...
    - IFileTransfer: upload_group_file, download_file
    加上 QQ/OB11 专用扩展方法。
    """

    # ---- 消息操作 (IMessaging) ----

    @abstractmethod
    async def send_private_msg(
        self, user_id: Union[str, int], message: list, **kwargs
    ) -> SendMessageResult: ...

    @abstractmethod
    async def send_group_msg(
        self, group_id: Union[str, int], message: list, **kwargs
    ) -> SendMessageResult: ...

    @abstractmethod
    async def delete_msg(self, message_id: Union[str, int]) -> None: ...

    @abstractmethod
    async def send_forward_msg(
        self,
        message_type: str,
        target_id: Union[str, int],
        messages: list,
        **kwargs,
    ) -> SendMessageResult: ...

    # ---- 群管理 (IGroupManage) ----

    @abstractmethod
    async def set_group_kick(
        self,
        group_id: Union[str, int],
        user_id: Union[str, int],
        reject_add_request: bool = False,
    ) -> None: ...

    @abstractmethod
    async def set_group_ban(
        self,
        group_id: Union[str, int],
        user_id: Union[str, int],
        duration: int = 1800,
    ) -> None: ...

    @abstractmethod
    async def set_group_whole_ban(
        self, group_id: Union[str, int], enable: bool = True
    ) -> None: ...

    @abstractmethod
    async def set_group_admin(
        self,
        group_id: Union[str, int],
        user_id: Union[str, int],
        enable: bool = True,
    ) -> None: ...

    @abstractmethod
    async def set_group_card(
        self,
        group_id: Union[str, int],
        user_id: Union[str, int],
        card: str = "",
    ) -> None: ...

    @abstractmethod
    async def set_group_name(self, group_id: Union[str, int], name: str) -> None: ...

    @abstractmethod
    async def set_group_leave(
        self, group_id: Union[str, int], is_dismiss: bool = False
    ) -> None: ...

    @abstractmethod
    async def set_group_special_title(
        self,
        group_id: Union[str, int],
        user_id: Union[str, int],
        special_title: str = "",
    ) -> None: ...

    @abstractmethod
    async def get_group_notice(
        self, group_id: Union[str, int]
    ) -> List[GroupNotice]: ...

    @abstractmethod
    async def send_group_notice(
        self, group_id: Union[str, int], content: str, image: str = ""
    ) -> None: ...

    @abstractmethod
    async def delete_group_notice(
        self, group_id: Union[str, int], notice_id: str
    ) -> None: ...

    @abstractmethod
    async def set_essence_msg(self, message_id: Union[str, int]) -> None: ...

    @abstractmethod
    async def delete_essence_msg(self, message_id: Union[str, int]) -> None: ...

    @abstractmethod
    async def set_group_kick_members(
        self,
        group_id: Union[str, int],
        user_ids: list,
        reject_add_request: bool = False,
    ) -> None: ...

    @abstractmethod
    async def set_group_remark(
        self, group_id: Union[str, int], remark: str
    ) -> None: ...

    @abstractmethod
    async def set_group_sign(self, group_id: Union[str, int]) -> None: ...

    @abstractmethod
    async def set_group_todo(
        self, group_id: Union[str, int], message_id: Union[str, int]
    ) -> None: ...

    @abstractmethod
    async def set_group_portrait(
        self, group_id: Union[str, int], file: str
    ) -> None: ...

    # ---- 账号操作 ----

    @abstractmethod
    async def set_friend_add_request(
        self, flag: str, approve: bool = True, remark: str = ""
    ) -> None: ...

    @abstractmethod
    async def set_group_add_request(
        self, flag: str, sub_type: str, approve: bool = True, reason: str = ""
    ) -> None: ...

    @abstractmethod
    async def set_friend_remark(
        self, user_id: Union[str, int], remark: str
    ) -> None: ...

    @abstractmethod
    async def delete_friend(self, user_id: Union[str, int]) -> None: ...

    @abstractmethod
    async def friend_poke(self, user_id: Union[str, int]) -> None: ...

    @abstractmethod
    async def set_self_longnick(self, long_nick: str) -> None: ...

    @abstractmethod
    async def set_qq_avatar(self, file: str) -> None: ...

    @abstractmethod
    async def set_qq_profile(
        self,
        nickname: str = "",
        company: str = "",
        email: str = "",
        college: str = "",
        personal_note: str = "",
    ) -> None: ...

    @abstractmethod
    async def set_online_status(
        self,
        status: OnlineStatus | int,
        ext_status: int = 0,
        custom_status: str = "",
        *,
        battery_status: int = 0,
    ) -> None: ...

    @abstractmethod
    async def ocr_image(self, image: str) -> OcrResult: ...

    # ---- 信息查询 (IQuery) ----

    @abstractmethod
    async def get_login_info(self) -> LoginInfo: ...

    @abstractmethod
    async def get_stranger_info(self, user_id: Union[str, int]) -> StrangerInfo: ...

    @abstractmethod
    async def get_friend_list(self) -> List[FriendInfo]: ...

    @abstractmethod
    async def get_group_info(self, group_id: Union[str, int]) -> GroupInfo: ...

    @abstractmethod
    async def get_group_list(self) -> List[GroupInfo]: ...

    @abstractmethod
    async def get_group_member_info(
        self, group_id: Union[str, int], user_id: Union[str, int]
    ) -> GroupMemberInfo: ...

    @abstractmethod
    async def get_group_member_list(
        self, group_id: Union[str, int]
    ) -> List[GroupMemberInfo]: ...

    @abstractmethod
    async def get_msg(self, message_id: Union[str, int]) -> MessageData: ...

    @abstractmethod
    async def get_forward_msg(
        self, message_id: Union[str, int]
    ) -> ForwardMessageData: ...

    @abstractmethod
    async def get_essence_msg_list(
        self, group_id: Union[str, int]
    ) -> List[EssenceMessage]: ...

    @abstractmethod
    async def get_group_honor_info(
        self, group_id: Union[str, int], type: str = "all"
    ) -> GroupHonorInfo: ...

    @abstractmethod
    async def get_group_at_all_remain(
        self, group_id: Union[str, int]
    ) -> GroupAtAllRemain: ...

    @abstractmethod
    async def get_group_shut_list(
        self, group_id: Union[str, int]
    ) -> List[GroupShutInfo]: ...

    @abstractmethod
    async def get_group_system_msg(self) -> GroupSystemMsg: ...

    @abstractmethod
    async def get_group_info_ex(self, group_id: Union[str, int]) -> GroupInfoEx: ...

    @abstractmethod
    async def get_group_file_system_info(
        self, group_id: Union[str, int]
    ) -> GroupFileSystemInfo: ...

    @abstractmethod
    async def get_group_files_by_folder(
        self, group_id: Union[str, int], folder_id: str
    ) -> GroupFileList: ...

    @abstractmethod
    async def get_private_file_url(
        self, user_id: Union[str, int], file_id: str
    ) -> str: ...

    @abstractmethod
    async def get_group_msg_history(
        self,
        group_id: Union[str, int],
        message_seq: Union[str, int, None] = None,
        count: int = 20,
    ) -> MessageHistory: ...

    @abstractmethod
    async def get_friend_msg_history(
        self,
        user_id: Union[str, int],
        message_seq: Union[str, int, None] = None,
        count: int = 20,
    ) -> MessageHistory: ...

    @abstractmethod
    async def get_file(self, file_id: str) -> FileData: ...

    @abstractmethod
    async def fetch_emoji_like(
        self,
        message_id: Union[str, int],
        emoji_id: str,
        emoji_type: str = "1",
        count: int = 20,
        cookie: str = "",
    ) -> EmojiLikeInfo: ...

    @abstractmethod
    async def get_emoji_likes(
        self,
        message_id: Union[str, int],
        emoji_id: str = "",
        count: int = 0,
    ) -> EmojiLikesResult: ...

    @abstractmethod
    async def get_version_info(self) -> VersionInfo: ...

    @abstractmethod
    async def get_status(self) -> BotStatus: ...

    @abstractmethod
    async def get_recent_contact(self, count: int = 10) -> List[RecentContact]: ...

    # ---- 文件操作 (IFileTransfer) ----

    @abstractmethod
    async def upload_group_file(
        self,
        group_id: Union[str, int],
        file: str,
        name: str,
        folder_id: str = "",
    ) -> None: ...

    @abstractmethod
    async def get_group_root_files(
        self, group_id: Union[str, int]
    ) -> GroupFileList: ...

    @abstractmethod
    async def get_group_file_url(
        self, group_id: Union[str, int], file_id: str
    ) -> str: ...

    @abstractmethod
    async def delete_group_file(
        self, group_id: Union[str, int], file_id: str
    ) -> None: ...

    @abstractmethod
    async def create_group_file_folder(
        self, group_id: Union[str, int], name: str, parent_id: str = ""
    ) -> CreateFolderResult: ...

    @abstractmethod
    async def delete_group_folder(
        self, group_id: Union[str, int], folder_id: str
    ) -> None: ...

    @abstractmethod
    async def upload_private_file(
        self, user_id: Union[str, int], file: str, name: str
    ) -> None: ...

    @abstractmethod
    async def download_file(
        self, url: str = "", file: str = "", headers: str = ""
    ) -> DownloadResult: ...

    # ---- 消息扩展操作 ----

    @abstractmethod
    async def set_msg_emoji_like(
        self, message_id: Union[str, int], emoji_id: str, set: bool = True
    ) -> None: ...

    @abstractmethod
    async def mark_group_msg_as_read(self, group_id: Union[str, int]) -> None: ...

    @abstractmethod
    async def mark_private_msg_as_read(self, user_id: Union[str, int]) -> None: ...

    @abstractmethod
    async def mark_all_as_read(self) -> None: ...

    @abstractmethod
    async def forward_friend_single_msg(
        self, user_id: Union[str, int], message_id: Union[str, int]
    ) -> None: ...

    @abstractmethod
    async def forward_group_single_msg(
        self, group_id: Union[str, int], message_id: Union[str, int]
    ) -> None: ...

    # ---- 辅助功能 ----

    @abstractmethod
    async def send_like(self, user_id: Union[str, int], times: int = 1) -> None: ...

    @abstractmethod
    async def send_poke(
        self, group_id: Union[str, int], user_id: Union[str, int]
    ) -> None: ...
