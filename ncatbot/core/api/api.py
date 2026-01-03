"""
统一的 Bot API 类

使用依赖注入和组合模式整合所有 API 功能。
"""

from __future__ import annotations

from typing import Any, Callable, Coroutine, Dict, Optional, TYPE_CHECKING

from .client import IAPIClient, CallbackAPIClient
from .api_account import AccountAPI
from .api_group import GroupAPI
from .api_message import MessageAPI
from .api_private import PrivateAPI
from .api_support import SupportAPI

if TYPE_CHECKING:
    from ncatbot.core.service import ServiceManager


class BotAPI(AccountAPI, GroupAPI, MessageAPI, PrivateAPI, SupportAPI):
    """
    统一的 Bot API 类

    通过依赖注入整合所有 API 功能，提供完整的 Bot 操作接口。

    架构说明：
    - 使用多重继承组合各个 API 模块的功能
    - 所有 API 模块共享同一个 IAPIClient 实例
    - 支持依赖注入，方便测试和扩展

    使用方式：
    ```python
    # 使用回调函数创建（传统方式，向后兼容）
    api = BotAPI(adapter.send)

    # 使用 IAPIClient 创建（推荐方式）
    client = CallbackAPIClient(adapter.send)
    api = BotAPI.from_client(client)

    # 异步调用
    info = await api.get_login_info()

    # 同步调用（已废弃，不推荐）
    info = api.get_login_info_sync()
    ```

    Attributes:
        _client: API 客户端实例
    """

    def __init__(
        self,
        async_callback: Callable[
            [str, Optional[Dict[str, Any]]], Coroutine[Any, Any, Dict]
        ],
        service_manager: Optional["ServiceManager"] = None,
    ):
        """
        使用回调函数初始化（向后兼容）

        Args:
            async_callback: 异步回调函数，接受 (endpoint, params) 返回响应字典
            service_manager: 服务管理器实例（可选）

        Note:
            推荐使用 `BotAPI.from_client()` 工厂方法创建实例
        """
        # 将回调函数包装为 IAPIClient
        client = CallbackAPIClient(async_callback)

        # 初始化所有父类（使用 MRO 确保正确初始化）
        super().__init__(client, service_manager)

    @classmethod
    def from_client(
        cls,
        client: IAPIClient,
        service_manager: Optional["ServiceManager"] = None,
    ) -> "BotAPI":
        """
        使用 IAPIClient 创建实例（推荐方式）

        Args:
            client: API 客户端实例
            service_manager: 服务管理器实例（可选）

        Returns:
            BotAPI: Bot API 实例

        Example:
            ```python
            from ncatbot.core.api import BotAPI, CallbackAPIClient, MockAPIClient
            from ncatbot.core.service import ServiceManager

            # 生产环境
            client = CallbackAPIClient(adapter.send)
            service_manager = ServiceManager()
            api = BotAPI.from_client(client, service_manager)

            # 测试环境
            mock_client = MockAPIClient()
            api = BotAPI.from_client(mock_client)
            ```
        """
        # 创建一个空的实例，绕过 __init__
        instance = object.__new__(cls)
        instance._client = client
        instance._service_manager = service_manager
        return instance

    # -------------------------------------------------------------------------
    # 属性访问器
    # -------------------------------------------------------------------------

    @property
    def client(self) -> IAPIClient:
        """获取 API 客户端实例"""
        return self._client

    # -------------------------------------------------------------------------
    # 便捷方法
    # -------------------------------------------------------------------------

    async def is_connected(self) -> bool:
        """
        检查 API 连接状态

        Returns:
            bool: 是否已连接

        Note:
            通过尝试获取登录信息来判断连接状态
        """
        try:
            await self.get_login_info()
            return True
        except Exception:
            return False
