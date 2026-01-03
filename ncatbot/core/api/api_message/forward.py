"""
合并转发消息 API

提供合并转发消息的发送功能。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional, Union

from ..utils import APIComponent, MessageAPIReturnStatus, check_exclusive_argument
from ncatbot.utils import NcatBotValueError

if TYPE_CHECKING:
    from ncatbot.core import GroupMessageEvent, Forward


# =============================================================================
# 合并转发消息 Mixin
# =============================================================================


class ForwardMessageMixin(APIComponent):
    """合并转发消息相关方法"""

    async def send_forward_msg(
        self,
        group_id: Optional[Union[str, int]] = None,
        user_id: Optional[Union[str, int]] = None,
        messages: Optional[List["GroupMessageEvent"]] = None,
        news: Optional[List[str]] = None,
        prompt: Optional[str] = None,
        summary: Optional[str] = None,
        source: Optional[str] = None,
    ) -> str:
        """
        发送合并转发消息（底层接口）

        Args:
            group_id: 群号（与 user_id 二选一）
            user_id: 用户 QQ 号（与 group_id 二选一）
            messages: 消息内容列表
            news: 预览文本列表
            prompt: 提示文本
            summary: 摘要文本
            source: 来源文本

        Returns:
            str: 消息 ID
        """
        check_exclusive_argument(
            group_id, user_id, names=["group_id", "user_id"], error=True
        )

        data = {
            "messages": messages,
            "news": news,
            "prompt": prompt,
            "summary": summary,
            "source": source,
        }
        if group_id is not None:
            data["group_id"] = str(group_id)
        else:
            data["user_id"] = str(user_id)

        result = await self._request_raw("/send_forward_msg", data)
        status = MessageAPIReturnStatus(result)
        return status.message_id

    async def post_forward_msg(
        self,
        group_id: Optional[Union[str, int]] = None,
        user_id: Optional[Union[str, int]] = None,
        msg: Optional["Forward"] = None,
    ) -> str:
        """
        发送合并转发消息（Forward 对象）

        Args:
            group_id: 群号（与 user_id 二选一）
            user_id: 用户 QQ 号（与 group_id 二选一）
            msg: Forward 消息对象

        Returns:
            str: 消息 ID
        """
        if msg is None:
            raise NcatBotValueError("msg", "None")
        return await self.send_forward_msg(group_id, user_id, **msg.to_forward_dict())

    async def post_group_forward_msg(
        self, group_id: Union[str, int], forward: "Forward"
    ) -> str:
        """
        发送群合并转发消息

        Args:
            group_id: 群号
            forward: Forward 消息对象

        Returns:
            str: 消息 ID
        """
        return await self.post_forward_msg(group_id=group_id, msg=forward)

    async def post_private_forward_msg(
        self, user_id: Union[str, int], forward: "Forward"
    ) -> str:
        """
        发送私聊合并转发消息

        Args:
            user_id: 用户 QQ 号
            forward: Forward 消息对象

        Returns:
            str: 消息 ID
        """
        return await self.post_forward_msg(user_id=user_id, msg=forward)

    async def send_group_forward_msg(
        self,
        group_id: Union[str, int],
        messages: List[dict],
        news: List[str],
        prompt: str,
        summary: str,
        source: str,
    ) -> str:
        """
        发送群合并转发消息

        Args:
            group_id: 群号
            messages: 消息内容列表
            news: 预览文本列表
            prompt: 提示文本
            summary: 摘要文本
            source: 来源文本

        Returns:
            str: 消息 ID
        """
        result = await self._request_raw(
            "/send_group_forward_msg",
            {
                "group_id": group_id,
                "messages": messages,
                "news": news,
                "prompt": prompt,
                "summary": summary,
                "source": source,
            },
        )
        status = MessageAPIReturnStatus(result)
        return status.message_id

    async def send_group_forward_msg_by_id(
        self,
        group_id: Union[str, int],
        messages: List[Union[str, int]],
    ) -> str:
        """
        通过消息 ID 发送群合并转发

        Args:
            group_id: 群号
            messages: 消息 ID 列表

        Returns:
            str: 消息 ID
        """
        from ncatbot.core.helper import ForwardConstructor

        info = await self.get_login_info()
        fcr = ForwardConstructor(info.user_id, info.nickname)
        for message_id in messages:
            fcr.attach_message_id(message_id)
        return await self.post_group_forward_msg(group_id, fcr.to_forward())

    async def send_private_forward_msg(
        self,
        user_id: Union[str, int],
        messages: List[dict],
        news: List[str],
        prompt: str,
        summary: str,
        source: str,
    ) -> str:
        """
        发送私聊合并转发消息

        Args:
            user_id: 用户 QQ 号
            messages: 消息内容列表
            news: 预览文本列表
            prompt: 提示文本
            summary: 摘要文本
            source: 来源文本

        Returns:
            str: 消息 ID
        """
        result = await self._request_raw(
            "/send_private_forward_msg",
            {
                "user_id": user_id,
                "messages": messages,
                "news": news,
                "prompt": prompt,
                "summary": summary,
                "source": source,
            },
        )
        status = MessageAPIReturnStatus(result)
        return status.message_id

    async def send_private_forward_msg_by_id(
        self,
        user_id: Union[str, int],
        messages: List[Union[str, int]],
    ) -> str:
        """
        通过消息 ID 发送私聊合并转发

        Args:
            user_id: 用户 QQ 号
            messages: 消息 ID 列表

        Returns:
            str: 消息 ID
        """
        from ncatbot.core.helper import ForwardConstructor

        info = await self.get_login_info()
        fcr = ForwardConstructor(info.user_id, info.nickname)
        for message_id in messages:
            fcr.attach_message_id(message_id)
        return await self.post_private_forward_msg(user_id, fcr.to_forward())

    # -------------------------------------------------------------------------
    # 占位方法（由其他 API 实现）
    # -------------------------------------------------------------------------

    async def get_login_info(self):
        """获取登录信息（应由 AccountAPI 实现）"""
        raise NotImplementedError("This method should be implemented by AccountAPI")
