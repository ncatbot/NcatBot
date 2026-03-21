"""
平台子注册器 — 为 QQ / Bilibili / GitHub 提供平台专属的便捷装饰器

使用方式::

    from ncatbot.core import registrar

    @registrar.qq.on_poke()
    async def handle_poke(self, event): ...

    @registrar.bilibili.on_danmu()
    async def handle_danmu(self, event): ...

    @registrar.github.on_push()
    async def handle_push(self, event): ...
"""

from __future__ import annotations

from typing import Any, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from .registrar import Registrar

from .builtin_hooks import MessageTypeFilter
from .command_hook import CommandHook

__all__ = [
    "PlatformRegistrar",
    "QQRegistrar",
    "BilibiliRegistrar",
    "GitHubRegistrar",
]


class PlatformRegistrar:
    """平台子注册器基类

    持有对主 Registrar 的引用，所有装饰器自动注入 ``platform`` 过滤。
    """

    _platform: str = ""

    def __init__(self, parent: "Registrar"):
        self._parent = parent

    def on(self, event_type: str, priority: int = 0, **metadata: Any) -> Callable:
        """注册 handler（自动附带平台过滤）"""
        return self._parent.on(
            event_type, priority=priority, platform=self._platform, **metadata
        )

    # ---- 通用消息装饰器 ----

    def on_message(self, priority: int = 0, **metadata: Any) -> Callable:
        """注册该平台的所有消息 handler"""
        return self.on("message", priority=priority, **metadata)

    def on_group_message(self, priority: int = 0, **metadata: Any) -> Callable:
        """注册该平台的群消息 handler"""

        def decorator(func: Callable) -> Callable:
            if not hasattr(func, "__hooks__"):
                func.__hooks__ = []
            func.__hooks__.append(MessageTypeFilter("group"))
            return self.on("message", priority=priority, **metadata)(func)

        return decorator

    def on_private_message(self, priority: int = 0, **metadata: Any) -> Callable:
        """注册该平台的私聊消息 handler"""

        def decorator(func: Callable) -> Callable:
            if not hasattr(func, "__hooks__"):
                func.__hooks__ = []
            func.__hooks__.append(MessageTypeFilter("private"))
            return self.on("message", priority=priority, **metadata)(func)

        return decorator

    # ---- 通用命令装饰器 ----

    def on_command(
        self, *names: str, priority: int = 0, ignore_case: bool = False, **metadata: Any
    ) -> Callable:
        """注册该平台的命令 handler"""

        def decorator(func: Callable) -> Callable:
            if not hasattr(func, "__hooks__"):
                func.__hooks__ = []
            func.__hooks__.append(CommandHook(*names, ignore_case=ignore_case))
            return self.on("message", priority=priority, **metadata)(func)

        return decorator

    def on_group_command(
        self, *names: str, priority: int = 0, ignore_case: bool = False, **metadata: Any
    ) -> Callable:
        """注册该平台的群命令 handler"""

        def decorator(func: Callable) -> Callable:
            if not hasattr(func, "__hooks__"):
                func.__hooks__ = []
            func.__hooks__.append(MessageTypeFilter("group"))
            func.__hooks__.append(CommandHook(*names, ignore_case=ignore_case))
            return self.on("message", priority=priority, **metadata)(func)

        return decorator

    def on_private_command(
        self, *names: str, priority: int = 0, ignore_case: bool = False, **metadata: Any
    ) -> Callable:
        """注册该平台的私聊命令 handler"""

        def decorator(func: Callable) -> Callable:
            if not hasattr(func, "__hooks__"):
                func.__hooks__ = []
            func.__hooks__.append(MessageTypeFilter("private"))
            func.__hooks__.append(CommandHook(*names, ignore_case=ignore_case))
            return self.on("message", priority=priority, **metadata)(func)

        return decorator

    def on_notice(self, priority: int = 0, **metadata: Any) -> Callable:
        """注册该平台的通知事件 handler"""
        return self.on("notice", priority=priority, **metadata)

    def on_request(self, priority: int = 0, **metadata: Any) -> Callable:
        """注册该平台的请求事件 handler"""
        return self.on("request", priority=priority, **metadata)


