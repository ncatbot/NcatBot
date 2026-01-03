"""
测试套件

提供端到端测试的高级封装。
使用 pytest-asyncio 管理事件循环，不创建额外的事件循环。
"""
# pyright: reportAttributeAccessIssue=false
# pyright: reportReturnType=false
# pyright: reportOptionalMemberAccess=false

from typing import List, Optional, TYPE_CHECKING
from contextlib import asynccontextmanager

from ncatbot.utils import get_log
from .mixins import PluginMixin, InjectorMixin, AssertionMixin

if TYPE_CHECKING:
    from ncatbot.core import BotClient, BotAPI
    from .mock_server import NapCatMockServer

LOG = get_log("E2ETestSuite")


class E2ETestSuite(PluginMixin, InjectorMixin, AssertionMixin):
    """
    端到端测试套件
    
    提供完整的测试环境，包括：
    - Mock 模式的 BotClient（连接到 MockServer）
    - 插件注册和卸载
    - 事件注入（通过 MockServer）
    - API 调用断言
    
    使用示例（pytest-asyncio fixture）：
    ```python
    @pytest_asyncio.fixture
    async def test_suite():
        suite = E2ETestSuite()
        await suite.setup()
        yield suite
        await suite.teardown()
    
    @pytest.mark.asyncio
    async def test_example(test_suite):
        await test_suite.register_plugin("my_plugin")
        await test_suite.inject_group_message("/hello")
        test_suite.assert_api_called("send_group_msg")
    ```
    """
    
    _port_counter = 16700
    
    def __init__(
        self,
        bt_uin: str = "123456789",
        mock_server: Optional["NapCatMockServer"] = None,
        port: Optional[int] = None,
    ):
        """
        初始化测试套件
        
        Args:
            bt_uin: 模拟的机器人 QQ 号
            mock_server: MockServer 实例（可选，未提供时自动创建）
            port: MockServer 端口（仅在自动创建时使用）
        """
        self._bt_uin = bt_uin
        self._mock_server = mock_server
        self._port = port
        self._client: Optional["BotClient"] = None
        self._registered_plugins: List[str] = []
        self._owns_mock_server = False
    
    # ==================== 生命周期 ====================
    
    async def setup(self) -> "BotClient":
        """异步设置测试环境"""
        from ncatbot.core import BotClient
        from ncatbot.utils import ncatbot_config
        from .mock_server import NapCatMockServer, get_standard_data
        
        # 自动创建 MockServer
        if not self._mock_server:
            port = self._port
            if port is None:
                E2ETestSuite._port_counter += 1
                port = E2ETestSuite._port_counter
            
            self._mock_server = NapCatMockServer(
                port=port,
                initial_data=get_standard_data()
            )
            await self._mock_server.start()
            self._owns_mock_server = True
        
        # 配置 WebSocket URI 指向 MockServer
        ncatbot_config.napcat.ws_uri = self._mock_server.uri
        
        # 创建并启动 BotClient（与 run_backend 使用相同的初始化逻辑）
        BotClient.reset_singleton()
        self._client = BotClient()
        await self._client.run_backend_async(
            bt_uin=self._bt_uin,
            mock=True,
            skip_plugin_load=True,
        )
        
        # 设置反向引用，供 TestHelper 使用
        self._client._test_suite = self

        LOG.info("测试套件已启动")
        return self._client

    async def teardown(self) -> None:
        """异步清理测试环境"""
        if self._client:
            # 使用 shutdown() 安全关闭，让 finally 块负责清理
            # 避免与 _core_execution 的 _cleanup() 重复调用 close_all()
            await self._client.shutdown()
            self._client = None
            self._registered_plugins.clear()
        
        if self._owns_mock_server and self._mock_server:
            await self._mock_server.stop()
            self._mock_server = None
            self._owns_mock_server = False

        LOG.info("测试套件已清理")
    
    async def __aenter__(self) -> "E2ETestSuite":
        await self.setup()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.teardown()
    
    # ==================== 属性访问 ====================
    
    @property
    def client(self) -> "BotClient":
        """获取 BotClient 实例"""
        if not self._client:
            raise RuntimeError("测试套件未启动，请先调用 setup()")
        return self._client
    
    @property
    def event_bus(self):
        """获取 EventBus"""
        return self.client.event_bus
    
    @property
    def services(self):
        """获取 ServiceManager"""
        return self.client.services
    
    @property
    def api(self) -> "BotAPI":
        """获取 BotAPI"""
        return self.client.api
    
    @property
    def mock_server(self) -> Optional["NapCatMockServer"]:
        """获取 MockServer 实例"""
        return self._mock_server


@asynccontextmanager
async def create_test_suite_with_mock_server(
    initial_data: Optional[dict] = None,
    port: int = 16700,
    **suite_kwargs
):
    """
    创建带有 MockServer 的测试套件
    
    自动启动 MockServer 并配置测试套件。
    
    Args:
        initial_data: 初始数据，默认使用 get_standard_data()
        port: MockServer 端口，默认 16700
        **suite_kwargs: 传递给 E2ETestSuite 的其他参数
    """
    from .mock_server import NapCatMockServer, get_standard_data
    
    data = initial_data or get_standard_data()
    
    async with NapCatMockServer(port=port, initial_data=data) as server:
        suite = E2ETestSuite(mock_server=server, **suite_kwargs)
        await suite.setup()
        try:
            yield suite
        finally:
            await suite.teardown()
