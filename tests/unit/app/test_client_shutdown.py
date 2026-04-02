from __future__ import annotations

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
    bot._listen_task = _CompletedTask()
    bot._plugin_loader.stop_hot_reload = AsyncMock()
    bot._plugin_loader.unload_all = AsyncMock()
    bot._service_manager.close_all = AsyncMock()

    with patch("platform.system", return_value="Linux"):
        await bot.shutdown()

    adapter.disconnect.assert_awaited_once()
    adapter.stop_managed_runtime.assert_called_once()


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
    bot._listen_task = _CompletedTask()
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
    bot._listen_task = _CompletedTask()
    bot._plugin_loader.stop_hot_reload = AsyncMock()
    bot._plugin_loader.unload_all = AsyncMock()
    bot._service_manager.close_all = AsyncMock()

    with patch("platform.system", return_value="Windows"):
        await bot.shutdown()

    adapter.disconnect.assert_awaited_once()
    adapter.stop_managed_runtime.assert_not_called()
