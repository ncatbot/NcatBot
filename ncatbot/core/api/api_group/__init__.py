"""
群管理相关 API

通过 Mixin 组合提供完整的群管理功能，包括：
- 成员管理（踢人、禁言、设置管理员等）
- 文件管理（上传、下载、移动、删除）
- 信息查询（群信息、成员信息、荣誉信息）
- 管理员功能（群设置、公告、相册）
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..utils import generate_sync_methods

# Mixin 类
from .member import GroupMemberMixin
from .file import GroupFileMixin
from .info import GroupInfoMixin
from .admin import GroupAdminMixin

# 数据模型
from .models import (
    EssenceMessage as EssenceMessage,
    GroupChatActivity as GroupChatActivity,
    GroupInfo as GroupInfo,
    GroupMemberInfo as GroupMemberInfo,
    GroupMemberList as GroupMemberList,
    UserInfo as UserInfo,
)

if TYPE_CHECKING:
    from ..client import IAPIClient


# =============================================================================
# GroupAPI 组合类
# =============================================================================


@generate_sync_methods
class GroupAPI(
    GroupMemberMixin,
    GroupFileMixin,
    GroupInfoMixin,
    GroupAdminMixin,
):
    """
    群管理 API

    通过多重继承组合各个功能模块，提供完整的群管理功能。
    使用依赖注入模式，通过构造函数接收 IAPIClient 实例。

    功能模块:
        - GroupMemberMixin: 成员管理（踢人、禁言、设置管理员等）
        - GroupFileMixin: 文件管理（上传、下载、移动、删除）
        - GroupInfoMixin: 信息查询（群信息、成员信息、荣誉信息）
        - GroupAdminMixin: 管理员功能（群设置、公告、相册）

    Usage:
        ```python
        from ncatbot.core.api import GroupAPI, CallbackAPIClient

        client = CallbackAPIClient(callback_func)
        group_api = GroupAPI(client)

        # 异步调用
        info = await group_api.get_group_info(123456)

        # 同步调用（自动生成）
        info = group_api.get_group_info_sync(123456)
        ```
    """

    def __init__(self, client: "IAPIClient", service_manager=None):
        """
        初始化群管理 API

        Args:
            client: API 客户端实例，实现 IAPIClient 协议
            service_manager: 服务管理器实例（可选）
        """
        super().__init__(client, service_manager)
