from __future__ import annotations

from typing import Any, cast
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ncatbot.app.client import BotClient


class _CompletedTask:
    def done(self) -> bool:
        return True

    def cancel(self) -> None:
        return None

    def __await__(self):
        if False:
            yield
        return None


@pytest.mark.asyncio
async def test_lifecycle_decorators_accept_call_syntax():
    """APP-04: on_startup()/on_close() 支持调用式装饰器注册"""
    bot = BotClient(adapters=[])
    events: list[str] = []

    @bot.on_startup()
    async def startup_async():
        events.append("startup-async")

    @bot.on_close()
    async def close_async():
        events.append("close-async")

    await bot._execute_lifecycle_callbacks(bot._startup_callbacks, "启动")
    await bot._execute_lifecycle_callbacks(bot._close_callbacks, "关闭")

    assert events == ["startup-async", "close-async"]


def test_lifecycle_decorators_reject_sync_callbacks():
    """APP-05: 生命周期装饰器拒绝同步回调"""
    bot = BotClient(adapters=[])

    with pytest.raises(TypeError, match="生命周期回调必须使用 async def 定义"):
        bot.on_startup()(cast(Any, lambda: None))

    with pytest.raises(TypeError, match="生命周期回调必须使用 async def 定义"):
        bot.on_close()(cast(Any, lambda: None))


@pytest.mark.asyncio
async def test_shutdown_stops_napcat_when_enabled_on_linux():
    """APP-01: Linux 下 stop_napcat=true 时 shutdown 会停止 NapCat"""
    adapter = MagicMock()
    adapter.name = "napcat"
    adapter.disconnect = AsyncMock()
    adapter.napcat_config = SimpleNamespace(stop_napcat=True)
    adapter.stop_managed_runtime = MagicMock()

    bot = BotClient(adapters=[adapter])
    bot._running = True
    bot._listen_tasks = []
    bot._listen_task = cast(Any, _CompletedTask())
    bot._plugin_loader.stop_hot_reload = AsyncMock()
    bot._plugin_loader.unload_all = AsyncMock()
    bot._service_manager.close_all = AsyncMock()

    with patch("platform.system", return_value="Linux"):
        await bot.shutdown()

    adapter.disconnect.assert_awaited_once()
    adapter.stop_managed_runtime.assert_called_once()


@pytest.mark.asyncio
async def test_shutdown_executes_on_close_callbacks_registered_with_call_syntax():
    """APP-06: shutdown 会执行通过 on_close() 注册的回调"""
    adapter = MagicMock()
    adapter.name = "napcat"
    adapter.disconnect = AsyncMock()
    adapter.napcat_config = SimpleNamespace(stop_napcat=False)
    adapter.stop_managed_runtime = MagicMock()

    bot = BotClient(adapters=[adapter])
    bot._running = True
    bot._listen_tasks = []
    bot._listen_task = cast(Any, _CompletedTask())
    bot._plugin_loader.stop_hot_reload = AsyncMock()
    bot._plugin_loader.unload_all = AsyncMock()
    bot._service_manager.close_all = AsyncMock()

    events: list[tuple[str, bool]] = []

    @bot.on_close()
    async def close_async():
        events.append(("async", bot._running))

    with patch("platform.system", return_value="Linux"):
        await bot.shutdown()

    assert events == [("async", False)]
    adapter.disconnect.assert_awaited_once()


@pytest.mark.asyncio
async def test_shutdown_does_not_stop_napcat_when_disabled():
    """APP-02: stop_napcat=false 时 shutdown 不会停止 NapCat"""
    adapter = MagicMock()
    adapter.name = "napcat"
    adapter.disconnect = AsyncMock()
    adapter.napcat_config = SimpleNamespace(stop_napcat=False)
    adapter.stop_managed_runtime = MagicMock()

    bot = BotClient(adapters=[adapter])
    bot._running = True
    bot._listen_tasks = []
    bot._listen_task = cast(Any, _CompletedTask())
    bot._plugin_loader.stop_hot_reload = AsyncMock()
    bot._plugin_loader.unload_all = AsyncMock()
    bot._service_manager.close_all = AsyncMock()

    with patch("platform.system", return_value="Linux"):
        await bot.shutdown()

    adapter.disconnect.assert_awaited_once()
    adapter.stop_managed_runtime.assert_not_called()


@pytest.mark.asyncio
async def test_shutdown_does_not_stop_napcat_on_non_linux():
    """APP-03: 非 Linux 平台即使 stop_napcat=true 也不执行停止"""
    adapter = MagicMock()
    adapter.name = "napcat"
    adapter.disconnect = AsyncMock()
    adapter.napcat_config = SimpleNamespace(stop_napcat=True)
    adapter.stop_managed_runtime = MagicMock()

    bot = BotClient(adapters=[adapter])
    bot._running = True
    bot._listen_tasks = []
    bot._listen_task = cast(Any, _CompletedTask())
    bot._plugin_loader.stop_hot_reload = AsyncMock()
    bot._plugin_loader.unload_all = AsyncMock()
    bot._service_manager.close_all = AsyncMock()

    with patch("platform.system", return_value="Windows"):
        await bot.shutdown()

    adapter.disconnect.assert_awaited_once()
    adapter.stop_managed_runtime.assert_not_called()
