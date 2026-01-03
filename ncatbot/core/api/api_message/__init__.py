"""
消息相关 API

通过 Mixin 组合提供完整的消息功能，包括：
- 群消息发送（文本、图片、语音、文件等）
- 群音乐消息（音乐分享、戳一戳）
- 私聊消息发送（文本、图片、语音、文件等）
- 私聊音乐消息（音乐分享、戳一戳）
- 通用消息操作（删除、贴表情等）
- 合并转发消息
- 消息获取（历史记录、详情、媒体文件）
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List

from ..utils import generate_sync_methods

# Mixin 类
from .group_send import GroupMessageMixin
from .group_music import GroupMusicMixin
from .private_send import PrivateMessageMixin
from .private_music import PrivateMusicMixin
from .common import CommonMessageMixin
from .forward import ForwardMessageMixin
from .retrieve import MessageRetrieveMixin

# 工具函数
from .validation import validate_msg as validate_msg

if TYPE_CHECKING:
    from ..client import IAPIClient


# =============================================================================
# MessageAPI 组合类
# =============================================================================


@generate_sync_methods
class MessageAPI(
    GroupMessageMixin,
    GroupMusicMixin,
    PrivateMessageMixin,
    PrivateMusicMixin,
    CommonMessageMixin,
    ForwardMessageMixin,
    MessageRetrieveMixin,
):
    """
    消息 API

    通过多重继承组合各个功能模块，提供完整的消息功能。
    使用依赖注入模式，通过构造函数接收 IAPIClient 实例。

    功能模块:
        - GroupMessageMixin: 群消息发送
        - GroupMusicMixin: 群音乐和特殊消息
        - PrivateMessageMixin: 私聊消息发送
        - PrivateMusicMixin: 私聊音乐和特殊消息
        - CommonMessageMixin: 通用消息操作
        - ForwardMessageMixin: 合并转发消息
        - MessageRetrieveMixin: 消息获取

    Usage:
        ```python
        from ncatbot.core.api import MessageAPI, CallbackAPIClient

        client = CallbackAPIClient(callback_func)
        message_api = MessageAPI(client)

        # 异步调用
        msg_id = await message_api.send_group_text(123456, "Hello!")

        # 同步调用（自动生成）
        msg_id = message_api.send_group_text_sync(123456, "Hello!")
        ```
    """

    def __init__(self, client: "IAPIClient", service_manager=None):
        """
        初始化消息 API

        Args:
            client: API 客户端实例，实现 IAPIClient 协议
            service_manager: 服务管理器实例（可选）
        """
        super().__init__(client, service_manager)

    # -------------------------------------------------------------------------
    # 占位方法（由其他 API 实现）
    # -------------------------------------------------------------------------

    async def get_login_info(self):
        """获取登录信息（应由 AccountAPI 实现）"""
        raise NotImplementedError("This method should be implemented by AccountAPI")

    async def get_group_list(self) -> List[str]:
        """获取群列表（应由 GroupAPI 实现）"""
        raise NotImplementedError("This method should be implemented by GroupAPI")
