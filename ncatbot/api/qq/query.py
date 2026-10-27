"""QQQuery — 信息查询功能分组"""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Literal, Union

from ncatbot.types import ImageAttachment
from ncatbot.types.napcat import (
    BotStatus,
    EmojiLikeInfo,
    EmojiLikesResult,
    EssenceMessage,
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
    GroupNotice,
    GroupShutInfo,
    GroupSystemMsg,
    LoginInfo,
    MessageData,
    OcrResult,
    PttTextResult,
    RecentContact,
    StrangerInfo,
    VersionInfo,
)

if TYPE_CHECKING:
    from .interface import IQQAPIClient


class QQQuery:
    """所有 get_* 查询操作"""

    __slots__ = ("_api",)

    def __init__(self, api: IQQAPIClient) -> None:
        self._api = api

    async def get_login_info(self) -> LoginInfo:
        return await self._api.get_login_info()

    async def get_stranger_info(self, user_id: Union[str, int]) -> StrangerInfo:
        return await self._api.get_stranger_info(user_id)

    async def get_friend_list(self) -> List[FriendInfo]:
        return await self._api.get_friend_list()

    async def get_group_info(self, group_id: Union[str, int]) -> GroupInfo:
        return await self._api.get_group_info(group_id)

    async def get_group_list(self) -> List[GroupInfo]:
        return await self._api.get_group_list()

    async def get_group_member_info(
        self, group_id: Union[str, int], user_id: Union[str, int]
    ) -> GroupMemberInfo:
        return await self._api.get_group_member_info(group_id, user_id)

    async def get_group_member_list(
        self, group_id: Union[str, int]
    ) -> List[GroupMemberInfo]:
        return await self._api.get_group_member_list(group_id)

    async def get_msg(self, message_id: Union[str, int]) -> MessageData:
        return await self._api.get_msg(message_id)

    async def get_forward_msg(self, message_id: Union[str, int]) -> ForwardMessageData:
        return await self._api.get_forward_msg(message_id)

    # ---- 群扩展查询 ----

    async def get_group_notice(self, group_id: Union[str, int]) -> List[GroupNotice]:
        return await self._api.get_group_notice(group_id)

    async def get_essence_msg_list(
        self, group_id: Union[str, int]
    ) -> List[EssenceMessage]:
        return await self._api.get_essence_msg_list(group_id)

    async def get_group_honor_info(
        self, group_id: Union[str, int], type: str = "all"
    ) -> GroupHonorInfo:
        return await self._api.get_group_honor_info(group_id, type)

    async def get_group_at_all_remain(
        self, group_id: Union[str, int]
    ) -> GroupAtAllRemain:
        return await self._api.get_group_at_all_remain(group_id)

    async def get_group_shut_list(
        self, group_id: Union[str, int]
    ) -> List[GroupShutInfo]:
        return await self._api.get_group_shut_list(group_id)

    async def get_group_system_msg(self) -> GroupSystemMsg:
        return await self._api.get_group_system_msg()

    async def get_group_info_ex(self, group_id: Union[str, int]) -> GroupInfoEx:
        return await self._api.get_group_info_ex(group_id)

    # ---- 文件查询 ----

    async def get_group_root_files(self, group_id: Union[str, int]) -> GroupFileList:
        return await self._api.get_group_root_files(group_id)

    async def get_group_file_url(self, group_id: Union[str, int], file_id: str) -> str:
        return await self._api.get_group_file_url(group_id, file_id)

    async def get_group_file_system_info(
        self, group_id: Union[str, int]
    ) -> GroupFileSystemInfo:
        return await self._api.get_group_file_system_info(group_id)

    async def get_group_files_by_folder(
        self, group_id: Union[str, int], folder_id: str
    ) -> GroupFileList:
        return await self._api.get_group_files_by_folder(group_id, folder_id)

    async def get_private_file_url(self, user_id: Union[str, int], file_id: str) -> str:
        return await self._api.get_private_file_url(user_id, file_id)

    async def get_file(self, file_id: str) -> FileData:
        return await self._api.get_file(file_id)

    # ---- Emoji 查询 ----

    async def fetch_emoji_like(
        self,
        message_id: Union[str, int],
        emoji_id: str,
        emoji_type: str = "1",
        count: int = 20,
        cookie: str = "",
    ) -> EmojiLikeInfo:
        return await self._api.fetch_emoji_like(
            message_id, emoji_id, emoji_type, count, cookie
        )

    async def get_emoji_likes(
        self,
        message_id: Union[str, int],
        emoji_id: str = "",
        count: int = 0,
    ) -> EmojiLikesResult:
        return await self._api.get_emoji_likes(message_id, emoji_id, count)

    # ---- 系统信息 ----

    async def get_version_info(self) -> VersionInfo:
        return await self._api.get_version_info()

    async def get_status(self) -> BotStatus:
        return await self._api.get_status()

    async def get_recent_contact(self, count: int = 10) -> List[RecentContact]:
        return await self._api.get_recent_contact(count)

    async def ocr_image(self, image: str) -> OcrResult:
        return await self._api.ocr_image(image)

    async def fetch_ptt_text(self, message_id: Union[str, int]) -> PttTextResult:
        """获取语音消息的转文字结果

        Parameters
        ----------
        message_id : str | int
            语音消息的消息 ID

        Returns
        -------
        PttTextResult
            转写文本位于 ``text`` 字段
        """
        return await self._api.fetch_ptt_text(message_id)

    # ---- 头像查询 ----

    async def get_user_avatar(
        self,
        user_id: Union[str, int],
        spec: Literal[40, 100, 640] = 640,
    ) -> ImageAttachment:
        """获取 QQ 用户头像

        通过 QQ 头像公开接口构造下载链接，返回 `ImageAttachment`。

        Parameters
        ----------
        user_id : str | int
            目标用户 QQ 号
        spec : 40 | 100 | 640
            头像尺寸（像素），默认 640
        """
        uid = int(user_id)
        url = f"http://q.qlogo.cn/headimg_dl?dst_uin={uid}&spec={spec}&img_type=jpg"
        return ImageAttachment(
            name=f"{uid}_avatar_{spec}.jpg",
            url=url,
            content_type="image/jpeg",
            width=spec,
            height=spec,
        )
