"""
生命周期管理

负责 Bot 的启动、退出和运行模式管理。
"""

import asyncio
import threading
import traceback
from typing import Callable, Union, Optional, TypedDict, TYPE_CHECKING

from typing_extensions import Unpack

from ncatbot.utils import get_log, run_coroutine, status, ncatbot_config
from ncatbot.utils.error import NcatBotError, NcatBotConnectionError
from ncatbot.core.adapter import launch_napcat_service

if TYPE_CHECKING:
    from ncatbot.core.api import BotAPI
    from ncatbot.core.service import ServiceManager, MessageRouter
    from .event_bus import EventBus
    from .registry import EventRegistry
    from .dispatcher import EventDispatcher

LOG = get_log("Lifecycle")


class StartArgs(TypedDict, total=False):
    """启动参数类型定义"""
    bt_uin: Union[str, int]
    root: Optional[str]
    ws_uri: Optional[str]
    webui_uri: Optional[str]
    ws_token: Optional[str]
    webui_token: Optional[str]
    ws_listen_ip: Optional[str]
    remote_mode: Optional[bool]
    enable_webui: Optional[bool]
    enable_webui_interaction: Optional[bool]
    debug: Optional[bool]
    mock: Optional[bool]  # Mock 模式，用于测试
    skip_plugin_load: Optional[bool]  # 跳过插件加载


LEGAL_ARGS = StartArgs.__annotations__.keys()