class QQRegistrar(PlatformRegistrar):
    """QQ 平台子注册器

    提供 QQ 专属便捷装饰器::

        @registrar.qq.on_group_increase()
        async def welcome(self, event): ...

        @registrar.qq.on_poke()
        async def handle_poke(self, event): ...
    """

    _platform = "qq"

    # ---- 通知事件精确类型 ----

    def on_group_increase(self, priority: int = 0, **metadata: Any) -> Callable:
        """注册群成员增加事件 handler"""
        return self.on("notice.group_increase", priority=priority, **metadata)

    def on_group_decrease(self, priority: int = 0, **metadata: Any) -> Callable:
        """注册群成员减少事件 handler"""
        return self.on("notice.group_decrease", priority=priority, **metadata)

    def on_group_recall(self, priority: int = 0, **metadata: Any) -> Callable:
        """注册群消息撤回事件 handler"""
        return self.on("notice.group_recall", priority=priority, **metadata)

    def on_group_admin(self, priority: int = 0, **metadata: Any) -> Callable:
        """注册群管理员变动事件 handler"""
        return self.on("notice.group_admin", priority=priority, **metadata)

    def on_group_ban(self, priority: int = 0, **metadata: Any) -> Callable:
        """注册群禁言事件 handler"""
        return self.on("notice.group_ban", priority=priority, **metadata)

    def on_friend_add(self, priority: int = 0, **metadata: Any) -> Callable:
        """注册好友已添加通知 handler"""
        return self.on("notice.friend_add", priority=priority, **metadata)

    def on_poke(self, priority: int = 0, **metadata: Any) -> Callable:
        """注册戳一戳事件 handler"""
        return self.on("notice.poke", priority=priority, **metadata)

    # ---- 请求事件精确类型 ----

    def on_friend_request(self, priority: int = 0, **metadata: Any) -> Callable:
        """注册好友请求 handler"""
        return self.on("request.friend", priority=priority, **metadata)

    def on_group_request(self, priority: int = 0, **metadata: Any) -> Callable:
        """注册群请求 handler"""
        return self.on("request.group", priority=priority, **metadata)

    # ---- 元事件 ----

    def on_meta(self, priority: int = 0, **metadata: Any) -> Callable:
        """注册元事件 handler"""
        return self.on("meta_event", priority=priority, **metadata)

    def on_message_sent(self, priority: int = 0, **metadata: Any) -> Callable:
        """注册消息发送 handler"""
        return self.on("message_sent", priority=priority, **metadata)


class BilibiliRegistrar(PlatformRegistrar):
    """Bilibili 平台子注册器

    提供 Bilibili 专属便捷装饰器::

        @registrar.bilibili.on_danmu()
        async def handle_danmu(self, event): ...

        @registrar.bilibili.on_gift()
        async def handle_gift(self, event): ...
    """

    _platform = "bilibili"

    # ---- 直播间事件 ----

    def on_live(self, priority: int = 0, **metadata: Any) -> Callable:
        """注册所有直播间事件 handler（弹幕、礼物、SC 等）"""
        return self.on("live", priority=priority, **metadata)

    def on_danmu(self, priority: int = 0, **metadata: Any) -> Callable:
        """注册弹幕消息 handler"""
        return self.on("live.danmu_msg", priority=priority, **metadata)

    def on_superchat(self, priority: int = 0, **metadata: Any) -> Callable:
        """注册醒目留言 (SuperChat) handler"""
        return self.on("live.super_chat_message", priority=priority, **metadata)

    def on_gift(self, priority: int = 0, **metadata: Any) -> Callable:
        """注册礼物 handler"""
        return self.on("live.send_gift", priority=priority, **metadata)

    def on_guard_buy(self, priority: int = 0, **metadata: Any) -> Callable:
        """注册大航海 (舰长/提督/总督) handler"""
        return self.on("live.guard_buy", priority=priority, **metadata)

    def on_interact(self, priority: int = 0, **metadata: Any) -> Callable:
        """注册互动事件 handler（进入直播间/关注/分享）"""
        return self.on("live.interact_word_v2", priority=priority, **metadata)

    def on_like(self, priority: int = 0, **metadata: Any) -> Callable:
        """注册点赞事件 handler"""
        return self.on("live.like_info_v3_click", priority=priority, **metadata)

    def on_live_start(self, priority: int = 0, **metadata: Any) -> Callable:
        """注册开播事件 handler"""
        return self.on("live.live", priority=priority, **metadata)

    def on_live_end(self, priority: int = 0, **metadata: Any) -> Callable:
        """注册下播事件 handler"""
        return self.on("live.preparing", priority=priority, **metadata)

    # ---- 评论事件 ----

    def on_comment(self, priority: int = 0, **metadata: Any) -> Callable:
        """注册所有评论事件 handler"""
        return self.on("comment", priority=priority, **metadata)


class GitHubRegistrar(PlatformRegistrar):
    """GitHub 平台子注册器

    提供 GitHub 专属便捷装饰器::

        @registrar.github.on_push()
        async def handle_push(self, event): ...

        @registrar.github.on_issue()
        async def handle_issue(self, event): ...
    """

    _platform = "github"

    def on_push(self, priority: int = 0, **metadata: Any) -> Callable:
        """注册 push 事件 handler"""
        return self.on("push", priority=priority, **metadata)

    def on_issue(self, priority: int = 0, **metadata: Any) -> Callable:
        """注册 issue 事件 handler（所有 action）"""
        return self.on("issue", priority=priority, **metadata)

    def on_pr(self, priority: int = 0, **metadata: Any) -> Callable:
        """注册 pull request 事件 handler（所有 action）"""
        return self.on("pull_request", priority=priority, **metadata)

    def on_star(self, priority: int = 0, **metadata: Any) -> Callable:
        """注册 star 事件 handler"""
        return self.on("star", priority=priority, **metadata)

    def on_fork(self, priority: int = 0, **metadata: Any) -> Callable:
        """注册 fork 事件 handler"""
        return self.on("fork", priority=priority, **metadata)

    def on_release(self, priority: int = 0, **metadata: Any) -> Callable:
        """注册 release 事件 handler"""
        return self.on("release", priority=priority, **metadata)

    def on_comment(self, priority: int = 0, **metadata: Any) -> Callable:
        """注册 comment 事件 handler（issue comment + PR review comment）"""
        return self.on("comment", priority=priority, **metadata)
