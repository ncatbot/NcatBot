"""
测试套件

提供端到端测试的高级封装，简化测试编写。
"""

from typing import List, Optional, Type, TYPE_CHECKING
from contextlib import asynccontextmanager

from ncatbot.utils import get_log, run_coroutine

if TYPE_CHECKING:
    from ncatbot.core import BotClient
    from ncatbot.plugin_system import BasePlugin

LOG = get_log("E2ETestSuite")


class E2ETestSuite:
    """
    端到端测试套件
    
    提供完整的测试环境，包括：
    - Mock 模式的 BotClient
    - 插件注册和卸载
    - 事件注入
    - API 调用断言
    
    使用示例（作为上下文管理器）：
    ```python
    async with TestSuite() as suite:
        await suite.register_plugin(MyPlugin)
        await suite.inject_group_message("/hello")
        suite.assert_api_called("send_group_msg")
    ```
    
    使用示例（手动管理）：
    ```python
    suite = TestSuite()
    suite.setup()
    try:
        suite.register_plugin_sync(MyPlugin)
        suite.inject_group_message_sync("/hello")
        suite.assert_api_called("send_group_msg")
    finally:
        suite.teardown()
    ```
    """
    
    def __init__(self, bt_uin: str = "123456789", skip_builtin_plugins: bool = False):
        """
        初始化测试套件
        
        Args:
            bt_uin: 模拟的机器人 QQ 号
            skip_builtin_plugins: 是否跳过内置插件加载（默认为 False，会加载 UnifiedRegistryPlugin 等）
        """
        self._bt_uin = bt_uin
        self._skip_builtin_plugins = skip_builtin_plugins
        self._client: Optional["BotClient"] = None
        self._registered_plugins: List[str] = []
    
    # ==================== 生命周期 ====================
    
    def setup(self) -> "BotClient":
        """
        设置测试环境
        
        Returns:
            配置好的 BotClient 实例
        """
        from ncatbot.core import BotClient
        
        # 重置单例以允许创建新实例
        BotClient.reset_singleton()
        
        self._client = BotClient()
        # 始终跳过插件目录加载，但可选择是否加载内置插件
        self._client.start(
            mock=True,
            bt_uin=self._bt_uin,
            skip_plugin_load=True,  # 始终跳过自动加载
        )
        
        # 手动加载内置插件（如果需要）
        if not self._skip_builtin_plugins:
            run_coroutine(self._client.plugin_loader.load_builtin_plugins)
        
        LOG.info("测试套件已启动")
        return self._client
    
    def teardown(self) -> None:
        """清理测试环境"""
        if self._client:
            # 卸载测试中注册的插件
            for plugin_name in self._registered_plugins:
                try:
                    run_coroutine(self._client.plugin_loader.unload_plugin, plugin_name)
                except Exception as e:
                    LOG.warning(f"卸载插件 {plugin_name} 失败: {e}")
            
            self._client.bot_exit()
            self._client = None
            self._registered_plugins.clear()
        
        LOG.info("测试套件已清理")
    
    async def __aenter__(self) -> "E2ETestSuite":
        """异步上下文管理器入口"""
        self.setup()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """异步上下文管理器出口"""
        self.teardown()
    
    def __enter__(self) -> "E2ETestSuite":
        """同步上下文管理器入口"""
        self.setup()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """同步上下文管理器出口"""
        self.teardown()
    
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
    def api(self):
        """获取 BotAPI"""
        return self.client.api
    
    @property
    def mock_router(self):
        """获取 MockMessageRouter"""
        return self.services.message_router
    
    # ==================== 插件管理 ====================
    
    async def register_plugin(self, plugin_class: Type["BasePlugin"]) -> "BasePlugin":
        """
        注册插件
        
        Args:
            plugin_class: 插件类
            
        Returns:
            插件实例
        """
        plugin = await self.client.plugin_loader.load_plugin_by_class(
            plugin_class, plugin_class.name
        )
        self._registered_plugins.append(plugin_class.name)
        LOG.info(f"已注册测试插件: {plugin_class.name}")
        return plugin
    
    def register_plugin_sync(self, plugin_class: Type["BasePlugin"]) -> "BasePlugin":
        """同步版本的 register_plugin"""
        return run_coroutine(self.register_plugin, plugin_class)
    
    async def unregister_plugin(self, plugin_name: str) -> None:
        """卸载插件"""
        await self.client.plugin_loader.unload_plugin(plugin_name)
        if plugin_name in self._registered_plugins:
            self._registered_plugins.remove(plugin_name)
        LOG.info(f"已卸载测试插件: {plugin_name}")
    
    def unregister_plugin_sync(self, plugin_name: str) -> None:
        """同步版本的 unregister_plugin"""
        run_coroutine(self.unregister_plugin, plugin_name)
    
    # ==================== 事件注入 ====================
    
    async def inject_event(self, event) -> None:
        """
        注入解析后的事件
        
        Args:
            event: 事件对象
        """
        await self.client.inject_event(event)
    
    def inject_event_sync(self, event) -> None:
        """同步版本的 inject_event"""
        run_coroutine(self.inject_event, event)
    
    async def inject_raw_event(self, data: dict) -> None:
        """
        注入原始事件数据
        
        Args:
            data: OneBot 格式的原始事件数据
        """
        await self.client.inject_raw_event(data)
    
    def inject_raw_event_sync(self, data: dict) -> None:
        """同步版本的 inject_raw_event"""
        run_coroutine(self.inject_raw_event, data)
    
    async def inject_group_message(
        self,
        message: str,
        group_id: str = "123456789",
        user_id: str = "987654321",
        **kwargs
    ) -> None:
        """
        注入群消息事件
        
        Args:
            message: 消息内容
            group_id: 群号
            user_id: 发送者 QQ
        """
        from .event_factory import EventFactory
        event = EventFactory.create_group_message(
            message=message,
            group_id=group_id,
            user_id=user_id,
            **kwargs
        )
        await self.inject_event(event)
    
    def inject_group_message_sync(
        self,
        message: str,
        group_id: str = "123456789",
        user_id: str = "987654321",
        **kwargs
    ) -> None:
        """同步版本的 inject_group_message"""
        run_coroutine(self.inject_group_message, message, group_id, user_id, **kwargs)
    
    async def inject_private_message(
        self,
        message: str,
        user_id: str = "987654321",
        **kwargs
    ) -> None:
        """
        注入私聊消息事件
        
        Args:
            message: 消息内容
            user_id: 发送者 QQ
        """
        from .event_factory import EventFactory
        event = EventFactory.create_private_message(
            message=message,
            user_id=user_id,
            **kwargs
        )
        await self.inject_event(event)
    
    def inject_private_message_sync(
        self,
        message: str,
        user_id: str = "987654321",
        **kwargs
    ) -> None:
        """同步版本的 inject_private_message"""
        run_coroutine(self.inject_private_message, message, user_id, **kwargs)
    
    # ==================== 断言方法 ====================
    
    def assert_api_called(self, action: str) -> None:
        """断言 API 被调用过"""
        self.mock_router.assert_called(action)
    
    def assert_api_not_called(self, action: str) -> None:
        """断言 API 未被调用"""
        self.mock_router.assert_not_called(action)
    
    def assert_api_called_with(self, action: str, **expected_params) -> None:
        """断言 API 使用特定参数被调用"""
        self.mock_router.assert_called_with(action, **expected_params)
    
    def assert_reply_sent(self, contains: Optional[str] = None) -> None:
        """
        断言发送了回复消息
        
        Args:
            contains: 回复中应包含的文本（可选）
        """
        group_calls = self.mock_router.get_calls_for_action("send_group_msg")
        private_calls = self.mock_router.get_calls_for_action("send_private_msg")
        all_calls = group_calls + private_calls
        
        assert all_calls, "没有发送任何回复消息"
        
        if contains:
            for params in all_calls:
                if params and "message" in params:
                    message = params["message"]
                    # 检查消息内容
                    message_str = str(message)
                    if contains in message_str:
                        return
            raise AssertionError(f"回复中未包含预期文本: {contains}")
    
    def assert_no_reply(self) -> None:
        """断言没有发送回复"""
        group_calls = self.mock_router.get_calls_for_action("send_group_msg")
        private_calls = self.mock_router.get_calls_for_action("send_private_msg")
        all_calls = group_calls + private_calls
        
        assert not all_calls, f"意外发送了 {len(all_calls)} 条回复"
    
    def get_api_calls(self, action: Optional[str] = None) -> list:
        """
        获取 API 调用记录
        
        Args:
            action: 指定 API，为 None 则返回所有调用
        """
        if action:
            return self.mock_router.get_calls_for_action(action)
        return self.mock_router.get_call_history()
    
    def clear_call_history(self) -> None:
        """清空 API 调用历史"""
        self.mock_router.clear_call_history()
    
    # ==================== API 响应设置 ====================
    
    def set_api_response(self, action: str, response: dict) -> None:
        """设置 API 响应"""
        self.mock_router.set_api_response(action, response)


@asynccontextmanager
async def create_test_suite(**kwargs):
    """
    创建测试套件的异步上下文管理器
    
    使用示例：
    ```python
    async with create_test_suite() as suite:
        await suite.register_plugin(MyPlugin)
        await suite.inject_group_message("/hello")
    ```
    """
    suite = E2ETestSuite(**kwargs)
    suite.setup()
    try:
        yield suite
    finally:
        suite.teardown()
