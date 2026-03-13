"""
平台适配器抽象基类

定义所有平台适配器必须实现的接口。
"""

from abc import ABC, abstractmethod
from typing import Optional, Callable, Awaitable, List, TYPE_CHECKING

if TYPE_CHECKING:
    from ncatbot.core.api.interface import IBotAPI
    from ncatbot.core.event.events import BaseEvent


class BaseAdapter(ABC):
    """平台适配器抽象基类

    每个平台适配器必须继承此类并实现所有抽象方法。
    一个 Adapter 实例封装与一个平台的完整交互。

    职责：
    1. 平台环境的准备和部署
    2. 与平台的连接建立和维护
    3. 原始协议数据到标准 Event 的转换
    4. IBotAPI 的具体实现
    5. 平台特定能力（如文件预上传）
    """

    # ---- 元数据（子类必须定义） ----

    name: str
    description: str
    supported_protocols: List[str]

    # ---- 内部状态 ----

    _event_callback: Optional[Callable[["BaseEvent"], Awaitable[None]]] = None

    # ==================================================================
    # 生命周期方法
    # ==================================================================

    @abstractmethod
    async def setup(self) -> None:
        """准备平台环境

        职责：
        - 检查平台依赖是否满足
        - 安装/部署平台服务（如 NapCat）
        - 生成/加载平台配置

        此方法在 connect() 之前调用。
        如果平台已就绪，此方法应快速返回。

        Raises:
            AdapterSetupError: 环境准备失败
        """

    @abstractmethod
    async def connect(self) -> None:
        """建立与平台的连接

        职责：
        - 建立通信通道（WebSocket/HTTP/...）
        - 完成认证/握手
        - 确认连接可用

        此方法在 setup() 之后、listen() 之前调用。

        Raises:
            AdapterConnectionError: 连接建立失败
        """

    @abstractmethod
    async def disconnect(self) -> None:
        """断开与平台的连接

        职责：
        - 清理所有挂起的请求
        - 关闭通信通道
        - 释放连接相关资源

        此方法在 shutdown 阶段调用，必须幂等。
        """

    @abstractmethod
    async def listen(self) -> None:
        """开始监听平台消息

        此方法阻塞运行，持续接收消息直到连接断开或被取消。
        收到消息后：
        1. 调用 convert_event() 转换为标准 Event
        2. 调用 _event_callback() 传递给 Core 层

        Raises:
            asyncio.CancelledError: 正常取消
            AdapterConnectionError: 连接中断
        """

    # ==================================================================
    # 事件转换
    # ==================================================================

    @abstractmethod
    def convert_event(self, raw_data: dict) -> Optional["BaseEvent"]:
        """将平台原始数据转换为标准 Event 对象

        契约：
        1. 必须返回 BaseEvent 子类实例，或 None（无法解析时）
        2. 必须在返回前调用 event.bind_api(self.get_api()) 绑定 API
        3. 不得返回平台特定的 Event 子类（必须是标准模型中定义的类）
        4. 转换失败时返回 None 并记录日志，不得抛出异常

        Args:
            raw_data: 平台原始数据（通常是 JSON dict）

        Returns:
            标准 Event 对象，或 None
        """

    # ==================================================================
    # API 实现
    # ==================================================================

    @abstractmethod
    def get_api(self) -> "IBotAPI":
        """返回此适配器的 IBotAPI 实现

        返回的 API 实例：
        - 必须实现 IBotAPI 中定义的所有方法
        - 生命周期与 Adapter 绑定（Adapter 断开后 API 不可用）
        - 应是单例（同一 Adapter 多次调用返回同一实例）

        Returns:
            IBotAPI 实现实例
        """

    # ==================================================================
    # 回调设置
    # ==================================================================

    def set_event_callback(
        self, callback: Callable[["BaseEvent"], Awaitable[None]]
    ) -> None:
        """设置事件回调

        由 BotClient 在启动阶段调用，将转换后的标准 Event
        传递给 Core 层的 EventDispatcher。

        Args:
            callback: 接收标准 Event 的异步回调函数
        """
        self._event_callback = callback

    # ==================================================================
    # 状态查询
    # ==================================================================

    @property
    @abstractmethod
    def connected(self) -> bool:
        """是否已连接到平台"""

    # ==================================================================
    # 可选能力（子类按需实现）
    # ==================================================================

    async def preupload_file(self, file_path: str, file_type: str = "file") -> str:
        """预上传文件（可选能力）

        平台支持文件预上传时实现此方法。
        不支持时返回原始路径。

        Args:
            file_path: 本地文件路径、URL 或 base64
            file_type: 文件类型（image/video/record/file）

        Returns:
            处理后的文件引用（URL 或平台特定标识）
        """
        return file_path

    async def preupload_message(self, message: list) -> list:
        """预上传消息中的文件（可选能力）

        遍历消息段，对其中的文件类型进行预上传处理。
        不支持时原样返回。

        Args:
            message: 消息段列表

        Returns:
            处理后的消息段列表
        """
        return message
