"""
生命周期管理

负责 Bot 的启动、退出和运行模式管理。
"""

import asyncio
import sys
from typing import Optional, Union, TypedDict, TYPE_CHECKING

from typing_extensions import Unpack

from ncatbot.utils import get_log, ncatbot_config
from ncatbot.utils.error import NcatBotError, NcatBotConnectionError
from ncatbot.core.adapter import launch_napcat_service

if TYPE_CHECKING:
    from ncatbot.core.api import BotAPI
    from ncatbot.core.service import ServiceManager
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
    mock: Optional[bool]
    skip_plugin_load: Optional[bool]


LEGAL_ARGS = StartArgs.__annotations__.keys()


class LifecycleManager:
    def __init__(
        self,
        services: "ServiceManager",
        event_bus: "EventBus",
        registry: "EventRegistry",
    ):
        self.services = services
        self.event_bus = event_bus
        self.registry = registry
        
        self._running = False
        self.plugin_loader = None
        self.api: Optional["BotAPI"] = None
        self.dispatcher: Optional["EventDispatcher"] = None
        
        # 异步任务控制
        self._main_task: Optional[asyncio.Task] = None
        self._startup_event: Optional[asyncio.Event] = None
        self._skip_plugin_load = False

    def _prepare_startup(self, **kwargs: Unpack[StartArgs]) -> bool:
        """通用启动准备"""
        mock_mode = kwargs.pop("mock", False)
        self._skip_plugin_load = kwargs.pop("skip_plugin_load", False)
        
        for key, value in kwargs.items():
            if key not in LEGAL_ARGS:
                raise NcatBotError(f"非法启动参数: {key}")
            if value is not None:
                ncatbot_config.update_value(key, value)

        ncatbot_config.validate_config()

        from ncatbot.plugin_system import PluginLoader
        self.plugin_loader = PluginLoader(
            self.event_bus,
            self.services,
            debug=ncatbot_config.debug,
        )
        self._running = True

        if not mock_mode:
            launch_napcat_service()
            
        return mock_mode

    async def _core_execution(self):
        """核心执行流"""
        try:
            # 1. 加载服务
            await self.services.load_all()

            # 2. 构建 API
            router = self.services.message_router
            from ncatbot.core.api import BotAPI
            from .dispatcher import EventDispatcher

            self.api = BotAPI(router.send, service_manager=self.services)
            self.dispatcher = EventDispatcher(self.event_bus, self.api)
            router.set_event_callback(self.dispatcher)

            # 3. 加载插件
            if not self._skip_plugin_load and self.plugin_loader:
                await self.plugin_loader.load_plugins()

            # 4. 关键：通知启动完成
            # 在开始无限循环监听之前，设置事件，告知 start_background 可以返回了
            if self._startup_event:
                self._startup_event.set()

            # 5. 开始监听 (阻塞直到连接断开或任务取消)
            if router.websocket:
                await router.websocket.listen()
                
        except asyncio.CancelledError:
            # 正常退出信号
            LOG.info("Bot 运行任务被取消，正在停止...")
            raise
        except Exception as e:
            LOG.error(f"运行时发生错误: {e}")
            # 如果错误发生在启动阶段，也要释放等待锁，否则 start_background 会死锁
            if self._startup_event and not self._startup_event.is_set():
                # 这里不设置 set，而是让 task 结束，外层检测到 task done 会抛出异常
                pass 
            raise
        finally:
            await self._cleanup()

    async def _cleanup(self):
        """资源清理"""
        if not self._running:
            return
        
        self._running = False
        
        # 1. 卸载插件
        if self.plugin_loader:
            await self.plugin_loader.unload_all()
        
        # 2. 关闭服务 (包括 Websocket 连接)
        await self.services.close_all()
        
        LOG.info("Bot 资源已释放")

    # ================= 启动入口 =================

    async def run_backend_async(self, **kwargs: Unpack[StartArgs]) -> "BotAPI":
        """
        [推荐] 安全的异步非阻塞启动
        
        1. 启动 NapCat
        2. 建立 WebSocket 连接
        3. 确认连接成功后，立即返回 BotAPI
        4. Bot 在后台任务中运行
        
        Returns:
            BotAPI: 操作 Bot 的接口对象
            
        Raises:
            NcatBotError: 启动超时或失败
        """
        if self._running:
             LOG.warning("Bot 已经在运行中")
             return self.api  # type: ignore

        self._prepare_startup(**kwargs)
        
        # 创建同步事件
        self._startup_event = asyncio.Event()
        
        # 创建后台任务
        self._main_task = asyncio.create_task(self._core_execution())
        
        # 等待启动完成 或 任务崩溃
        # 我们同时等待 startup_event (成功) 和 _main_task (可能失败退出)
        done, pending = await asyncio.wait(
            [
                asyncio.create_task(self._startup_event.wait()),
                self._main_task
            ],
            return_when=asyncio.FIRST_COMPLETED
        )

        # 检查是否是任务先结束了（说明启动失败崩溃了）
        if self._main_task in done:
            exception = self._main_task.exception()
            if exception:
                raise exception
            else:
                raise NcatBotError("Bot 启动任务意外结束，未返回 API")

        # 此时 startup_event 必然已 set
        LOG.info("Bot 后台启动成功")
        return self.api  # type: ignore

    def run(self, **kwargs: Unpack[StartArgs]):
        """同步阻塞启动 (命令行用)"""
        try:
            self._prepare_startup(**kwargs)
            asyncio.run(self._core_execution())
        except KeyboardInterrupt:
            LOG.info("停止运行...")
        except Exception as e:
            LOG.error(f"启动失败: {e}")
            sys.exit(1)

    # ================= 退出逻辑 =================

    async def shutdown(self):
        """
        异步安全关闭 Bot
        
        取消后台任务并等待清理完成。推荐在测试 teardown 中使用。
        清理工作由 _core_execution 的 finally 块中的 _cleanup() 完成。
        """
        if not self._running:
            return
        
        LOG.info("正在安全关闭 Bot...")
        
        if self._main_task and not self._main_task.done():
            self._main_task.cancel()
            try:
                await self._main_task
            except asyncio.CancelledError:
                pass  # 预期的取消
            except Exception:
                pass  # 忽略其他异常，清理已在 finally 中完成

    def bot_exit(self):
        """
        退出 Bot (支持在异步或同步环境中调用)
        
        触发后台任务的取消，清理由 _core_execution 的 finally 块完成。
        """
        if not self._running:
            LOG.warning("Bot 未运行")
            return

        LOG.info("正在请求退出 Bot...")
        
        # 取消后台任务，清理由 finally 块的 _cleanup() 完成
        if self._main_task and not self._main_task.done():
            self._main_task.cancel()