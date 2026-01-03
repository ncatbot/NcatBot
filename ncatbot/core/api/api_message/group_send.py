"""
群消息发送 API

提供群消息的各种发送功能，包括文本、图片、语音、文件、音乐等。
"""

from __future__ import annotations

from typing import List, Optional, Union, TYPE_CHECKING
from ...event import MessageArray, Record, File
from ..utils import (
    APIComponent,
    MessageAPIReturnStatus,
    get_log,
)
from .validation import validate_msg

if TYPE_CHECKING:
    from ...event import MessageArray

LOG = get_log("ncatbot.core.api.api_message.group_send")


# =============================================================================
# 群消息发送 Mixin
# =============================================================================


class GroupMessageMixin(APIComponent):
    """群消息发送相关方法"""

    async def send_group_msg(
        self, group_id: Union[str, int], message: List[dict]
    ) -> str:
        """
        发送群消息（底层接口）

        此方法会自动处理消息中的文件预上传。

        Args:
            group_id: 群号
            message: 消息内容列表

        Returns:
            str: 消息 ID
        """
        if not validate_msg(message):
            LOG.warning("消息格式验证失败，发送群聊消息取消")
            return ""

        # 预上传处理
        processed_message = await self._preupload_message(message)

        result = await self._request_raw(
            "/send_group_msg",
            {"group_id": group_id, "message": processed_message},
        )
        status = MessageAPIReturnStatus(result)
        return status.message_id

    async def post_group_array_msg(
        self, group_id: Union[str, int], msg: "MessageArray"
    ) -> str:
        """
        发送群消息（MessageArray）

        Args:
            group_id: 群号
            msg: MessageArray 消息对象

        Returns:
            str: 消息 ID
        """
        return await self.send_group_msg(group_id, msg.to_list())

    async def post_all_group_array_msg(self, msg: "MessageArray"):
        """TODO: 发送群消息到所有群"""
        pass

    async def post_group_msg(
        self,
        group_id: Union[str, int],
        text: Optional[str] = None,
        at: Optional[Union[str, int]] = None,
        reply: Optional[Union[str, int]] = None,
        image: Optional[str] = None,
        rtf: Optional["MessageArray"] = None,
    ) -> str:
        """
        发送群消息（便捷方法）

        Args:
            group_id: 群号
            text: 文本内容
            at: @某人的 QQ 号
            reply: 回复的消息 ID
            image: 图片路径/URL
            rtf: 富文本 MessageArray

        Returns:
            str: 消息 ID
        """
        from ...event import MessageArray, Image

        msg_array = MessageArray()
        if reply is not None:
            msg_array.add_reply(reply)
        if at is not None:
            msg_array.add_at(at)
        if text is not None:
            msg_array.add_text(text)
        if image is not None:
            msg_array.add_by_segment(Image(file=image))
        if rtf is not None:
            msg_array += rtf
        return await self.post_group_array_msg(group_id, msg_array)

    async def send_group_text(self, group_id: Union[str, int], text: str) -> str:
        """
        发送群文本消息（支持 CQ 码）

        Args:
            group_id: 群号
            text: 文本内容

        Returns:
            str: 消息 ID
        """
        return await self.post_group_msg(group_id, text=text)

    async def send_group_plain_text(self, group_id: Union[str, int], text: str) -> str:
        """
        发送群纯文本消息（不转义）

        Args:
            group_id: 群号
            text: 文本内容

        Returns:
            str: 消息 ID
        """
        return await self.send_group_msg(
            group_id, [{"type": "text", "data": {"text": text}}]
        )

    async def send_group_image(self, group_id: Union[str, int], image: str) -> str:
        """
        发送群图片消息

        Args:
            group_id: 群号
            image: 图片路径/URL

        Returns:
            str: 消息 ID
        """
        return await self.post_group_msg(group_id, image=image)

    async def send_group_record(self, group_id: Union[str, int], file: str) -> str:
        """
        发送群语音消息

        Args:
            group_id: 群号
            file: 语音文件路径/URL

        Returns:
            str: 消息 ID
        """
        # 统一走 send_group_msg 以确保预上传
        return await self.send_group_msg(group_id, [Record(file=file).to_dict()])

    async def send_group_dice(self, group_id: Union[str, int], value: int = 1):
        """TODO: 发送群掷骰子消息"""
        pass

    async def send_group_rps(self, group_id: Union[str, int], value: int = 1):
        """TODO: 发送群猜拳消息"""

    async def send_group_file(
        self,
        group_id: Union[str, int],
        file: str,
        name: Optional[str] = None,
    ) -> str:
        """
        发送群文件消息

        Args:
            group_id: 群号
            file: 文件路径/URL
            name: 文件名

        Returns:
            str: 消息 ID
        """
        # 统一走 send_group_msg 以确保预上传
        return await self.send_group_msg(
            group_id, [File(file=file, file_name=name).to_dict()]
        )
