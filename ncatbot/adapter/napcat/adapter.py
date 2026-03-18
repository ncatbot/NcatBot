"""
NapCat 适配器主类

纯编排类，组合 setup / connection / api / parser 子组件。
"""

from typing import Any, Dict, Optional

from ..base import BaseAdapter
from ncatbot.api import IAPIClient
from ncatbot.utils import get_log
from ncatbot.utils.config.models import NapCatConfig

from .api.bot_api import NapCatBotAPI
from .connection.protocol import OB11Protocol
from .connection.websocket import NapCatWebSocket
from .parser import NapCatEventParser
from .setup.launcher import NapCatLauncher

LOG = get_log("NapCatAdapter")


class NapCatAdapter(BaseAdapter):
    name = "napcat"
    description = "NapCat (OneBot v11) 适配器"
    supported_protocols = ["onebot_v11"]
    platform = "qq"

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        *,
        bot_uin: str = "",
        websocket_timeout: int = 15,
    ):
        super().__init__(
            config=config,
            bot_uin=bot_uin,
            websocket_timeout=websocket_timeout,
        )
        self._config = NapCatConfig.model_validate(self._raw_config)
        self._launcher = NapCatLauncher(
            napcat_config=self._config,
            bot_uin=self._bot_uin,
            websocket_timeout=self._websocket_timeout,
        )
        self._ws: Optional[NapCatWebSocket] = None
        self._protocol: Optional[OB11Protocol] = None
        self._api: Optional[NapCatBotAPI] = None
        self._parser = NapCatEventParser()

    @property
    def napcat_config(self) -> NapCatConfig:
        """适配器的 NapCat 配置（供外部诊断工具访问）。"""
        return self._config

    async def setup(self) -> None:
        await self._launcher.launch()

    async def connect(self) -> None:
        uri = self._config.get_uri_with_token()
        self._ws = NapCatWebSocket(uri)
        await self._ws.connect()
        self._protocol = OB11Protocol(self._ws)
        self._api = NapCatBotAPI(self._protocol)
        self._protocol.set_event_handler(self._on_event)

    async def disconnect(self) -> None:
        if self._protocol:
            self._protocol.cancel_all()
        if self._ws:
            await self._ws.disconnect()
        self._api = self._protocol = self._ws = None

    async def listen(self) -> None:
        await self._ws.listen(self._protocol.on_message)

    def get_api(self) -> IAPIClient:
        return self._api

    @property
    def connected(self) -> bool:
        return self._ws is not None and self._ws.connected

    async def _on_event(self, raw_data: dict) -> None:
        """收到事件推送，解析为数据模型后回调给分发器"""
        data_model = self._parser.parse(raw_data)
        if data_model is None:
            return
        s = data_model.model_dump_json()
        if len(s) > 2000:
            s = s[:2000] + "..."
        LOG.info(f"收到事件 {data_model.post_type.value}: {s}")
        if self._event_callback:
            await self._event_callback(data_model)
