"""
CommandGroupHook 单元测试 — 核心功能
"""

import pytest
from unittest.mock import MagicMock

from ncatbot.core import CommandGroupHook, HookAction
from ncatbot.core.registry.hook import HookContext
from ncatbot.core.registry.dispatcher import HandlerEntry
from ncatbot.core.dispatcher.event import Event
from ncatbot.testing import factory


def _make_ctx(text: str, handler_func):
    """构造 HookContext（使用真实 MessageArray）"""
    data = factory.group_message(text, group_id="100200")
    event = Event(type="message.group", data=data)
    entry = HandlerEntry(func=handler_func, event_type="message")
    return HookContext(
        event=event,
        event_type="message.group",
        handler_entry=entry,
        api=None,
    )


@pytest.fixture
def mock_context():
    """构造 mock context 的辅助工厂"""
    return _make_ctx


# ---- 命令匹配 ----


@pytest.mark.asyncio
async def test_command_matching(mock_context):
    """测试命令匹配（精确、别名、前缀）"""
    hook = CommandGroupHook("admin", "/admin", "a")

    async def handler(event):
        pass

    # 精确匹配命令名
    ctx = mock_context("admin", handler)
    assert await hook.execute(ctx) == HookAction.CONTINUE

    # 别名匹配
    ctx = mock_context("/admin", handler)
    assert await hook.execute(ctx) == HookAction.CONTINUE

    # 短别名
    ctx = mock_context("a", handler)
    assert await hook.execute(ctx) == HookAction.CONTINUE

    # 不匹配
    ctx = mock_context("unknown", handler)
    assert await hook.execute(ctx) == HookAction.SKIP


@pytest.mark.asyncio
async def test_case_sensitivity(mock_context):
    """测试大小写敏感性"""
    # 默认区分大小写
    hook = CommandGroupHook("admin")

    async def handler(event):
        pass

    ctx = mock_context("ADMIN", handler)
    assert await hook.execute(ctx) == HookAction.SKIP

    # 忽略大小写
    hook = CommandGroupHook("admin", ignore_case=True)
    ctx = mock_context("ADMIN", handler)
    assert await hook.execute(ctx) == HookAction.CONTINUE


# ---- 子命令参数绑定 ----


@pytest.mark.asyncio
async def test_subcommand_and_parameters(mock_context):
    """测试子命令路由与参数绑定"""
    hook = CommandGroupHook("admin")

    async def handler(event):
        pass

    # 子命令注册
    @hook.subcommand("ban", "禁言")
    async def admin_ban(event, user_id: int, minutes: int = 60):
        pass

    @hook.subcommand("kick")
    async def admin_kick(event, user_id: int):
        pass

    # 匹配 ban 子命令（主别名）
    ctx = mock_context("admin ban 12345", handler)
    result = await hook.execute(ctx)
    assert result == HookAction.CONTINUE
    assert ctx.kwargs.get("user_id") == 12345
    assert ctx.kwargs.get("minutes") == 60  # 默认值

    # 匹配 ban 子命令（别名）
    ctx = mock_context("admin 禁言 100 120", handler)
    result = await hook.execute(ctx)
    assert result == HookAction.CONTINUE
    assert ctx.kwargs.get("user_id") == 100
    assert ctx.kwargs.get("minutes") == 120

    # 匹配 kick 子命令
    ctx = mock_context("admin kick 200", handler)
    result = await hook.execute(ctx)
    assert result == HookAction.CONTINUE
    assert ctx.kwargs.get("user_id") == 200


@pytest.mark.asyncio
async def test_parameter_types(mock_context):
    """测试多种参数类型绑定"""
    hook = CommandGroupHook("calc")

    async def handler(event):
        pass

    @hook.subcommand("math")
    async def calc_math(event, a: int, b: float, text: str):
        pass

    # int + float + str (str 获取剩余文本)
    ctx = mock_context("calc math 10 3.14 hello world", handler)
    result = await hook.execute(ctx)
    assert result == HookAction.CONTINUE
    assert ctx.kwargs.get("a") == 10
    assert ctx.kwargs.get("b") == 3.14
    assert ctx.kwargs.get("text") == "hello world"


# ---- 异常情况 ----


@pytest.mark.asyncio
async def test_error_cases(mock_context):
    """测试异常情况（空消息、缺失字段等）"""
    hook = CommandGroupHook("admin")

    async def handler(event):
        pass

    # 空消息
    ctx = mock_context("", handler)
    assert await hook.execute(ctx) == HookAction.SKIP

    # 缺少 message 字段
    event = MagicMock()
    event.data = MagicMock()
    event.data.message = None
    entry = MagicMock()
    entry.func = handler
    ctx = HookContext(
        event=event, event_type="message.group", handler_entry=entry, api=MagicMock()
    )
    assert await hook.execute(ctx) == HookAction.SKIP