class LifecycleManager:
    """
    生命周期管理器
    
    职责：
    - Bot 启动流程
    - Bot 退出流程
    - 前台/后台运行模式
    - 插件加载器管理
    """
    
    def __init__(
        self,
        services: "ServiceManager",
        event_bus: "EventBus",
        registry: "EventRegistry",
    ):
        """
        初始化生命周期管理器
        
        Args:
            services: 服务管理器
            event_bus: 事件总线
            registry: 事件注册器
        """
        self.services = services
        self.event_bus = event_bus
        self.registry = registry
        
        self._running = False
        self.crash_flag = False
        self.plugin_loader = None
        self.api: Optional["BotAPI"] = None
        self.dispatcher: Optional["EventDispatcher"] = None  # 事件分发器
        
        # Mock 模式相关
        self._mock_mode = False
        
        # 后台运行相关
        self.lock: Optional[threading.Lock] = None
        self.release_callback: Optional[Callable[[None], None]] = None

    def start(self, **kwargs: Unpack[StartArgs]):
        """
        启动 Bot
        
        流程：
        1. 验证并应用配置参数
        2. 初始化插件加载器
        3. 加载插件
        4. 启动 NapCat 服务
        5. 加载内置服务并连接 WebSocket
        
        Args:
            mock: 是否启用 Mock 模式（用于测试，不建立网络连接）
            skip_plugin_load: 是否跳过插件加载
        """
        # 提取特殊参数
        mock_mode = kwargs.pop("mock", False)
        skip_plugin_load = kwargs.pop("skip_plugin_load", False)
        self._mock_mode = mock_mode
        
        # 验证并应用配置
        for key, value in kwargs.items():
            if key not in LEGAL_ARGS:
                raise NcatBotError(f"非法参数: {key}")
            if value is not None:
                ncatbot_config.update_value(key, value)

        ncatbot_config.validate_config()

        # 初始化插件系统（注入 ServiceManager）
        from ncatbot.plugin_system import PluginLoader
        self.plugin_loader = PluginLoader(
            self.event_bus,
            self.services,
            debug=ncatbot_config.debug,
        )
        self._running = True

        # 加载插件（可选跳过）
        if not skip_plugin_load:
            run_coroutine(self.plugin_loader.load_plugins)

        # Mock 模式：替换网络相关服务为 Mock 版本
        if mock_mode:
            self._replace_network_services_with_mock()

        # 启动服务
        if not mock_mode:
            launch_napcat_service()
        
        try:
            # 检查是否已有事件循环在运行
            try:
                loop = asyncio.get_running_loop()
                # 已有事件循环，使用 run_coroutine
                run_coroutine(self._async_start)
            except RuntimeError:
                # 没有事件循环，使用 asyncio.run
                asyncio.run(self._async_start())
        except NcatBotConnectionError:
            self.bot_exit()
            raise
    
    def _replace_network_services_with_mock(self):
        """
        替换网络相关服务为 Mock 版本
        
        - 使用 MockMessageRouter 替代真实的 WebSocket 连接
        - 使用 MockPreUploadService 替代真实的预上传服务
        - 保留其他真实服务（plugin_config, rbac 等）
        """
        LOG.info("Mock 模式：替换网络相关服务")
        
        from ncatbot.utils.testing.mock_services import MockMessageRouter, MockPreUploadService
        
        # 移除真实的网络相关服务，注册 Mock 版本
        if "message_router" in self.services._service_classes:
            del self.services._service_classes["message_router"]
            del self.services._service_configs["message_router"]
        if "preupload" in self.services._service_classes:
            del self.services._service_classes["preupload"]
            del self.services._service_configs["preupload"]
        
        self.services.register(MockMessageRouter)
        self.services.register(MockPreUploadService)
    
    async def _async_start(self):
        """异步启动流程（正常模式和 Mock 模式共用）"""
        # 加载所有服务
        await self.services.load_all()
        
        # 获取消息路由服务
        router = self.services.message_router
        
        from ncatbot.core.api import BotAPI
        from .dispatcher import EventDispatcher
        
        # 传入 service_manager 以支持预上传等服务
        self.api = BotAPI(router.send, service_manager=self.services)
        
        # 设置事件分发器
        self.dispatcher = EventDispatcher(self.event_bus, self.api)
        router.set_event_callback(self.dispatcher)
        
        # 开始监听（仅在有 WebSocket 连接时）
        await router.websocket.listen()
    
    # ==================== 测试辅助方法 ====================
    
    async def inject_event(self, event) -> None:
        """
        注入事件（仅 Mock 模式可用）
        
        将解析后的事件对象直接发布到 EventBus。
        
        Args:
            event: 事件对象（如 GroupMessageEvent, PrivateMessageEvent 等）
        """
        if not self._mock_mode:
            raise RuntimeError("inject_event 仅在 Mock 模式下可用")
        
        from .ncatbot_event import NcatBotEvent
        
        # 绑定 API 上下文（如果事件对象支持）
        if hasattr(event, 'bind_api') and self.api:
            event.bind_api(self.api)
        
        # 构造事件类型
        event_type = f"ncatbot.{event.post_type}"
        ncatbot_event = NcatBotEvent(event_type, event)
        
        await self.event_bus.publish(ncatbot_event)
    
    async def inject_raw_event(self, data: dict) -> None:
        """
        注入原始事件数据（仅 Mock 模式可用）
        
        将原始事件数据通过 EventDispatcher 解析并发布。
        
        Args:
            data: 原始事件数据（OneBot 格式）
        """
        if not self._mock_mode:
            raise RuntimeError("inject_raw_event 仅在 Mock 模式下可用")
        
        router = self.services.message_router
        if hasattr(router, "inject_event"):
            await router.inject_event(data)
        elif self.dispatcher:
            await self.dispatcher.dispatch(data)

    def bot_exit(self):
        """退出 Bot"""
        if not self._running:
            LOG.warning("Bot 未运行")
            return
        status.exit = True
        
        # 关闭所有服务
        run_coroutine(self.services.close_all)
        
        if self.plugin_loader:
            # 检查是否在事件循环中
            try:
                loop = asyncio.get_running_loop()
                # 在运行中的事件循环内，使用 run_coroutine
                run_coroutine(self.plugin_loader.unload_all)
            except RuntimeError:
                # 没有运行中的事件循环，使用 asyncio.run
                asyncio.run(self.plugin_loader.unload_all())
        LOG.info("Bot 已退出")

    def run_frontend(self, **kwargs: Unpack[StartArgs]):
        """
        前台运行（阻塞）
        
        适用于：命令行直接运行
        """
        try:
            self.start(**kwargs)
        except KeyboardInterrupt:
            self.bot_exit()

    def run_backend(self, **kwargs: Unpack[StartArgs]) -> "BotAPI":
        """
        后台运行（非阻塞）
        
        适用于：与其他程序集成
        
        Returns:
            BotAPI 实例
        """
        def run_async():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                self.start(**kwargs)
            except Exception as e:
                LOG.error(f"启动失败: {e}\n{traceback.format_exc()}")
                self.crash_flag = True
                if self.release_callback:
                    self.release_callback(None)
            finally:
                loop.close()

        self.lock = threading.Lock()
        self.lock.acquire()
        self.release_callback = lambda _: self.lock.release() # type: ignore
        self.registry.add_startup_handler(self.release_callback)

        thread = threading.Thread(target=run_async, daemon=True)
        thread.start()

        if not self.lock.acquire(timeout=90):
            raise NcatBotError("启动超时")
        if self.crash_flag:
            raise NcatBotError("启动失败", log=False)
        return self.api


    # ==================== 兼容别名 ====================
    run_blocking = run_frontend
    run_non_blocking = run_backend
    run = run_frontend
