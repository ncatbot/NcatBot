"""
群管理员功能 API

提供群设置、公告、相册、头像等管理功能。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional, Union

from ..utils import APIComponent, APIReturnStatus, get_log

if TYPE_CHECKING:
    pass

LOG = get_log("GroupAdminMixin")


# =============================================================================
# 管理员功能 Mixin
# =============================================================================


class GroupAdminMixin(APIComponent):
    """群管理员功能相关方法"""

    # -------------------------------------------------------------------------
    # 群设置
    # -------------------------------------------------------------------------

    async def set_group_remark(self, group_id: Union[str, int], remark: str) -> None:
        """
        设置群备注

        Args:
            group_id: 群号
            remark: 备注内容
        """
        result = await self._request_raw(
            "/set_group_remark",
            {"group_id": group_id, "remark": remark},
        )
        APIReturnStatus.raise_if_failed(result)

    async def set_group_sign(self, group_id: Union[str, int]) -> None:
        """
        群签到

        Args:
            group_id: 群号
        """
        result = await self._request_raw(
            "/set_group_sign",
            {"group_id": group_id},
        )
        APIReturnStatus.raise_if_failed(result)

    async def send_group_sign(self, group_id: Union[str, int]) -> None:
        """
        发送群签到

        Args:
            group_id: 群号
        """
        result = await self._request_raw(
            "/send_group_sign",
            {"group_id": group_id},
        )
        APIReturnStatus.raise_if_failed(result)

    # -------------------------------------------------------------------------
    # 群相册
    # -------------------------------------------------------------------------

    async def get_group_album_list(self, group_id: Union[str, int]) -> List[dict]:
        """
        获取群相册列表

        Args:
            group_id: 群号

        Returns:
            List[dict]: 相册列表

        Raises:
            NapCatAPIError: 如果 NapCat 不支持此 API
        """
        result = await self._request_raw(
            "/get_qun_album_list",
            {"group_id": group_id},
        )
        status = APIReturnStatus(result)
        return status.data

    async def upload_image_to_group_album(
        self,
        group_id: Union[str, int],
        file: str,
        album_id: str = "",
        album_name: str = "",
    ) -> None:
        """
        上传图片到群相册

        Args:
            group_id: 群号
            file: 图片路径/URL
            album_id: 相册 ID
            album_name: 相册名称
        """
        # 预上传处理
        processed_file = await self._preupload_file(file, "image")

        result = await self._request_raw(
            "/upload_image_to_qun_album",
            {
                "group_id": group_id,
                "album_name": album_name,
                "album_id": album_id,
                "file": processed_file,
            },
        )
        APIReturnStatus.raise_if_failed(result)

    # -------------------------------------------------------------------------
    # 群管理
    # -------------------------------------------------------------------------

    async def set_group_avatar(self, group_id: Union[str, int], file: str) -> None:
        """
        设置群头像

        Args:
            group_id: 群号
            file: 图片 URL（目前仅支持 URL）
        """
        # 预上传处理
        processed_file = await self._preupload_file(file, "image")

        result = await self._request_raw(
            "/set_group_avatar",
            {"group_id": group_id, "file": processed_file},
        )
        APIReturnStatus.raise_if_failed(result)

    async def set_group_name(self, group_id: Union[str, int], name: str) -> None:
        """
        设置群名称

        Args:
            group_id: 群号
            name: 新群名
        """
        result = await self._request_raw(
            "/set_group_name",
            {"group_id": group_id, "group_name": name},
        )
        APIReturnStatus.raise_if_failed(result)

    async def _send_group_notice(
        self,
        group_id: Union[str, int],
        content: str,
        confirm_required: bool = False,
        image: Optional[str] = None,
        is_show_edit_card: bool = False,
        pinned: bool = False,
    ) -> None:
        """
        发送群公告（内部方法）

        Args:
            group_id: 群号
            content: 公告内容
            confirm_required: 是否需要确认
            image: 公告图片
            is_show_edit_card: 是否显示编辑卡片
            pinned: 是否置顶
        """
        result = await self._request_raw(
            "/_send_group_notice",
            {
                "group_id": group_id,
                "content": content,
                "confirm_required": 1 if confirm_required else 0,
                "image": image,
                "is_show_edit_card": 1 if is_show_edit_card else 0,
                "pinned": 1 if pinned else 0,
                "tip_window_type": 0,
                "type": 0,
            },
        )
        APIReturnStatus.raise_if_failed(result)

    async def set_group_todo(
        self, group_id: Union[str, int], message_id: Union[str, int]
    ) -> dict:
        """
        设置群待办

        Args:
            group_id: 群号
            message_id: 消息 ID

        Returns:
            dict: 响应结果
        """
        result = await self._request_raw(
            "/set_group_todo",
            {"group_id": group_id, "message_id": message_id},
        )
        APIReturnStatus.raise_if_failed(result)
        return result

    # -------------------------------------------------------------------------
    # 消息发送方法占位（由 MessageAPI 实现）
    # -------------------------------------------------------------------------

    async def send_group_image(self, group_id: Union[str, int], image: str) -> str:
        """发送群图片（应由 MessageAPI 实现）"""
        raise NotImplementedError("This method should be implemented by MessageAPI")

    async def send_group_record(self, group_id: Union[str, int], file: str) -> str:
        """发送群语音（应由 MessageAPI 实现）"""
        raise NotImplementedError("This method should be implemented by MessageAPI")

    async def send_group_video(self, group_id: Union[str, int], video: str) -> str:
        """发送群视频（应由 MessageAPI 实现）"""
        raise NotImplementedError("This method should be implemented by MessageAPI")

    async def send_group_file(self, group_id: Union[str, int], file: str) -> str:
        """发送群文件（应由 MessageAPI 实现）"""
        raise NotImplementedError("This method should be implemented by MessageAPI")
