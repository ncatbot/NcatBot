"""
NapCat IQQAPIClient 实现

组合所有 Mixin 并提供 _call / _call_data 入口。
"""

from __future__ import annotations

from typing import Any, Optional, Union, TYPE_CHECKING

from ncatbot.api.qq import IQQAPIClient
from ncatbot.api.errors import raise_for_retcode
from ncatbot.types.napcat import OcrResult, SendMessageResult
from ncatbot.utils import get_log

from .message import MessageAPIMixin
from .group import GroupAPIMixin
from .account import AccountAPIMixin
from .query import QueryAPIMixin
from .file import FileAPIMixin

if TYPE_CHECKING:
    from ..connection.protocol import OB11Protocol

LOG = get_log("NapCatBotAPI")


class NapCatBotAPI(
    MessageAPIMixin,
    GroupAPIMixin,
    AccountAPIMixin,
    QueryAPIMixin,
    FileAPIMixin,
    IQQAPIClient,
):
    """NapCat 平台的 IQQAPIClient 实现"""

    @property
    def platform(self) -> str:
        return "qq"

    def __init__(self, protocol: "OB11Protocol"):
        self._protocol = protocol
        from ..service.preupload import PreUploadService

        self._preupload = PreUploadService(protocol)

    async def call(self, action: str, params: Optional[dict] = None) -> dict:
        resp = await self._protocol.call(action, params)
        raise_for_retcode(resp, action=action)
        return resp

    _call = call  # alias for mixin compatibility

    async def _call_data(self, action: str, params: Optional[dict] = None) -> Any:
        resp = await self.call(action, params)
        return resp.get("data")

    async def _preupload_message(self, message: list) -> list:
        """对消息列表中的可下载资源执行预上传，返回处理后的消息列表"""
        result = await self._preupload.process_message_array(message)
        if result.uploaded_count > 0:
            LOG.info(f"预上传完成: 共上传 {result.uploaded_count} 个文件")
        if result.errors:
            LOG.warning(f"预上传部分失败: {result.errors}")
        return result.data.get("message", message) if result.data else message

    # ---- 重写消息发送，接入预上传 ----

    async def send_group_msg(
        self,
        group_id: Union[str, int],
        message: list,
        **kwargs: Any,
    ) -> SendMessageResult:
        message = await self._preupload_message(message)
        return await super().send_group_msg(group_id, message, **kwargs)

    async def send_private_msg(
        self,
        user_id: Union[str, int],
        message: list,
        **kwargs: Any,
    ) -> SendMessageResult:
        message = await self._preupload_message(message)
        return await super().send_private_msg(user_id, message, **kwargs)

    async def send_forward_msg(
        self,
        message_type: str,
        target_id: Union[str, int],
        messages: list,
        **kwargs: Any,
    ) -> SendMessageResult:
        result = await self._preupload.process_message_array(messages)
        if result.uploaded_count > 0:
            LOG.info(f"转发消息预上传完成: 共上传 {result.uploaded_count} 个文件")
        if result.errors:
            LOG.warning(f"转发消息预上传部分失败: {result.errors}")
        messages = result.data.get("message", messages) if result.data else messages
        return await super().send_forward_msg(
            message_type, target_id, messages, **kwargs
        )

    # ---- 重写文件类接口，接入预上传 ----

    async def upload_group_file(
        self,
        group_id: Union[str, int],
        file: str,
        name: str,
        folder_id: str = "",
    ) -> None:
        file = await self._preupload.preupload_file_if_needed(file, "file")
        return await super().upload_group_file(group_id, file, name, folder_id)

    async def upload_private_file(
        self,
        user_id: Union[str, int],
        file: str,
        name: str,
    ) -> None:
        file = await self._preupload.preupload_file_if_needed(file, "file")
        return await super().upload_private_file(user_id, file, name)

    async def set_qq_avatar(self, file: str) -> None:
        file = await self._preupload.preupload_file_if_needed(file, "image")
        return await super().set_qq_avatar(file)

    async def ocr_image(self, image: str) -> OcrResult:
        image = await self._preupload.preupload_file_if_needed(image, "image")
        return await super().ocr_image(image)

    async def send_group_notice(
        self,
        group_id: Union[str, int],
        content: str,
        image: str = "",
    ) -> None:
        if image:
            image = await self._preupload.preupload_file_if_needed(image, "image")
        return await super().send_group_notice(group_id, content, image)

    async def set_group_portrait(self, group_id: Union[str, int], file: str) -> None:
        file = await self._preupload.preupload_file_if_needed(file, "image")
        return await super().set_group_portrait(group_id, file)

    # ---- 辅助功能 ----

    async def send_like(self, user_id: Union[str, int], times: int = 1) -> None:
        await self._call("send_like", {"user_id": int(user_id), "times": times})

    async def send_poke(
        self,
        group_id: Union[str, int],
        user_id: Union[str, int],
    ) -> None:
        await self._call(
            "group_poke",
            {
                "group_id": int(group_id),
                "user_id": int(user_id),
            },
        )
