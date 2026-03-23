"""
系统管理插件

内置插件，负责：
- 插件配置管理（查看/修改任意插件配置）
- 心跳超时检测（meta 事件监控）
- 内置 ``!`` 管理命令（热重载 / 加载 / 卸载 / 系统信息 / 开关配置）
"""

from __future__ import annotations

import asyncio
import importlib.metadata
import platform
import sys
import time as time_mod
from typing import Any, Dict, Optional, Set

from ...ncatbot_plugin import NcatBotPlugin
from ncatbot.core import registrar
from ncatbot.event import HasSender
from ncatbot.utils import get_config_manager, get_log

LOG = get_log("SystemManager")

_DENY = "无权执行此操作。"
_GROUP_DENY = "请在私聊中使用此命令（或开启 plugin.builtin_commands_group_allowed）。"
_OFF = "内置管理命令已关闭。"


def _builtin_reserved_names() -> Set[str]:
    from ncatbot.plugin.builtin import BUILTIN_PLUGINS

    return {p.name for p in BUILTIN_PLUGINS}


class SystemManagerPlugin(NcatBotPlugin):
    """系统管理插件"""

    name = "_system_manager"
    version = "1.0.0"
    author = "NcatBot"
    description = "系统内置管理插件：插件配置管理、心跳超时检测、内置管理命令"

    def _init_(self) -> None:
        self._last_heartbeat_time: float = time_mod.time()
        self._heartbeat_monitor_task: Optional[asyncio.Task] = None

    async def on_load(self) -> None:
        # 启动心跳监听
        self._heartbeat_monitor_task = asyncio.create_task(
            self._heartbeat_monitor_loop()
        )

        # 启动定时心跳超时检查（每 30s）
        self.add_scheduled_task("_check_heartbeat_timeout", "30s")

        LOG.info("系统管理插件已加载")

    async def on_close(self) -> None:
        if self._heartbeat_monitor_task and not self._heartbeat_monitor_task.done():
            self._heartbeat_monitor_task.cancel()
            try:
                await self._heartbeat_monitor_task
            except asyncio.CancelledError:
                pass

        LOG.info("系统管理插件已关闭")

    # ------------------------------------------------------------------
    # 内置 ! 命令 — 权限与配置
    # ------------------------------------------------------------------

    @staticmethod
    def _is_group_context(event: object) -> bool:
        fn = getattr(event, "is_group_msg", None)
        if callable(fn):
            try:
                return bool(fn())
            except Exception:
                pass
        data = getattr(event, "data", None)
        if data is None:
            return False
        mt = getattr(data, "message_type", None)
        if mt is None:
            return False
        if isinstance(mt, str):
            return mt == "group"
        val = getattr(mt, "value", None)
        if isinstance(val, str):
            return val == "group"
        return str(mt) == "group"

    async def _reply(self, event: object, text: str) -> None:
        reply = getattr(event, "reply", None)
        if callable(reply):
            await reply(text)

    async def _ensure_builtin_cmd(
        self,
        event: object,
        feature: str,
        *,
        require_master: bool = True,
    ) -> bool:
        """检查总开关、细粒度开关、群聊限制、root。通过返回 True。

        ``require_master=False`` 用于 ``!builtin on``：总开关关闭时仍允许重新开启。
        """
        mgr = get_config_manager()
        if require_master and not mgr.plugin.enable_builtin_commands:
            await self._reply(event, _OFF)
            return False
        if not getattr(mgr.plugin.builtin_commands, feature, True):
            await self._reply(event, _OFF)
            return False
        if (
            self._is_group_context(event)
            and not mgr.plugin.builtin_commands_group_allowed
        ):
            await self._reply(event, _GROUP_DENY)
            return False
        if not isinstance(event, HasSender):
            return False
        root = str(mgr.root)
        if str(event.user_id) != root:
            await self._reply(event, _DENY)
            return False
        return True

    @staticmethod
    def _ncatbot_version() -> str:
        try:
            return importlib.metadata.version("ncatbot")
        except Exception:
            return "unknown"

    def _sysinfo_lines(self) -> list[str]:
        mgr = get_config_manager()
        names = ", ".join(sorted(self.list_plugins())) or "(无)"
        lines = [
            f"NcatBot: {self._ncatbot_version()}",
            f"Python: {sys.version.split()[0]} ({platform.system()})",
            f"debug: {self.debug} | hot_reload: {mgr.effective_hot_reload()}",
            f"已加载插件: {names}",
        ]
        return lines

    @registrar.on_command("!reload", priority=50)
    async def cmd_reload(self, event: object, name: str) -> None:
        if not await self._ensure_builtin_cmd(event, "reload"):
            return
        reserved = _builtin_reserved_names()
        if name in reserved:
            await self._reply(
                event,
                "内置插件不支持聊天命令热重载，仅支持 plugins 目录下已索引的外部插件。",
            )
            return
        ok = await self._plugin_loader.reload_plugin(name)
        if ok:
            await self._reply(event, f"已重载: {name}")
        else:
            await self._reply(event, f"重载失败（未索引、未加载或加载出错）: {name}")

    @registrar.on_command("!load", priority=50)
    async def cmd_load(self, event: object, name: str) -> None:
        if not await self._ensure_builtin_cmd(event, "load"):
            return
        plugin = await self._plugin_loader.load_plugin(name)
        if plugin is not None:
            await self._reply(event, f"已加载: {name}")
        else:
            await self._reply(event, f"加载失败（未索引、依赖或加载异常）: {name}")

    @registrar.on_command("!unload", priority=50)
    async def cmd_unload(self, event: object, name: str) -> None:
        if not await self._ensure_builtin_cmd(event, "unload"):
            return
        if name in _builtin_reserved_names():
            await self._reply(event, "禁止卸载内置插件。")
            return
        ok = await self._plugin_loader.unload_plugin(name)
        if ok:
            await self._reply(event, f"已卸载: {name}")
        else:
            await self._reply(event, f"卸载失败（未加载）: {name}")

    @registrar.on_command("!sysinfo", priority=50)
    async def cmd_sysinfo(self, event: object) -> None:
        if not await self._ensure_builtin_cmd(event, "sysinfo"):
            return
        text = "\n".join(self._sysinfo_lines())
        await self._reply(event, text)

    @registrar.on_command("!builtin", priority=50)
    async def cmd_builtin_toggle(self, event: object, sub: str) -> None:
        if not await self._ensure_builtin_cmd(
            event, "config_toggle", require_master=False
        ):
            return
        key = sub.strip().lower()
        if key not in ("on", "off"):
            await self._reply(event, "用法: !builtin on | !builtin off")
            return
        mgr = get_config_manager()
        enabled = key == "on"
        mgr.update_value("plugin.enable_builtin_commands", enabled)
        mgr.save()
        if enabled:
            await self._reply(event, "已开启内置管理命令（本消息起生效）。")
        else:
            await self._reply(event, "已关闭内置管理命令（本消息起生效，已写入配置）。")

    # ------------------------------------------------------------------
    # 功能 A: 插件配置管理
    # ------------------------------------------------------------------

    def get_plugin_config(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """获取指定插件的配置字典。"""
        plugin = self.get_plugin(plugin_name)
        if plugin is None:
            return None
        return getattr(plugin, "config", None)

    def set_plugin_config(self, plugin_name: str, key: str, value: Any) -> bool:
        """设置指定插件的配置项并持久化。"""
        plugin = self.get_plugin(plugin_name)
        if plugin is None:
            return False
        set_config = getattr(plugin, "set_config", None)
        if callable(set_config):
            set_config(key, value)
            return True
        config = getattr(plugin, "config", None)
        if isinstance(config, dict):
            config[key] = value
            return True
        return False

    def list_plugin_configs(self) -> Dict[str, Dict[str, Any]]:
        """列出所有已加载插件的配置。"""
        result = {}
        for name in self.list_plugins():
            plugin = self.get_plugin(name)
            if plugin is not None:
                result[name] = getattr(plugin, "config", {})
        return result

    # ------------------------------------------------------------------
    # 功能 B: 心跳超时检测
    # ------------------------------------------------------------------

    async def _heartbeat_monitor_loop(self) -> None:
        """监听心跳事件，更新最后心跳时间。"""
        try:
            async with self.events("meta_event.heartbeat") as stream:
                async for event in stream:
                    self._last_heartbeat_time = time_mod.time()
        except asyncio.CancelledError:
            pass

    async def _check_heartbeat_timeout(self) -> None:
        """定时任务：检查心跳是否超时。"""
        timeout = self.get_config("heartbeat_timeout", 60)
        elapsed = time_mod.time() - self._last_heartbeat_time

        if elapsed > timeout:
            LOG.warning(
                "心跳超时: 已 %.1f 秒未收到心跳 (阈值: %ds)",
                elapsed,
                timeout,
            )
            await self._emit_heartbeat_timeout(elapsed, timeout)

    async def _emit_heartbeat_timeout(self, elapsed: float, timeout: int) -> None:
        """发出心跳超时事件。"""
        from ncatbot.types.qq import HeartbeatTimeoutMetaEventData

        event_data = HeartbeatTimeoutMetaEventData(
            time=int(time_mod.time()),
            self_id="0",
            last_heartbeat_time=int(self._last_heartbeat_time),
            timeout_seconds=timeout,
        )
        await self._dispatcher.callback(event_data)
