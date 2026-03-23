"""
平台适配器抽象基类
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Callable, Awaitable, List, TYPE_CHECKING

from ncatbot.utils import get_log

_LOG = get_log("BaseAdapter")

if TYPE_CHECKING:
    from ncatbot.api import IAPIClient
    from ncatbot.types import BaseEventData


class BaseAdapter(ABC):
    """平台适配器抽象基类

    回调签名为 Callable[[BaseEventData], Awaitable[None]]，
    即 adapter 只产出纯数据模型，不创建实体。

    Parameters
    ----------
    config:
        适配器专属配置字典，由子类自行验证。
    bot_uin:
        全局 bot_uin，由 BotClient 从顶层配置注入。
    websocket_timeout:
        全局 WebSocket 超时设置。

    pip_dependencies:
        Python 包依赖声明，格式 ``{"包名": "版本约束"}``。
        框架在 ``setup()`` 之前自动调用 ``ensure_deps()`` 检查并安装。
    """

    name: str
    description: str
    supported_protocols: List[str]
    platform: str  # 平台标识，如 "qq"、"telegram" 等
    pip_dependencies: Dict[str, str] = {}  # pip 依赖声明，如 {"pkg": ">=1.0"}

    _event_callback: Optional[Callable[["BaseEventData"], Awaitable[None]]] = None

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        *,
        bot_uin: str = "",
        websocket_timeout: int = 15,
    ) -> None:
        self._raw_config = config or {}
        self._bot_uin = bot_uin
        self._websocket_timeout = websocket_timeout

    # ---- 依赖管理 ----

    async def ensure_deps(self) -> bool:
        """检查并安装 ``pip_dependencies`` 中声明的依赖，返回是否就绪。

        无依赖或依赖已满足时直接返回 ``True``；
        缺少依赖时交互式询问用户确认安装。
        """
        deps = getattr(self, "pip_dependencies", None)
        if not deps:
            return True

        from ncatbot.plugin.loader.pip_helper import (
            check_requirements,
            install_packages,
        )

        _, missing = check_requirements(deps)
        if not missing:
            return True

        from ncatbot.utils import async_confirm
        from ncatbot.utils import get_config_manager

        listing = ", ".join(missing)
        _LOG.info("适配器 %s 需要安装 pip 依赖: %s", self.name, listing)
        mgr = get_config_manager()
        if mgr.effective_skip_pip_install_confirm():
            approved = True
        else:
            approved = await async_confirm(
                f"适配器 {self.name} 需要安装以下 pip 依赖:\n  {listing}\n确认安装?",
                default=True,
            )
        if not approved:
            return False

        success = install_packages(missing)
        if not success:
            _LOG.error("适配器 %s 的 pip 依赖安装失败", self.name)
            return False

        _, still_missing = check_requirements(deps)
        if still_missing:
            _LOG.error("适配器 %s 安装后仍缺少依赖: %s", self.name, still_missing)
            return False

        _LOG.info("适配器 %s 的 pip 依赖安装完成", self.name)
        return True

    # ---- 生命周期 ----

    @abstractmethod
    async def setup(self) -> None:
        """准备平台环境（安装/配置/启动）"""

    @abstractmethod
    async def connect(self) -> None:
        """建立连接并初始化 API"""

    @abstractmethod
    async def disconnect(self) -> None:
        """断开连接，释放资源"""

    @abstractmethod
    async def listen(self) -> None:
        """阻塞监听消息，内部完成事件解析后回调数据模型"""

    # ---- API ----

    @abstractmethod
    def get_api(self) -> "IAPIClient":
        """返回 IAPIClient 实现"""

    # ---- 回调 ----

    def set_event_callback(
        self,
        callback: Callable[["BaseEventData"], Awaitable[None]],
    ) -> None:
        """设置事件数据回调，由异步分发器在启动时调用"""
        self._event_callback = callback

    # ---- 状态 ----

    @property
    @abstractmethod
    def connected(self) -> bool: ...
