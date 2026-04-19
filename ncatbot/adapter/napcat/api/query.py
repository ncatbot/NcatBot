"""信息查询 API Mixin"""

from typing import List, Union

from ncatbot.types.napcat import (
    BotStatus,
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
    GroupShutInfo,
    GroupSystemMsg,
    LoginInfo,
    MessageData,
    MessageHistory,
    ForwardMessageData,
    RecentContact,
    StrangerInfo,
    VersionInfo,
)


class QueryAPIMixin:
    async def get_login_info(self) -> LoginInfo:
        data = await self._call_data("get_login_info") or {}
        return LoginInfo(**data)

    async def get_stranger_info(self, user_id: Union[str, int]) -> StrangerInfo:
        data = (
            await self._call_data("get_stranger_info", {"user_id": int(user_id)}) or {}
        )
        return StrangerInfo(**data)

    async def get_friend_list(self) -> List[FriendInfo]:
        data = await self._call_data("get_friend_list") or []
        return [FriendInfo(**item) for item in data]

    async def get_group_info(self, group_id: Union[str, int]) -> GroupInfo:
        data = (
            await self._call_data("get_group_info", {"group_id": int(group_id)}) or {}
        )
        return GroupInfo(**data)

    async def get_group_list(self) -> List[GroupInfo]:
        data = await self._call_data("get_group_list") or []
        return [GroupInfo(**item) for item in data]

    async def get_group_member_info(
        self,
        group_id: Union[str, int],
        user_id: Union[str, int],
    ) -> GroupMemberInfo:
        data = (
            await self._call_data(
                "get_group_member_info",
                {
                    "group_id": int(group_id),
                    "user_id": int(user_id),
                },
            )
            or {}
        )
        return GroupMemberInfo(**data)

    async def get_group_member_list(
        self, group_id: Union[str, int]
    ) -> List[GroupMemberInfo]:
        data = (
            await self._call_data("get_group_member_list", {"group_id": int(group_id)})
            or []
        )
        return [GroupMemberInfo(**item) for item in data]

    async def get_msg(self, message_id: Union[str, int]) -> MessageData:
        data = await self._call_data("get_msg", {"message_id": int(message_id)}) or {}
        return MessageData(**data)

    async def get_forward_msg(self, message_id: Union[str, int]) -> ForwardMessageData:
        data = (
            await self._call_data("get_forward_msg", {"message_id": int(message_id)})
            or {}
        )
        return ForwardMessageData(**data)

    # ---- 群扩展查询 ----

    async def get_essence_msg_list(
        self, group_id: Union[str, int]
    ) -> List[EssenceMessage]:
        data = (
            await self._call_data("get_essence_msg_list", {"group_id": int(group_id)})
            or []
        )
        return [EssenceMessage(**item) for item in data]

    async def get_group_honor_info(
        self, group_id: Union[str, int], type: str = "all"
    ) -> GroupHonorInfo:
        data = (
            await self._call_data(
                "get_group_honor_info",
                {"group_id": int(group_id), "type": type},
            )
            or {}
        )
        return GroupHonorInfo(**data)

    async def get_group_at_all_remain(
        self, group_id: Union[str, int]
    ) -> GroupAtAllRemain:
        data = (
            await self._call_data(
                "get_group_at_all_remain", {"group_id": int(group_id)}
            )
            or {}
        )
        return GroupAtAllRemain(**data)

    async def get_group_shut_list(
        self, group_id: Union[str, int]
    ) -> List[GroupShutInfo]:
        data = (
            await self._call_data("get_group_shut_list", {"group_id": int(group_id)})
            or []
        )
        return [GroupShutInfo(**item) for item in data]

    async def get_group_system_msg(self) -> GroupSystemMsg:
        data = await self._call_data("get_group_system_msg") or {}
        return GroupSystemMsg(**data)

    async def get_group_info_ex(self, group_id: Union[str, int]) -> GroupInfoEx:
        data = (
            await self._call_data("get_group_info_ex", {"group_id": int(group_id)})
            or {}
        )
        return GroupInfoEx(**data)

    # ---- 文件扩展查询 ----

    async def get_group_file_system_info(
        self, group_id: Union[str, int]
    ) -> GroupFileSystemInfo:
        data = (
            await self._call_data(
                "get_group_file_system_info", {"group_id": int(group_id)}
            )
            or {}
        )
        return GroupFileSystemInfo(**data)

    async def get_group_files_by_folder(
        self, group_id: Union[str, int], folder_id: str
    ) -> GroupFileList:
        data = (
            await self._call_data(
                "get_group_files_by_folder",
                {"group_id": int(group_id), "folder_id": folder_id},
            )
            or {}
        )
        return GroupFileList(**data)

    async def get_private_file_url(self, user_id: Union[str, int], file_id: str) -> str:
        data = await self._call_data(
            "get_private_file_url",
            {"user_id": int(user_id), "file_id": file_id},
        )
        return (data or {}).get("url", "")

    # ---- 消息查询扩展 ----

    async def get_group_msg_history(
        self,
        group_id: Union[str, int],
        message_seq: Union[str, int, None] = None,
        count: int = 20,
    ) -> MessageHistory:
        params: dict = {"group_id": int(group_id), "count": count}
        if message_seq is not None:
            params["message_seq"] = int(message_seq)
        data = await self._call_data("get_group_msg_history", params) or {}
        return MessageHistory(**data)

    async def get_friend_msg_history(
        self,
        user_id: Union[str, int],
        message_seq: Union[str, int, None] = None,
        count: int = 20,
    ) -> MessageHistory:
        params: dict = {"user_id": int(user_id), "count": count}
        if message_seq is not None:
            params["message_seq"] = int(message_seq)
        data = await self._call_data("get_friend_msg_history", params) or {}
        return MessageHistory(**data)

    async def get_file(self, file_id: str) -> FileData:
        data = await self._call_data("get_file", {"file_id": file_id}) or {}
        return FileData(**data)

    async def fetch_emoji_like(
        self,
        message_id: Union[str, int],
        emoji_id: str,
        emoji_type: str = "1",
        count: int = 20,
        cookie: str = "",
    ) -> EmojiLikeInfo:
        params: dict = {
            "message_id": int(message_id),
            "emojiId": emoji_id,
            "emojiType": emoji_type,
            "count": count,
            "cookie": cookie,
        }
        data = await self._call_data("fetch_emoji_like", params) or {}
        return EmojiLikeInfo(**data)

    async def get_emoji_likes(
        self,
        message_id: Union[str, int],
        emoji_id: str = "",
        count: int = 0,
    ) -> EmojiLikesResult:
        params: dict = {"message_id": int(message_id), "count": count}
        if emoji_id:
            params["emoji_id"] = emoji_id
        data = await self._call_data("get_emoji_likes", params) or {}
        return EmojiLikesResult(**data)

    # ---- 系统信息 ----

    async def get_version_info(self) -> VersionInfo:
        data = await self._call_data("get_version_info") or {}
        return VersionInfo(**data)

    async def get_status(self) -> BotStatus:
        data = await self._call_data("get_status") or {}
        return BotStatus(**data)

    async def get_recent_contact(self, count: int = 10) -> List[RecentContact]:
        data = await self._call_data("get_recent_contact", {"count": count}) or []
        return [RecentContact(**item) for item in data]
