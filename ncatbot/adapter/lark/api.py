"""飞书 Bot API — 基于 lark-oapi SDK 的二次封装"""

from __future__ import annotations

import json
from typing import Any, IO, Optional, TYPE_CHECKING
from uuid import uuid4

from ncatbot.api.base import IAPIClient
from ncatbot.utils import get_log

if TYPE_CHECKING:
    from ncatbot.types import MessageArray

LOG = get_log("LarkBotAPI")


class LarkBotAPI(IAPIClient):
    """飞书平台 API 客户端

    封装 lark-oapi 的同步 API 调用为 async 接口。
    """

    def __init__(self, client: Any) -> None:
        """
        Args:
            client: lark_oapi.Client 实例
        """
        self._client = client

    @property
    def platform(self) -> str:
        return "lark"

    async def call(self, action: str, params: Optional[dict] = None) -> Any:
        """通用 API 调用（飞书不直接支持通用 action，预留扩展点）"""
        raise NotImplementedError(f"飞书不支持通用 action 调用: {action}")

    async def send_message(
        self,
        receive_id: str,
        receive_id_type: str = "chat_id",
        msg_type: str = "text",
        content: str = "",
    ) -> Any:
        """发送消息

        Args:
            receive_id: 接收者 ID（chat_id / open_id / user_id / union_id / email）
            receive_id_type: ID 类型
            msg_type: 消息类型，如 "text"
            content: 消息内容 JSON 字符串
        """
        import asyncio

        import lark_oapi as lark
        from lark_oapi.api.im.v1 import (
            CreateMessageRequest,
            CreateMessageRequestBody,
        )

        uid = str(uuid4())
        request = (
            CreateMessageRequest.builder()
            .receive_id_type(receive_id_type)
            .request_body(
                CreateMessageRequestBody.builder()
                .receive_id(receive_id)
                .msg_type(msg_type)
                .content(content)
                .uuid(uid)
                .build()
            )
            .build()
        )

        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None, self._client.im.v1.message.create, request
        )

        if not response.success():
            LOG.error(
                "发送消息失败: code=%s, msg=%s",
                response.code,
                response.msg,
            )
            return None

        LOG.debug("消息发送成功: %s", lark.JSON.marshal(response.data))
        return response.data

    async def send_text(
        self, receive_id: str, text: str, receive_id_type: str = "chat_id"
    ) -> Any:
        """发送文本消息的便捷方法"""
        content = json.dumps({"text": text})
        return await self.send_message(
            receive_id=receive_id,
            receive_id_type=receive_id_type,
            msg_type="text",
            content=content,
        )

    async def reply_message(
        self,
        message_id: str,
        msg_type: str = "text",
        content: str = "",
    ) -> Any:
        """回复消息（引用回复）

        Args:
            message_id: 要回复的消息 ID
            msg_type: 消息类型，如 "text"
            content: 消息内容 JSON 字符串
        """
        import asyncio

        import lark_oapi as lark
        from lark_oapi.api.im.v1 import (
            ReplyMessageRequest,
            ReplyMessageRequestBody,
        )

        uid = str(uuid4())
        request = (
            ReplyMessageRequest.builder()
            .message_id(message_id)
            .request_body(
                ReplyMessageRequestBody.builder()
                .msg_type(msg_type)
                .content(content)
                .uuid(uid)
                .build()
            )
            .build()
        )

        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None, self._client.im.v1.message.reply, request
        )

        if not response.success():
            LOG.error(
                "回复消息失败: code=%s, msg=%s",
                response.code,
                response.msg,
            )
            return None

        LOG.debug("回复消息成功: %s", lark.JSON.marshal(response.data))
        return response.data

    async def reply_text(self, message_id: str, text: str) -> Any:
        """回复文本消息的便捷方法"""
        content = json.dumps({"text": text})
        return await self.reply_message(
            message_id=message_id,
            msg_type="text",
            content=content,
        )

    # ---- 富文本 (post) 消息 ----

    async def send_post(
        self,
        receive_id: str,
        content: str,
        receive_id_type: str = "chat_id",
    ) -> Any:
        """发送富文本 (post) 消息

        Args:
            receive_id: 接收者 ID
            content: post 格式 JSON 字符串
            receive_id_type: ID 类型
        """
        return await self.send_message(
            receive_id=receive_id,
            receive_id_type=receive_id_type,
            msg_type="post",
            content=content,
        )

    async def reply_post(
        self,
        message_id: str,
        content: str,
    ) -> Any:
        """引用回复富文本 (post) 消息

        Args:
            message_id: 要回复的消息 ID
            content: post 格式 JSON 字符串
        """
        return await self.reply_message(
            message_id=message_id,
            msg_type="post",
            content=content,
        )

    async def send_msg_array(
        self,
        receive_id: str,
        msg: "MessageArray",
        title: str = "",
        receive_id_type: str = "chat_id",
    ) -> Any:
        """将 MessageArray 转为飞书 post 格式发送

        如果 MessageArray 仅包含纯文本，则以 text 消息类型发送。
        否则转为 post 富文本发送。
        """
        from ncatbot.types.common.segment.text import PlainText
        from .post_builder import message_array_to_post

        # 仅纯文本 → 走 text 类型（更轻量）
        if all(isinstance(s, PlainText) for s in msg):
            return await self.send_text(
                receive_id=receive_id,
                text=msg.text,
                receive_id_type=receive_id_type,
            )

        content = message_array_to_post(msg, title=title)
        return await self.send_post(
            receive_id=receive_id,
            content=content,
            receive_id_type=receive_id_type,
        )

    async def reply_msg_array(
        self,
        message_id: str,
        msg: "MessageArray",
        title: str = "",
    ) -> Any:
        """将 MessageArray 转为飞书 post 格式引用回复

        如果 MessageArray 仅包含纯文本，则以 text 消息类型回复。
        否则转为 post 富文本回复。
        """
        from ncatbot.types.common.segment.text import PlainText
        from .post_builder import message_array_to_post

        if all(isinstance(s, PlainText) for s in msg):
            return await self.reply_text(
                message_id=message_id,
                text=msg.text,
            )

        content = message_array_to_post(msg, title=title)
        return await self.reply_post(
            message_id=message_id,
            content=content,
        )

    # ---- 撤回消息 ----

    async def delete_message(self, message_id: str) -> Any:
        """撤回（删除）消息

        Args:
            message_id: 要撤回的消息 ID
        """
        import asyncio

        from lark_oapi.api.im.v1 import DeleteMessageRequest

        request = DeleteMessageRequest.builder().message_id(message_id).build()

        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None, self._client.im.v1.message.delete, request
        )

        if not response.success():
            LOG.error(
                "撤回消息失败: code=%s, msg=%s",
                response.code,
                response.msg,
            )
            return None

        LOG.debug("撤回消息成功: message_id=%s", message_id)
        return response.data

    # ---- 上传文件 ----

    async def upload_file(
        self,
        file_type: str,
        file_name: str,
        file: IO[Any],
        duration: Optional[int] = None,
    ) -> Any:
        """上传文件到飞书

        Args:
            file_type: 文件类型，如 "opus" / "mp4" / "pdf" / "doc" / "xls" / "ppt" / "stream"
            file_name: 文件名
            file: 文件对象（IO）
            duration: 音视频时长（毫秒），仅 opus / mp4 类型需要

        Returns:
            response.data（包含 file_key 等）
        """
        import asyncio

        from lark_oapi.api.im.v1 import (
            CreateFileRequest,
            CreateFileRequestBody,
        )

        body_builder = (
            CreateFileRequestBody.builder()
            .file_type(file_type)
            .file_name(file_name)
            .file(file)
        )
        if duration is not None:
            body_builder = body_builder.duration(duration)

        request = CreateFileRequest.builder().request_body(body_builder.build()).build()

        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None, self._client.im.v1.file.create, request
        )

        if not response.success():
            LOG.error(
                "上传文件失败: code=%s, msg=%s",
                response.code,
                response.msg,
            )
            return None

        LOG.debug("上传文件成功: %s", file_name)
        return response.data
