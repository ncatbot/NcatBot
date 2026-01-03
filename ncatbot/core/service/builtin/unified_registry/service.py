"""统一注册服务

负责命令和过滤器的统一管理功能。
"""

from typing import Dict, Callable, TYPE_CHECKING, List, Tuple

from ncatbot.utils import get_log
from ...base import BaseService
from .executor import FunctionExecutor
from .command_runner import CommandRunner
from .filter_system import filter_registry
from .filter_system.event_registry import event_registry
from .command_system.registry.registry import command_registry
from .command_system.utils import CommandSpec

if TYPE_CHECKING:
    from ncatbot.core import MessageEvent, BaseEvent

LOG = get_log("UnifiedRegistryService")


class UnifiedRegistryService(BaseService):
    """统一注册服务

    提供过滤器和命令的统一管理功能。
    """

    name = "unified_registry"
    description = "统一的过滤器和命令注册服务"
    _executor: FunctionExecutor
    _command_runner: CommandRunner

    def __init__(self, **config):
        super().__init__(**config)

        # 注册表引用
        self.filter_registry = filter_registry
        self.command_registry = command_registry
        self.event_registry = event_registry

        # 状态管理
        self._initialized = False
        self.prefixes: List[str] = []

    # ==========================================================================
    # region 生命周期
    # ==========================================================================

    async def on_load(self) -> None:
        """服务加载时的初始化"""
        self._executor = FunctionExecutor()
        self._executor.set_plugin_loader(self.plugin_loader)
        LOG.info("统一注册服务已加载")

    async def on_close(self) -> None:
        """服务关闭时清理"""
        self.clear()
        LOG.info("统一注册服务已关闭")

    # ==========================================================================
    # region 插件管理
    # ==========================================================================

    @classmethod
    def set_current_plugin_name(cls, plugin_name: str) -> None:
        """设置当前注册的插件名"""
        event_registry.set_current_plugin_name(plugin_name)
        command_registry.set_current_plugin_name(plugin_name)
        filter_registry.set_current_plugin_name(plugin_name)

    @property
    def plugins(self) -> List:
        """获取已加载的插件列表"""
        if self._executor:
            return self._executor.plugins
        return []

    def handle_plugin_unload(self, plugin_name: str) -> None:
        """处理插件卸载，清理相关缓存"""
        LOG.debug(f"处理插件卸载: {plugin_name}")
        self.command_registry.root_group.revoke_plugin(plugin_name)
        self.filter_registry.revoke_plugin(plugin_name)
        self.event_registry.revoke_plugin(plugin_name)
        self.clear()
        self.initialize_if_needed()

    def handle_plugin_load(self) -> None:
        """处理插件加载，重新初始化"""
        self.clear()
        self.initialize_if_needed()

    # ==========================================================================
    # region 事件处理器注册
    # ==========================================================================

    def register_notice_handler(self, func: Callable) -> Callable:
        """注册通知事件处理器"""
        return self.event_registry.notice_handler(func)

    def register_request_handler(self, func: Callable) -> Callable:
        """注册请求事件处理器"""
        return self.event_registry.request_handler(func)

    # ==========================================================================
    # region 过滤器执行
    # ==========================================================================

    async def run_pure_filters(self, event: "MessageEvent") -> None:
        """遍历执行纯过滤器函数（不含命令函数）"""
        if not self._executor:
            return
        for func in filter_registry._function_filters.values():
            if getattr(func, "__is_command__", False):
                continue
            await self._executor.execute(func, event)

    # ==========================================================================
    # region 事件分发
    # ==========================================================================

    async def handle_message_event(self, event: "MessageEvent") -> None:
        """处理消息事件（命令和过滤器）"""
        self.initialize_if_needed()
        await self._command_runner.run(event)
        await self.run_pure_filters(event)

    async def handle_notice_event(self, event: "BaseEvent") -> bool:
        """处理通知事件"""
        for func in self.event_registry.notice_handlers:
            await self._executor.execute(func, event)
        return True

    async def handle_request_event(self, event: "BaseEvent") -> bool:
        """处理请求事件"""
        for func in self.event_registry.request_handlers:
            await self._executor.execute(func, event)
        return True

    async def handle_legacy_event(self, event_data: "BaseEvent") -> bool:
        """处理通知和请求事件（兼容旧 API）"""
        self.initialize_if_needed()
        if event_data.post_type == "notice":
            return await self.handle_notice_event(event_data)
        elif event_data.post_type == "request":
            return await self.handle_request_event(event_data)
        return True

    # ==========================================================================
    # region 初始化
    # ==========================================================================

    def initialize_if_needed(self) -> None:
        """首次触发时构建命令分发表并做严格冲突检测"""
        if self._initialized:
            return

        self._initialized = True

        # 收集所有前缀
        self.prefixes = self._collect_prefixes()
        LOG.info(f"命令前缀集合: {self.prefixes}")

        # 检查前缀冲突
        self._check_prefix_conflicts()

        self._command_runner = CommandRunner(
            prefixes=self.prefixes,
            executor=self._executor,
            event_bus=self.event_bus,
        )

        # 构建命令索引
        self._build_command_index()

    def _collect_prefixes(self) -> List[str]:
        """收集所有命令前缀"""
        prefixes = list(
            dict.fromkeys(
                prefix
                for registry in command_registry.command_registries
                for prefix in registry.prefixes
            )
        )
        if "" in prefixes:
            prefixes.remove("")
        return prefixes

    def _check_prefix_conflicts(self) -> None:
        """检查消息级前缀集合冲突"""
        norm_prefixes = [p.lower() for p in self.prefixes]
        for i, p1 in enumerate(norm_prefixes):
            for j, p2 in enumerate(norm_prefixes):
                if i != j and p2.startswith(p1):
                    LOG.error(f"消息前缀冲突: '{p1}' 与 '{p2}' 存在包含关系")
                    raise ValueError(f"prefix conflict: {p1} vs {p2}")

    def _build_command_index(self) -> None:
        """构建命令索引"""
        if not self._command_runner:
            return

        command_map = command_registry.get_all_commands()
        alias_map = command_registry.get_all_aliases()

        # 过滤出标记为命令的函数
        filtered_commands: Dict[Tuple[str, ...], CommandSpec] = {
            path: cmd
            for path, cmd in command_map.items()
            if getattr(cmd.func, "__is_command__", False)
        }

        filtered_aliases: Dict[Tuple[str, ...], CommandSpec] = {
            path: cmd
            for path, cmd in alias_map.items()
            if getattr(cmd.func, "__is_command__", False)
        }

        self._command_runner.resolver.build_index(filtered_commands, filtered_aliases)
        LOG.debug(
            f"初始化完成：命令={len(filtered_commands)}, 别名={len(filtered_aliases)}"
        )

    # ==========================================================================
    # region 清理
    # ==========================================================================

    def clear(self) -> None:
        """清理缓存"""
        if hasattr(self, "_executor") and self._executor:
            self._executor.clear_cache()
        if hasattr(self, "_command_runner") and self._command_runner:
            self._command_runner.clear()
        self._initialized = False
        self.prefixes = []
