"""
TimeTaskService 规范测试

规范:
  TT-01: 同一时间点的不同插件定时任务不会互相阻塞
"""

import asyncio
import time

import pytest

from ncatbot.plugin.mixin.time_task_mixin import TimeTaskMixin
from ncatbot.service.builtin.schedule.parser import TimeTaskParser
from ncatbot.service.builtin.schedule.service import TimeTaskService
from ncatbot.service.manager import ServiceManager

pytestmark = pytest.mark.asyncio(loop_scope="function")


class SlowPlugin(TimeTaskMixin):
    def __init__(self, service_manager, started_at, ready_event):
        self.name = "slow_plugin"
        self.services = service_manager
        self._started_at = started_at
        self._ready_event = ready_event

    async def slow_tick(self):
        self._started_at["slow"] = time.monotonic()
        if len(self._started_at) == 2:
            self._ready_event.set()
        await asyncio.sleep(0.15)


class FastPlugin(TimeTaskMixin):
    def __init__(self, service_manager, started_at, ready_event):
        self.name = "fast_plugin"
        self.services = service_manager
        self._started_at = started_at
        self._ready_event = ready_event

    async def fast_tick(self):
        self._started_at["fast"] = time.monotonic()
        if len(self._started_at) == 2:
            self._ready_event.set()


async def test_tt01_same_slot_tasks_do_not_block_each_other(monkeypatch):
    """TT-01: 同一时间点的不同插件定时任务不会互相阻塞"""

    monkeypatch.setattr(
        TimeTaskParser,
        "parse",
        classmethod(lambda cls, _: {"type": "interval", "value": 0.05}),
    )

    service = TimeTaskService()
    manager = ServiceManager()
    manager._services["time_task"] = service

    started_at = {}
    ready_event = asyncio.Event()
    slow_plugin = SlowPlugin(manager, started_at, ready_event)
    fast_plugin = FastPlugin(manager, started_at, ready_event)

    await service.on_load()
    try:
        assert slow_plugin.add_scheduled_task("slow_tick", "1s") is True
        assert fast_plugin.add_scheduled_task("fast_tick", "1s") is True

        await asyncio.wait_for(ready_event.wait(), timeout=1.0)

        skew = max(started_at.values()) - min(started_at.values())
        assert skew < 0.08
    finally:
        await service.on_close()
