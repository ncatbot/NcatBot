"""BotClient — Bot 统一入口（Composition Root）

负责引导 Adapter 启动、组装 BotAPIClient、接通事件流、管理服务生命周期。
支持单/多适配器，多平台共享同一事件分发器。
作为应用编排层，允许依赖所有模块（core / plugin / service / api / adapter）。
"""

from __future__ import annotations

import asyncio
import inspect
import platform
from pathlib import Path
from typing import Any, Awaitable, Callable, List, Optional, Sequence, TypeVar

from ncatbot.adapter import BaseAdapter, adapter_registry
from ncatbot.api import BotAPIClient, QQAPIClient, MiscAPI
from ncatbot.core import (
    AsyncEventDispatcher,
    HandlerDispatcher,
    DispatchFilterHook,
    flush_pending,
)
from ncatbot.plugin import PluginLoader
from ncatbot.service import ServiceManager
from ncatbot.utils import (
    get_config_manager,
    get_log,
    setup_logging,
    ncatbot_config,
    MISSING,
)

LOG = get_log("BotClient")

AsyncLifecycleCallback = Callable[..., Awaitable[Any]]
LifecycleCallback = TypeVar("LifecycleCallback", bound=AsyncLifecycleCallback)


class BotClient:
    """Bot 生命周期管理器

    用法（零配置 — 从 config.yaml 自动加载适配器）::

        bot = BotClient()

        @bot.on("message.group")
        async def on_group_msg(event):
            await event.reply("hello")

        bot.run()

    用法（编程式指定适配器）::

        from ncatbot.adapter import NapCatAdapter
        bot = BotClient(adapters=[NapCatAdapter(config={...})])
        bot.run()
    """

    def __init__(
        self,
        *,
        adapters: Optional[Sequence[BaseAdapter]] = None,
        plugins_dir: Any = MISSING,
        debug: Any = MISSING,
        hot_reload: Any = MISSING,
    ) -> None:
        mgr = get_config_manager()
        mgr.apply_runtime_overrides(
            debug=debug, plugins_dir=plugins_dir, hot_reload=hot_reload
        )
        setup_logging(debug=mgr.effective_debug)

        # 构建适配器列表
        if adapters is not None:
            self._adapters: List[BaseAdapter] = list(adapters)
        elif adapters is None:
            # 从配置文件加载
            self._adapters = self._create_adapters_from_config()

        # 按 platform 去重检查
        seen: dict[str, str] = {}
        for a in self._adapters:
            p = getattr(a, "platform", a.name)
            if p in seen:
                raise ValueError(f"重复的平台 '{p}'：{a.name} 与 {seen[p]} 冲突")
            seen[p] = a.name

        self._api: Optional[BotAPIClient] = None
        self._dispatcher: Optional[AsyncEventDispatcher] = None
        self._handler_dispatcher: Optional[HandlerDispatcher] = None
        self._service_manager = ServiceManager()
        self._plugin_loader = PluginLoader()
        self._plugins_dir = Path(mgr.effective_plugins_dir())
        self._running = False
        self._listen_task: Optional[asyncio.Task] = None
        self._listen_tasks: List[asyncio.Task] = []

        # 待注册的 handler（在 run 之前通过 @bot.on() 收集）
        self._pending_handlers: list[tuple[str, object, dict]] = []

        # 生命周期回调（通过 @bot.on_startup() / @bot.on_close() 收集）
        self._startup_callbacks: list[AsyncLifecycleCallback] = []
        self._close_callbacks: list[AsyncLifecycleCallback] = []

    @staticmethod
    def _create_adapters_from_config() -> List[BaseAdapter]:
        """从 config.yaml 的 adapters 列表创建适配器实例。"""
        cfg = ncatbot_config.config
        entries = [e for e in cfg.adapters if e.enabled]
        if not entries:
            raise ValueError(
                "配置文件中没有启用的适配器 (adapters 列表为空或全部 enabled: false)"
            )

        result: List[BaseAdapter] = []
        for entry in entries:
            adapter = adapter_registry.create(
                entry,
                bot_uin=cfg.bot_uin,
                websocket_timeout=cfg.websocket_timeout,
            )
            LOG.info(
                "从配置创建适配器: type=%s, platform=%s",
                entry.type,
                entry.platform or adapter.platform,
            )
            result.append(adapter)
        return result

    @property
    def plugin_loader(self) -> PluginLoader:
        return self._plugin_loader

    @property
    def service_manager(self) -> ServiceManager:
        return self._service_manager

    @property
    def api(self) -> BotAPIClient:
        if self._api is None:
            LOG.warning("API 不可用：BotClient 尚未启动")
            raise RuntimeError("API 不可用：BotClient 尚未启动")
        return self._api

    @property
    def dispatcher(self) -> AsyncEventDispatcher:
        if self._dispatcher is None:
            LOG.warning("Dispatcher 不可用：BotClient 尚未启动")
            raise RuntimeError("Dispatcher 不可用：BotClient 尚未启动")
        return self._dispatcher

    @property
    def handler_dispatcher(self) -> HandlerDispatcher:
        if self._handler_dispatcher is None:
            LOG.warning("HandlerDispatcher 不可用：BotClient 尚未启动")
            raise RuntimeError("HandlerDispatcher 不可用：BotClient 尚未启动")
        return self._handler_dispatcher

    def _register_lifecycle_callback(
        self,
        callbacks: list[AsyncLifecycleCallback],
    ) -> Callable[[LifecycleCallback], LifecycleCallback]:
        def decorator(callback: LifecycleCallback) -> LifecycleCallback:
            if not inspect.iscoroutinefunction(callback):
                raise TypeError("生命周期回调必须使用 async def 定义")
            callbacks.append(callback)
            return callback

        return decorator

    def on_startup(self) -> Callable[[LifecycleCallback], LifecycleCallback]:
        """注册启动回调（bot 就绪后自动调用）。

        回调在 ``_running = True`` 之后执行，此时 api / dispatcher / 服务 / 插件均已可用。

        用法::

            @bot.on_startup()
            async def on_start():
                print("Bot 已启动")
        """
        return self._register_lifecycle_callback(self._startup_callbacks)

    def on_close(self) -> Callable[[LifecycleCallback], LifecycleCallback]:
        """注册关闭回调（shutdown 时自动调用）。

        回调在 ``_running = False`` 之后、适配器断开/插件卸载/服务关闭**之前**执行，
        因此仍可访问运行中的服务和插件。

        用法::

            @bot.on_close()
            async def on_close():
                print("Bot 正在关闭")
        """
        return self._register_lifecycle_callback(self._close_callbacks)

    async def _execute_lifecycle_callbacks(
        self, callbacks: list[AsyncLifecycleCallback], name: str
    ) -> None:
        """依次执行生命周期回调。"""
        for cb in callbacks:
            try:
                await cb()
            except Exception as e:
                LOG.error("执行%s回调 %s 异常: %s", name, cb.__name__, e)

    # ---- 启动 ----

    def run(self) -> None:
        """同步阻塞启动（setup → connect → listen → shutdown）"""
        try:
            asyncio.run(self._run_blocking())
        except KeyboardInterrupt:
            LOG.info("收到 Ctrl+C，正在退出…")

    async def run_async(self) -> None:
        """异步非阻塞启动。

        完成 startup 后在后台启动监听，立即返回::

            bot = BotClient()
            await bot.run_async()
            # 此处 bot.api / bot.dispatcher 已可用
            async with bot.dispatcher.events(EventType.MESSAGE) as stream:
                async for event in stream:
                    ...
        """
        await self._startup()
        # listen 已在 _startup_core 中启动，包装为单 task 供 shutdown 使用
        self._listen_task = asyncio.create_task(self._listen_forever())
        LOG.info("Bot 已就绪，后台监听已启动")

    async def shutdown(self) -> None:
        """关闭服务、Dispatcher 和 Adapter，释放资源。"""
        if not self._running:
            return
        self._running = False
        LOG.info("正在关闭…")

        await self._execute_lifecycle_callbacks(self._close_callbacks, "关闭")

        # 优先断开适配器（释放端口等网络资源），使 listen 循环自然退出
        for adapter in self._adapters:
            try:
                await adapter.disconnect()
            except Exception as e:
                LOG.error("断开适配器 %s 异常: %s", adapter.name, e)

        # 等待所有监听 task 结束（已由 disconnect 触发退出）
        for task in self._listen_tasks:
            if not task.done():
                task.cancel()
        if self._listen_task and not self._listen_task.done():
            self._listen_task.cancel()
        for task in self._listen_tasks:
            try:
                await task
            except (asyncio.CancelledError, Exception):
                pass
        if self._listen_task:
            try:
                await self._listen_task
            except (asyncio.CancelledError, Exception):
                pass

        # 以下各步骤独立 try/except，避免互相阻塞
        try:
            await self._plugin_loader.stop_hot_reload()
            await self._plugin_loader.unload_all()
        except Exception as e:
            LOG.error("卸载插件异常: %s", e)

        try:
            await self._service_manager.close_all()
        except Exception as e:
            LOG.error("关闭服务异常: %s", e)

        try:
            if self._handler_dispatcher is not None:
                await self._handler_dispatcher.stop()
            if self._dispatcher is not None:
                await self._dispatcher.close()
        except Exception as e:
            LOG.error("关闭分发器异常: %s", e)

        self._stop_configured_napcat_runtimes()

        LOG.info("已关闭")

    # ---- 内部 ----

    async def _run_blocking(self) -> None:
        """同步 run() 的内部实现：startup → 阻塞等待 listen 结束 → shutdown"""
        await self._startup()
        LOG.info("Bot 已就绪（%d 个适配器）", len(self._adapters))
        try:
            # listen 已在 _startup_core 中启动，这里只等待其结束
            await asyncio.gather(*self._listen_tasks)
        except asyncio.CancelledError:
            LOG.info("Bot 被取消")
        finally:
            await self.shutdown()

    async def _safe_listen(self, adapter: "BaseAdapter") -> None:
        """安全监听单个适配器，崩溃时仅记录日志而不影响其他适配器。"""
        try:
            await adapter.listen()
        except asyncio.CancelledError:
            raise
        except Exception as e:
            LOG.error("适配器 %s 监听异常，已停止: %s", adapter.name, e)

    def _start_listening(self) -> None:
        """为每个适配器启动后台监听 task。"""
        self._listen_tasks = [
            asyncio.create_task(self._safe_listen(a)) for a in self._adapters
        ]
        LOG.info("已启动 %d 个适配器的事件监听", len(self._listen_tasks))

    async def _listen_forever(self) -> None:
        """后台监听 task，异常时自动 shutdown（供 run_async 使用）"""
        try:
            await asyncio.gather(*self._listen_tasks)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            LOG.error("监听异常: %s", e)
        finally:
            await self.shutdown()

    async def _startup(self) -> None:
        """引导启动：adapter → API → dispatcher → 服务 → 插件 → 热重载"""
        await self._startup_core()
        await self._setup_plugins()
        self._running = True
        await self._execute_lifecycle_callbacks(self._startup_callbacks, "启动")

    async def _startup_core(self) -> None:
        """核心启动（不含插件加载）：adapters → API → dispatcher → listen → 服务"""
        await self._setup_adapters()
        self._setup_api()
        self._setup_dispatcher()
        self._setup_handler_dispatcher()
        self._start_listening()
        await self._setup_services()

    async def _setup_adapters(self) -> None:
        """准备并连接所有 Adapter（含 pip 依赖检查）。"""
        skipped: list[BaseAdapter] = []
        for adapter in self._adapters:
            LOG.info(
                "正在启动 Adapter: %s (platform=%s)",
                adapter.name,
                getattr(adapter, "platform", "?"),
            )
            if not await adapter.ensure_deps():
                LOG.warning("适配器 %s 的 pip 依赖未满足，跳过该适配器", adapter.name)
                skipped.append(adapter)
                continue
            await adapter.setup()
            await adapter.connect()

        for adapter in skipped:
            self._adapters.remove(adapter)
        if not self._adapters:
            raise ValueError("所有适配器的依赖均未满足，无法启动")

    def _setup_api(self) -> None:
        """从所有 Adapter 取出底层 IAPIClient，包装为平台 Client 后注册到 BotAPIClient。"""
        # 平台 → 包装类注册表
        _CLIENT_REGISTRY: dict[str, type] = {"qq": QQAPIClient}

        self._api = BotAPIClient()

        # 注册与平台无关的 MiscAPI
        self._api.register_platform("misc", MiscAPI(get_config_manager().config))

        for adapter in self._adapters:
            platform = getattr(adapter, "platform", adapter.name)
            raw_api = adapter.get_api()
            if platform in _CLIENT_REGISTRY:
                client = _CLIENT_REGISTRY[platform](raw_api)
            else:
                client = raw_api
            self._api.register_platform(platform, client)
        LOG.info("BotAPIClient 已就绪（平台: %s）", list(self._api.platforms.keys()))

    def _setup_dispatcher(self) -> None:
        """创建事件分发器并接通所有 Adapter 的事件回调。"""
        self._dispatcher = AsyncEventDispatcher()
        for adapter in self._adapters:
            adapter.set_event_callback(self._dispatcher.callback)

    def _setup_handler_dispatcher(self) -> None:
        """创建 HandlerDispatcher 并订阅事件流。"""
        # 复用 _setup_api() 中已包装好的平台客户端（含 sugar 层），
        # 而非裸 adapter.get_api()，否则事件实体上的 sugar 方法会缺失。
        platform_apis = {}
        for adapter in self._adapters:
            platform = getattr(adapter, "platform", adapter.name)
            try:
                platform_apis[platform] = self._api.platform(platform)
            except KeyError:
                platform_apis[platform] = adapter.get_api()

        self._handler_dispatcher = HandlerDispatcher(
            api=self._api,
            service_manager=self._service_manager,
            platform_apis=platform_apis,
            global_hooks=[DispatchFilterHook()],
        )
        self._handler_dispatcher.start(self.dispatcher)

    async def _setup_services(self) -> None:
        """注册并加载所有内置服务。"""
        self._service_manager.set_event_callback(self.dispatcher.callback)
        self._service_manager.register_builtin()
        await self._service_manager.load_all()

    async def _setup_plugins(self) -> None:
        """加载插件并配置热重载。"""

        self._plugin_loader.set_handler_dispatcher(self.handler_dispatcher)

        # 非插件模式：将模块级 @registrar.on_*() 收集的 handler 注册到 dispatcher
        flush_pending(self.handler_dispatcher, "__global__")

        def _inject_plugin_deps(plugin, manifest):
            plugin.services = self._service_manager
            plugin.api = self._api
            plugin._dispatcher = self._dispatcher
            plugin._plugin_loader = self._plugin_loader

        self._plugin_loader._on_plugin_init = _inject_plugin_deps
        await self._plugin_loader.load_builtin_plugins()
        await self._plugin_loader.load_all(self._plugins_dir)

        mgr = get_config_manager()
        if mgr.effective_hot_reload() and self._service_manager.has("file_watcher"):
            fw = self._service_manager.file_watcher
            fw.add_watch_dir(str(self._plugins_dir.resolve()))
            self._plugin_loader.setup_hot_reload(fw)

    def _stop_configured_napcat_runtimes(self) -> None:
        """按适配器配置停止本地 NapCat 进程。"""
        if platform.system() != "Linux":
            return

        for adapter in self._adapters:
            napcat_config = getattr(adapter, "napcat_config", None)
            if getattr(napcat_config, "stop_napcat", False) is not True:
                continue

            stop_runtime = getattr(adapter, "stop_managed_runtime", None)
            if not callable(stop_runtime):
                continue

            try:
                stop_runtime()
            except Exception as e:
                LOG.error("停止 NapCat 运行时异常: %s", e)
