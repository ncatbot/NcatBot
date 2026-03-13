"""
NapCat 适配器

BaseAdapter 的 NapCat/OneBot v11 实现。
组合 connection、protocol、environment、event_converter、api_impl 等组件。
"""

from typing import Optional, List

from ncatbot.adapter.base import BaseAdapter
from ncatbot.core.api.interface import IBotAPI
from ncatbot.core.event.events import BaseEvent
from ncatbot.utils import get_log, ncatbot_config

from .api_impl import NapCatBotAPI
from .connection import NapCatConnection
from .environment import NapCatEnvironment
from .event_converter import NapCatEventConverter
from .protocol import NapCatProtocol

LOG = get_log("NapCatAdapter")


class NapCatAdapter(BaseAdapter):
    """NapCat 平台适配器

    实现 BaseAdapter 的全部抽象方法，封装 NapCat (OneBot v11) 平台交互。

    组件关系：
      NapCatAdapter
        ├── NapCatEnvironment   (环境准备/启动 NapCat)
        ├── NapCatConnection    (WebSocket 连接管理)
        ├── NapCatProtocol      (请求-响应匹配)
        ├── NapCatBotAPI        (IBotAPI 实现)
        └── NapCatEventConverter(事件转换)
    """

    name = "napcat"
    description = "NapCat (OneBot v11) 适配器"
    supported_protocols: List[str] = ["onebot_v11"]

    def __init__(self):
        self._environment = NapCatEnvironment()
        self._connection: Optional[NapCatConnection] = None
        self._protocol: Optional[NapCatProtocol] = None
        self._api: Optional[NapCatBotAPI] = None
        self._event_converter: Optional[NapCatEventConverter] = None

    # ==================================================================
    # BaseAdapter 生命周期
    # ==================================================================

    async def setup(self) -> None:
        """准备 NapCat 环境（安装/配置/启动 NapCat 服务）"""
        self._environment.launch()
        LOG.info("NapCat 环境准备完成")

    async def connect(self) -> None:
        """建立 WebSocket 连接并初始化协议层"""
        uri = ncatbot_config.get_uri_with_token()

        # 创建连接
        self._connection = NapCatConnection(uri=uri)
        await self._connection.connect()

        # 创建协议层
        self._protocol = NapCatProtocol(self._connection)
        self._protocol.bind_loop()

        # 创建 API 实现
        self._api = NapCatBotAPI(self._protocol)

        # 创建事件转换器
        self._event_converter = NapCatEventConverter(self._api)

        # 设置协议层的事件回调：接收到非 API 响应的消息时转换为事件并上报
        self._protocol.set_event_callback(self._dispatch_raw_event)

        LOG.info("NapCat 连接建立成功")

    async def disconnect(self) -> None:
        """断开连接并清理资源"""
        if self._protocol:
            self._protocol.cancel_all()

        if self._connection:
            await self._connection.disconnect()

        self._event_converter = None
        self._api = None
        self._protocol = None
        self._connection = None

        LOG.info("NapCat 连接已关闭")

    async def listen(self) -> None:
        """开始监听 WebSocket 消息"""
        if not self._connection:
            raise ConnectionError("适配器未连接，请先调用 connect()")
        await self._connection.listen()

    # ==================================================================
    # 事件转换
    # ==================================================================

    def convert_event(self, raw_data: dict) -> Optional[BaseEvent]:
        """将原始数据转换为标准事件"""
        if not self._event_converter:
            return None
        return self._event_converter.convert(raw_data)

    # ==================================================================
    # API 实现
    # ==================================================================

    def get_api(self) -> IBotAPI:
        """返回 NapCat 的 IBotAPI 实现"""
        if not self._api:
            raise RuntimeError("适配器未连接，API 不可用")
        return self._api

    # ==================================================================
    # 状态查询
    # ==================================================================

    @property
    def connected(self) -> bool:
        return self._connection is not None and self._connection.connected

    # ==================================================================
    # 内部方法
    # ==================================================================

    async def _dispatch_raw_event(self, raw_data: dict) -> None:
        """接收原始数据，转换为事件后通过回调上报"""
        event = self.convert_event(raw_data)
        if event is None:
            return

        if self._event_callback:
            await self._event_callback(event)
