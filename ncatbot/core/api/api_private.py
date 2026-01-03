"""
私聊相关 API

提供私聊文件上传、输入状态等功能。
"""

from __future__ import annotations

from typing import Optional, TYPE_CHECKING, Union

from .utils import (
    APIComponent,
    APIReturnStatus,
    generate_sync_methods,
    require_exactly_one,
    get_log,
)

if TYPE_CHECKING:
    pass

LOG = get_log("PrivateAPI")


# =============================================================================
# PrivateAPI 实现
# =============================================================================


@generate_sync_methods
class PrivateAPI(APIComponent):
    """
    私聊相关 API

    提供私聊文件上传、输入状态等功能。
    """

    # -------------------------------------------------------------------------
    # region 文件
    # -------------------------------------------------------------------------

    async def upload_private_file(
        self,
        user_id: Union[str, int],
        file: str,
        name: str,
    ) -> None:
        """
        上传私聊文件

        Args:
            user_id: 目标用户 QQ 号
            file: 文件路径/URL
            name: 文件名
        """
        # 预上传处理
        processed_file = await self._preupload_file(file, "file")

        result = await self._request_raw(
            "/upload_private_file",
            {"user_id": user_id, "file": processed_file, "name": name},
        )
        APIReturnStatus.raise_if_failed(result)

    async def get_private_file_url(self, file_id: str) -> str:
        """
        获取私聊文件下载链接

        Args:
            file_id: 文件 ID

        Returns:
            str: 下载 URL
        """
        result = await self._request_raw(
            "/get_private_file_url",
            {"file_id": file_id},
        )
        status = APIReturnStatus(result)
        return status.data.get("url")

    async def post_private_file(
        self,
        user_id: Union[str, int],
        image: Optional[str] = None,
        record: Optional[str] = None,
        video: Optional[str] = None,
        file: Optional[str] = None,
    ) -> str:
        """
        上传私聊文件（便捷方法）

        Args:
            user_id: 目标用户 QQ 号
            image: 图片路径/URL
            record: 语音路径/URL
            video: 视频路径/URL
            file: 文件路径/URL

        Returns:
            str: 消息 ID

        Note:
            四个参数中必须且只能提供一个
        """
        require_exactly_one(
            image,
            record,
            video,
            file,
            names=["image", "record", "video", "file"],
        )

        if image is not None:
            return await self.send_private_image(user_id, image)
        elif record is not None:
            return await self.send_private_record(user_id, record)
        elif video is not None:
            return await self.send_private_video(user_id, video)
        else:
            return await self.send_private_file(user_id, file)

    # -------------------------------------------------------------------------
    # region 其它
    # -------------------------------------------------------------------------

    async def set_input_status(
        self,
        event_type: int,
        user_id: Union[str, int],
    ) -> None:
        """
        设置输入状态

        Args:
            event_type: 事件类型
                - 0: "对方正在说话"
                - 1: "对方正在输入"
            user_id: 目标用户 QQ 号
        """
        result = await self._request_raw(
            "/set_input_status",
            {"event_type": event_type, "user_id": user_id},
        )
        APIReturnStatus.raise_if_failed(result)

    # -------------------------------------------------------------------------
    # region 占位方法（由 MessageAPI 实现）
    # -------------------------------------------------------------------------

    async def send_private_image(self, user_id: Union[str, int], image: str) -> str:
        """发送私聊图片（应由 MessageAPI 实现）"""
        raise NotImplementedError("This method should be implemented by MessageAPI")

    async def send_private_record(self, user_id: Union[str, int], file: str) -> str:
        """发送私聊语音（应由 MessageAPI 实现）"""
        raise NotImplementedError("This method should be implemented by MessageAPI")

    async def send_private_video(self, user_id: Union[str, int], video: str) -> str:
        """发送私聊视频（应由 MessageAPI 实现）"""
        raise NotImplementedError("This method should be implemented by MessageAPI")

    async def send_private_file(self, user_id: Union[str, int], file: str) -> str:
        """发送私聊文件（应由 MessageAPI 实现）"""
        raise NotImplementedError("This method should be implemented by MessageAPI")
