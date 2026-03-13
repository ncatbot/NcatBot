"""
RegistryEngine - 统一的命令/过滤器/事件处理器注册与执行引擎

从 UnifiedRegistryService 重构，不再继承 BaseService。
由 BotClient 直接持有和管理，直接订阅 EventBus。
"""

from typing import Callable, Dict, List, Optional, Tuple, TYPE_CHECKING

from ncatbot.utils import get_log
from ncatbot.core.service.builtin.unified_registry.executor import FunctionExecutor
from ncatbot.core.service.builtin.unified_registry.command_runner import CommandRunner
from ncatbot.core.service.builtin.unified_registry.filter_system import filter_registry
from ncatbot.core.service.builtin.unified_registry.filter_system.event_registry import (
    event_registry,
)
from ncatbot.core.service.builtin.unified_registry.command_system.registry.registry import (
    command_registry,
)
from ncatbot.core.service.builtin.unified_registry.command_system.utils import (
    CommandSpec,
)

if TYPE_CHECKING:
    from ncatbot.core.event import MessageEvent, BaseEvent
    from ncatbot.plugin_system import BasePlugin
    from ncatbot.core.client.client import BotClient

LOG = get_log("RegistryEngine")


class RegistryEngine:
    """统一的命令/过滤器/事件处理器注册与执行引擎

    不继承 BaseService。由 BotClient 直接持有和管理。

    组合关系：
    - 持有 CommandRunner（命令匹配与执行）
    - 持有 FunctionExecutor（函数调用与参数注入）
    - 引用全局注册表（command_registry, filter_registry, event_registry）
    """

    def __init__(self):
        self._initialized = False
        self._executor: Optional[FunctionExecutor] = None
        self._command_runner: Optional[CommandRunner] = None
        self.prefixes: List[str] = []

        # 注册表引用
        self.command_registry = command_registry
        self.filter_registry = filter_registry
        self.event_registry = event_registry

        # BotClient 引用（过渡阶段，用于 CommandRunner 兼容）
        self._bot_client: Optional["BotClient"] = None

    def set_bot_client(self, bot_client: "BotClient") -> None:
        """注入 BotClient 引用（过渡期使用，最终由 plugin_resolver 替代）"""
        self._bot_client = bot_client

    # ==================================================================
    # 生命周期
    # ==================================================================

    def initialize(self) -> None:
        """初始化引擎"""
        if self._initialized:
            return

        self._executor = FunctionExecutor()
        self._initialized_internal()

    def _initialized_internal(self) -> None:
        """内部初始化逻辑"""
        self._initialized = True

        # 收集所有前缀
        self.prefixes = self._collect_prefixes()
        LOG.info(f"命令前缀集合: {self.prefixes}")

        # 检查前缀冲突
        self._check_prefix_conflicts()

        self._command_runner = CommandRunner(
            prefixes=self.prefixes,
            executor=self._executor,
        )

        # 构建命令索引
        self._build_command_index()

    def initialize_if_needed(self) -> None:
        """惰性初始化"""
        if not self._initialized:
            if self._executor is None:
                self._executor = FunctionExecutor()
            self._initialized_internal()

    def clear(self) -> None:
        """清理所有状态"""
        if self._command_runner:
            self._command_runner.clear()
        self._initialized = False
        self.prefixes = []

    # ==================================================================
    # 插件管理
    # ==================================================================

    @staticmethod
    def set_current_plugin_name(plugin_name: str) -> None:
        """设置当前注册的插件名"""
        event_registry.set_current_plugin_name(plugin_name)
        command_registry.set_current_plugin_name(plugin_name)
        filter_registry.set_current_plugin_name(plugin_name)

    def handle_plugin_unload(self, plugin_name: str) -> None:
        """处理插件卸载"""
        LOG.debug(f"处理插件卸载: {plugin_name}")
        self.command_registry.root_group.revoke_plugin(plugin_name)
        self.filter_registry.revoke_plugin(plugin_name)
        self.event_registry.revoke_plugin(plugin_name)
        self.clear()
        self.initialize_if_needed()

    def handle_plugin_load(self) -> None:
        """处理插件加载"""
        self.clear()
        self.initialize_if_needed()

    # ==================================================================
    # 事件处理器注册
    # ==================================================================

    def register_notice_handler(self, func: Callable) -> Callable:
        """注册通知事件处理器"""
        return self.event_registry.notice_handler(func)

    def register_request_handler(self, func: Callable) -> Callable:
        """注册请求事件处理器"""
        return self.event_registry.request_handler(func)

    # ==================================================================
    # 过滤器执行
    # ==================================================================

    async def run_pure_filters(self, event: "MessageEvent") -> None:
        """遍历执行纯过滤器函数"""
        if not self._executor or not self._bot_client:
            return
        for full_name, func in filter_registry._function_filters.items():
            if getattr(func, "__is_command__", False):
                continue

            await self._executor.execute(func, self._bot_client, event)

    # ==================================================================
    # 事件分发
    # ==================================================================

    async def handle_message_event(self, event: "MessageEvent") -> None:
        """处理消息事件（命令和过滤器）"""
        self.initialize_if_needed()
        await self._command_runner.run(event, self._bot_client)  # type: ignore
        await self.run_pure_filters(event)

    async def handle_notice_event(self, event: "BaseEvent") -> bool:
        """处理通知事件"""
        for func, plugin_name in self.event_registry.notice_handlers.items():
            plugin_instance = self._get_plugin_instance(plugin_name, func)
            await self._executor.execute(func, plugin_instance, event)
        return True

    async def handle_request_event(self, event: "BaseEvent") -> bool:
        """处理请求事件"""
        for func, plugin_name in self.event_registry.request_handlers.items():
            plugin_instance = self._get_plugin_instance(plugin_name, func)
            await self._executor.execute(func, plugin_instance, event)
        return True

    async def handle_meta_event(self, event: "BaseEvent") -> bool:
        """处理元事件"""
        for func, plugin_name in self.event_registry.meta_handlers.items():
            plugin_instance = self._get_plugin_instance(plugin_name, func)
            await self._executor.execute(func, plugin_instance, event)
        return True

    async def handle_legacy_event(self, event: "BaseEvent") -> bool:
        """统一入口：根据 post_type 分发"""
        self.initialize_if_needed()
        if event.post_type == "notice":
            return await self.handle_notice_event(event)
        elif event.post_type == "request":
            return await self.handle_request_event(event)
        elif event.post_type == "meta_event":
            return await self.handle_meta_event(event)
        return True

    # ==================================================================
    # 内部方法
    # ==================================================================

    def _get_plugin_instance(
        self, plugin_name: str, func: Callable
    ) -> Optional["BasePlugin"]:
        """通过 bot_client 获取插件实例"""
        if not self._bot_client:
            return None
        try:
            plugin_class = self._bot_client.get_plugin_class_by_name(plugin_name)
            if func in plugin_class.__dict__.values():
                return self._bot_client.get_plugin(plugin_class)
        except Exception:
            pass
        return None

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
        """检查前缀冲突"""
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
