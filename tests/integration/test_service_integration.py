"""
服务集成测试

规范:
  I-20: ServiceManager 多服务按依赖加载
  I-21: 服务关闭顺序
"""

import pytest

from ncatbot.service.base import BaseService
from ncatbot.service.manager import ServiceManager


class TrackedService(BaseService):
    """记录生命周期调用顺序的服务"""

    _load_order: list = []  # 类级别共享

    async def on_load(self):
        TrackedService._load_order.append(f"load:{self.name}")

    async def on_close(self):
        TrackedService._load_order.append(f"close:{self.name}")


class ServiceDB(TrackedService):
    name = "db"
    dependencies = []


class ServiceCache(TrackedService):
    name = "cache"
    dependencies = ["db"]


class ServiceApp(TrackedService):
    name = "app"
    dependencies = ["cache", "db"]


@pytest.fixture(autouse=True)
def clear_tracking():
    TrackedService._load_order = []
    yield
    TrackedService._load_order = []


# ---- I-20: 按依赖拓扑加载 ----


async def test_load_order():
    """I-20: db → cache → app 顺序加载"""
    mgr = ServiceManager()
    mgr.register(ServiceApp)
    mgr.register(ServiceCache)
    mgr.register(ServiceDB)

    await mgr.load_all()

    # db 必须在 cache 和 app 之前
    load_events = [e for e in TrackedService._load_order if e.startswith("load:")]
    db_idx = load_events.index("load:db")
    cache_idx = load_events.index("load:cache")
    app_idx = load_events.index("load:app")

    assert db_idx < cache_idx
    assert cache_idx < app_idx


# ---- I-21: 全部关闭 ----


async def test_close_all():
    """I-21: close_all 关闭所有服务"""
    mgr = ServiceManager()
    mgr.register(ServiceDB)
    mgr.register(ServiceCache)

    await mgr.load_all()
    await mgr.close_all()

    close_events = [e for e in TrackedService._load_order if e.startswith("close:")]
    assert len(close_events) == 2
    assert "close:db" in close_events
    assert "close:cache" in close_events

    assert not mgr.has("db")
    assert not mgr.has("cache")
