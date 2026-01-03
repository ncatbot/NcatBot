"""
系统管理插件

提供 NcatBot 核心功能：
- 消息事件路由
- 命令/过滤器分发
- 插件热重载（通过 FileWatcherService）
- 系统状态查询
- 权限管理
"""

import asyncio
from typing import Optional, TYPE_CHECKING

import psutil

import ncatbot
from ncatbot.core import (
    MessageEvent,
    NcatBotEvent,
    GroupMessageEvent,
    PrivateMessageEvent,
)
from ncatbot.core.service.builtin.unified_registry import (
    command_registry,
    root_filter,
    option_group,
    admin_filter,
)
from ncatbot.utils import get_log, PermissionGroup

from ..builtin_mixin import NcatBotPlugin

if TYPE_CHECKING:
    from ncatbot.core.service.builtin import FileWatcherService

LOG = get_log("SystemManager")


class SystemManager(NcatBotPlugin):
    """系统管理插件"""

    version = "4.1.0"
    name = "system_manager"
    author = "huan-yp"
    description = "ncatbot 系统管理插件"

    # ------------------------------------------------------------------
    # 生命周期
    # ------------------------------------------------------------------

    async def on_load(self) -> None:
        """插件加载"""
        # 消息事件兼容层
        self.register_handler("ncatbot.message_event", self._handle_message_event)

        # 订阅消息事件以触发命令和过滤器处理
        self.event_bus.subscribe(
            "re:ncatbot.message_event|ncatbot.message_sent_event",
            self._handle_unified_registry_message,
            timeout=900,
        )
        self.event_bus.subscribe(
            "re:ncatbot.notice_event|ncatbot.request_event",
            self._handle_unified_registry_legacy,
            timeout=900,
        )

        # 设置文件监视服务的回调
        file_watcher: "FileWatcherService" = self.services.file_watcher
        if file_watcher:
            file_watcher.set_reload_callback(self._on_plugin_reload_requested)
            LOG.info("已注册插件热重载回调")

    async def on_unload(self) -> None:
        """插件卸载"""
        # FileWatcherService 会在服务关闭时自动停止
        pass

    # ------------------------------------------------------------------
    # 热重载回调
    # ------------------------------------------------------------------

    async def _on_plugin_reload_requested(self, plugin_folder: str) -> bool:
        """
        插件热重载回调

        由 FileWatcherService 在检测到文件变化时调用。

        Args:
            plugin_folder: 发生变化的插件文件夹名

        Returns:
            是否成功处理
        """
        plugin_name = self._loader.get_plugin_name_by_folder_name(plugin_folder)
        if plugin_name is None:
            LOG.warning(f"无法找到插件目录 {plugin_folder} 对应的插件名称")
            return False

        try:
            # 卸载插件
            await self._loader.unload_plugin(plugin_name)
            LOG.info(f"已卸载插件: {plugin_name}")

            # 短暂延迟后重新加载
            await asyncio.sleep(0.02)

            # 加载插件
            await self._loader.load_plugin(plugin_name)
            LOG.info(f"已加载插件: {plugin_name}")
            return True
        except Exception as e:
            LOG.error(f"热重载插件 {plugin_name} 失败: {e}")
            return False

    # ------------------------------------------------------------------
    # 消息事件处理
    # ------------------------------------------------------------------

    async def _handle_message_event(self, event: NcatBotEvent) -> None:
        """处理消息事件（兼容层，未来删除）"""
        message_event = event.data
        if isinstance(message_event, PrivateMessageEvent):
            await self.publish("ncatbot.private_message_event", message_event)
        elif isinstance(message_event, GroupMessageEvent):
            await self.publish("ncatbot.group_message_event", message_event)

    async def _handle_unified_registry_message(self, event: NcatBotEvent) -> None:
        """处理消息事件（命令和过滤器）"""
        await self.services.unified_registry.handle_message_event(event.data)

    async def _handle_unified_registry_legacy(self, event: NcatBotEvent) -> bool:
        """处理通知和请求事件"""
        return await self.services.unified_registry.handle_legacy_event(event.data)

    # ------------------------------------------------------------------
    # 系统命令
    # ------------------------------------------------------------------

    @command_registry.command("ncatbot_status", aliases=["ncs"])
    @root_filter
    async def get_status(self, event: MessageEvent) -> None:
        """查看 NcatBot 状态"""
        text = "ncatbot 状态:\n"
        text += f"插件数量: {len(self._loader.plugins)}\n"
        text += (
            f"插件列表: {', '.join([p.name for p in self._loader.plugins.values()])}\n"
        )
        text += f"CPU 使用率: {psutil.cpu_percent()}%\n"
        text += f"内存使用率: {psutil.virtual_memory().percent}%\n"
        text += f"NcatBot 版本: {ncatbot.__version__}\n"
        text += "Star NcatBot Meow~: https://github.com/liyihao1110/ncatbot\n"
        await event.reply(text)

    @command_registry.command("ncatbot_help", aliases=["nch"])
    @root_filter
    async def get_help(self, event: MessageEvent) -> None:
        """查看 NcatBot 帮助"""
        text = "ncatbot 帮助:\n"
        text += "/ncs 查看ncatbot状态\n"
        text += "/nch 查看ncatbot帮助\n"
        text += "开发中... 敬请期待\n"
        await event.reply(text)

    @command_registry.command("set_admin", aliases=["sa"])
    @option_group(
        choices=["add", "remove"], name="set", default="add", help="设置管理员"
    )
    @root_filter
    async def set_admin(
        self, event: MessageEvent, user_id: str, set: str = "add"
    ) -> None:
        """设置/移除管理员"""
        if user_id.startswith("At"):
            user_id = user_id.split("=")[1].split('"')[1]

        if set == "add":
            self.rbac.assign_role("user", user_id, PermissionGroup.ADMIN.value)
            await event.reply(f"添加管理员 {user_id}", at=False)
        elif set == "remove":
            self.rbac.unassign_role("user", user_id, PermissionGroup.ADMIN.value)
            await event.reply(f"删除管理员 {user_id}", at=False)

    @command_registry.command("set_config", aliases=["cfg"])
    @admin_filter
    async def set_config(
        self, event: MessageEvent, plugin_name: str, config_name: str, value: str
    ) -> None:
        """设置插件配置"""
        plugin: Optional["NcatBotPlugin"] = self.get_plugin(plugin_name)
        if not plugin:
            await event.reply(f"未找到插件 {plugin_name}")
            return
        try:
            _, newvalue = plugin.set_config(config_name, value)
            await event.reply(
                f"插件 {plugin_name} 配置 {config_name} 更新为 {newvalue}"
            )
        except Exception as e:
            await event.reply(f"插件 {plugin_name} 配置 {config_name} 更新失败: {e}")
