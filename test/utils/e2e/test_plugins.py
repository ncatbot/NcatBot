"""
测试用插件定义

这些插件用于测试端到端测试套件的功能。
"""

from typing import List, Dict, Any

from ncatbot.plugin_system import (
    NcatBotPlugin,
    command_registry,
    filter,
    on_notice,
    on_request,
    GroupFilter,
    PrivateFilter,
)
from ncatbot.core import GroupMessageEvent, PrivateMessageEvent


class SimpleReplyPlugin(NcatBotPlugin):
    """简单回复插件 - 测试 reply 功能"""
    name = "simple_reply_plugin"
    version = "1.0.0"
    
    handled_commands: List[str] = []
    
    async def on_load(self):
        SimpleReplyPlugin.handled_commands = []
        
        @command_registry.command("ping", description="ping 命令")
        async def ping_handler(event: GroupMessageEvent):
            SimpleReplyPlugin.handled_commands.append("ping")
            await event.reply("pong")
        
        @command_registry.command("echo", description="回显命令")
        async def echo_handler(event: GroupMessageEvent, text: str = ""):
            SimpleReplyPlugin.handled_commands.append(f"echo:{text}")
            await event.reply(f"Echo: {text}")
        
        @command_registry.command("greet", description="问候命令")
        async def greet_handler(event: GroupMessageEvent, name: str = "World"):
            SimpleReplyPlugin.handled_commands.append(f"greet:{name}")
            await event.reply(f"Hello, {name}!")


class FilteredReplyPlugin(NcatBotPlugin):
    """过滤器回复插件 - 测试过滤器与 reply 功能"""
    name = "filtered_reply_plugin"
    version = "1.0.0"
    
    handled_events: List[str] = []
    
    async def on_load(self):
        FilteredReplyPlugin.handled_events = []
        
        @command_registry.command("group_ping", description="仅群聊命令")
        @filter(GroupFilter())
        async def group_ping_handler(event: GroupMessageEvent):
            FilteredReplyPlugin.handled_events.append("group_ping")
            await event.reply("Group pong!")
        
        @command_registry.command("private_ping", description="仅私聊命令")
        @filter(PrivateFilter())
        async def private_ping_handler(event: PrivateMessageEvent):
            FilteredReplyPlugin.handled_events.append("private_ping")
            await event.reply("Private pong!")


class NoReplyPlugin(NcatBotPlugin):
    """无回复插件 - 测试不发送回复的情况"""
    name = "no_reply_plugin"
    version = "1.0.0"
    
    handled_commands: List[str] = []
    
    async def on_load(self):
        NoReplyPlugin.handled_commands = []
        
        @command_registry.command("silent", description="静默命令")
        async def silent_handler(event: GroupMessageEvent):
            NoReplyPlugin.handled_commands.append("silent")
            # 不回复


class NoticeHandlerPlugin(NcatBotPlugin):
    """通知处理插件 - 测试 @on_notice 装饰器"""
    name = "notice_handler_plugin"
    version = "1.0.0"
    
    notices_received: List[Dict[str, Any]] = []
    
    async def on_load(self):
        NoticeHandlerPlugin.notices_received = []
        
        @on_notice
        async def handle_notice(event):
            NoticeHandlerPlugin.notices_received.append({
                "notice_type": str(event.notice_type),
                "user_id": str(event.user_id),
            })


class RequestHandlerPlugin(NcatBotPlugin):
    """请求处理插件 - 测试 @on_request 装饰器"""
    name = "request_handler_plugin"
    version = "1.0.0"
    
    requests_received: List[Dict[str, Any]] = []
    
    async def on_load(self):
        RequestHandlerPlugin.requests_received = []
        
        @on_request
        async def handle_request(event):
            RequestHandlerPlugin.requests_received.append({
                "request_type": str(event.request_type),
                "user_id": str(event.user_id),
            })


class LifecyclePlugin(NcatBotPlugin):
    """生命周期插件 - 测试 on_load/on_close"""
    name = "lifecycle_plugin"
    version = "1.0.0"
    
    lifecycle_events: List[str] = []
    
    async def on_load(self):
        LifecyclePlugin.lifecycle_events.append("loaded")
    
    async def on_close(self):
        LifecyclePlugin.lifecycle_events.append("closed")
