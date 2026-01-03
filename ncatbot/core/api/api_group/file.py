"""
群文件管理 API

提供群文件的上传、下载、移动、删除等功能。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Union

from ..utils import APIComponent, APIReturnStatus, get_log

if TYPE_CHECKING:
    from ncatbot.core import File

LOG = get_log("GroupFileMixin")


# =============================================================================
# 文件管理 Mixin
# =============================================================================


class GroupFileMixin(APIComponent):
    """群文件管理相关方法"""

    async def move_group_file(
        self,
        group_id: Union[str, int],
        file_id: str,
        current_parent_directory: str,
        target_parent_directory: str,
    ) -> None:
        """
        移动群文件

        Args:
            group_id: 群号
            file_id: 文件 ID
            current_parent_directory: 当前父目录
            target_parent_directory: 目标父目录
        """
        result = await self._request_raw(
            "/move_group_file",
            {
                "group_id": group_id,
                "file_id": file_id,
                "current_parent_directory": current_parent_directory,
                "target_parent_directory": target_parent_directory,
            },
        )
        APIReturnStatus.raise_if_failed(result)

    async def trans_group_file(self, group_id: Union[str, int], file_id: str) -> None:
        """
        转存群文件为永久文件

        Args:
            group_id: 群号
            file_id: 文件 ID
        """
        result = await self._request_raw(
            "/trans_group_file",
            {"group_id": group_id, "file_id": file_id},
        )
        APIReturnStatus.raise_if_failed(result)

    async def rename_group_file(
        self,
        group_id: Union[str, int],
        file_id: str,
        new_name: str,
    ) -> None:
        """
        重命名群文件

        Args:
            group_id: 群号
            file_id: 文件 ID
            new_name: 新文件名
        """
        result = await self._request_raw(
            "/rename_group_file",
            {"group_id": group_id, "file_id": file_id, "new_name": new_name},
        )
        APIReturnStatus.raise_if_failed(result)

    async def get_file(self, file_id: str, file: str) -> "File":
        """
        获取文件信息

        Args:
            file_id: 文件 ID
            file: 文件标识

        Returns:
            File: 文件对象
        """
        from ncatbot.core import File as FileClass

        result = await self._request_raw(
            "/get_file",
            {"file_id": file_id, "file": file},
        )
        status = APIReturnStatus(result)
        segment = FileClass.from_dict({"type": "file", "data": status.data})
        return segment  # type: ignore

    async def upload_group_file(
        self,
        group_id: Union[str, int],
        file: str,
        name: str,
        folder: Optional[str] = None,
    ) -> None:
        """
        上传群文件

        Args:
            group_id: 群号
            file: 文件路径/URL
            name: 文件名
            folder: 目标文件夹
        """
        # 预上传处理
        processed_file = await self._preupload_file(file, "file")

        result = await self._request_raw(
            "/upload_group_file",
            {
                "group_id": group_id,
                "file": processed_file,
                "name": name,
                "folder": folder,
            },
        )
        APIReturnStatus.raise_if_failed(result)

    async def post_group_file(
        self,
        group_id: Union[str, int],
        image: Optional[str] = None,
        record: Optional[str] = None,
        video: Optional[str] = None,
        file: Optional[str] = None,
    ) -> str:
        """
        以消息形式发送群文件（便捷方法）

        Args:
            group_id: 目标群号
            image: 图片路径/URL
            record: 语音路径/URL
            video: 视频路径/URL
            file: 文件路径/URL

        Returns:
            str: 消息 ID

        Note:
            四个参数中必须且只能提供一个
        """
        from ..utils import require_exactly_one
        from ..api_message.group_send import GroupMessageMixin

        require_exactly_one(
            image,
            record,
            video,
            file,
            names=["image", "record", "video", "file"],
        )

        # 获取 GroupMessageMixin 的方法
        if image is not None:
            return await GroupMessageMixin.send_group_image(self, group_id, image)  # type: ignore
        elif record is not None:
            return await GroupMessageMixin.send_group_record(self, group_id, record)  # type: ignore
        elif video is not None:
            return await GroupMessageMixin.send_group_video(self, group_id, video)  # type: ignore
        else:
            return await GroupMessageMixin.send_group_file(self, group_id, file)  # type: ignore

    async def create_group_file_folder(
        self, group_id: Union[str, int], folder_name: str
    ) -> None:
        """
        创建群文件文件夹

        Args:
            group_id: 群号
            folder_name: 文件夹名称
        """
        result = await self._request_raw(
            "/create_group_file_folder",
            {"group_id": group_id, "folder_name": folder_name},
        )
        APIReturnStatus.raise_if_failed(result)

    async def group_file_folder_makedir(
        self, group_id: Union[str, int], path: str
    ) -> Optional[str]:
        """
        按路径创建群文件夹（自定义函数）

        Args:
            group_id: 群号
            path: 文件夹路径

        Returns:
            Optional[str]: 创建结果
        """
        # TODO: 实现此功能
        return None

    async def delete_group_file(self, group_id: Union[str, int], file_id: str) -> None:
        """
        删除群文件

        Args:
            group_id: 群号
            file_id: 文件 ID
        """
        result = await self._request_raw(
            "/delete_group_file",
            {"group_id": group_id, "file_id": file_id},
        )
        APIReturnStatus.raise_if_failed(result)

    async def delete_group_folder(
        self, group_id: Union[str, int], folder_id: str
    ) -> None:
        """
        删除群文件夹

        Args:
            group_id: 群号
            folder_id: 文件夹 ID
        """
        result = await self._request_raw(
            "/delete_group_folder",
            {"group_id": group_id, "folder_id": folder_id},
        )
        APIReturnStatus.raise_if_failed(result)

    async def get_group_root_files(
        self, group_id: Union[str, int], file_count: int = 50
    ) -> dict:
        """
        获取群根目录文件列表

        Args:
            group_id: 群号
            file_count: 获取数量

        Returns:
            dict: 文件列表
        """
        result = await self._request_raw(
            "/get_group_root_files",
            {"group_id": group_id, "file_count": file_count},
        )
        status = APIReturnStatus(result)
        return status.data

    async def get_group_files_by_folder(
        self,
        group_id: Union[str, int],
        folder_id: str,
        file_count: int = 50,
    ) -> dict:
        """
        获取群文件夹内文件列表

        Args:
            group_id: 群号
            folder_id: 文件夹 ID
            file_count: 获取数量

        Returns:
            dict: 文件列表
        """
        result = await self._request_raw(
            "/get_group_files_by_folder",
            {"group_id": group_id, "folder_id": folder_id, "file_count": file_count},
        )
        status = APIReturnStatus(result)
        return status.data

    async def get_group_file_url(self, group_id: Union[str, int], file_id: str) -> str:
        """
        获取群文件下载链接

        Args:
            group_id: 群号
            file_id: 文件 ID

        Returns:
            str: 下载 URL
        """
        result = await self._request_raw(
            "/get_group_file_url",
            {"group_id": group_id, "file_id": file_id},
        )
        status = APIReturnStatus(result)
        return status.data.get("url")
