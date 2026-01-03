"""
服务层集成测试

测试 ServiceManager 管理多个服务的生命周期和协同工作。
"""

import pytest
import asyncio
from typing import List, Optional

from ncatbot.core.service import ServiceManager, BaseService


# =============================================================================
# 测试用服务
# =============================================================================


class ServiceA(BaseService):
    """测试服务 A"""

    name = "service_a"
    description = "Test service A"

    def __init__(self, **config):
        super().__init__(**config)
        self.load_order: List[str] = config.get("load_order", [])
        self.close_order: List[str] = config.get("close_order", [])
        self.initialized = False

    async def on_load(self) -> None:
        self.load_order.append(self.name)
        self.initialized = True

    async def on_close(self) -> None:
        self.close_order.append(self.name)
        self.initialized = False


class ServiceB(BaseService):
    """测试服务 B - 依赖 A"""

    name = "service_b"
    description = "Test service B"

    def __init__(self, **config):
        super().__init__(**config)
        self.load_order: List[str] = config.get("load_order", [])
        self.close_order: List[str] = config.get("close_order", [])
        self.service_a_ref: Optional[ServiceA] = None

    async def on_load(self) -> None:
        self.load_order.append(self.name)
        # 通过 service_manager 获取 ServiceA
        if self.service_manager:
            self.service_a_ref = self.service_manager._services.get("service_a")

    async def on_close(self) -> None:
        self.close_order.append(self.name)


class ServiceC(BaseService):
    """测试服务 C"""

    name = "service_c"
    description = "Test service C"

    def __init__(self, **config):
        super().__init__(**config)
        self.load_order: List[str] = config.get("load_order", [])
        self.close_order: List[str] = config.get("close_order", [])

    async def on_load(self) -> None:
        self.load_order.append(self.name)

    async def on_close(self) -> None:
        self.close_order.append(self.name)


class FailingService(BaseService):
    """会失败的服务"""

    name = "failing_service"
    description = "Service that fails on load"

    async def on_load(self) -> None:
        raise RuntimeError("Service load failed")

    async def on_close(self) -> None:
        pass


class SlowService(BaseService):
    """加载缓慢的服务"""

    name = "slow_service"
    description = "Slow loading service"

    def __init__(self, delay: float = 0.1, **config):
        super().__init__(**config)
        self.delay = delay
        self.load_time: Optional[float] = None

    async def on_load(self) -> None:
        import time

        start = time.time()
        await asyncio.sleep(self.delay)
        self.load_time = time.time() - start

    async def on_close(self) -> None:
        pass


# =============================================================================
# 服务生命周期测试
# =============================================================================


class TestServiceLifecycle:
    """服务生命周期测试"""

    @pytest.mark.asyncio
    async def test_single_service_load_and_close(self):
        """测试单个服务的加载和关闭"""
        manager = ServiceManager()
        load_order = []
        close_order = []

        manager.register(ServiceA, load_order=load_order, close_order=close_order)

        # 加载
        service = await manager.load("service_a")

        assert service.is_loaded
        assert service.initialized
        assert load_order == ["service_a"]

        # 关闭
        await manager.unload("service_a")

        assert close_order == ["service_a"]

    @pytest.mark.asyncio
    async def test_multiple_services_load_all(self):
        """测试批量加载多个服务"""
        manager = ServiceManager()
        load_order = []

        manager.register(ServiceA, load_order=load_order, close_order=[])
        manager.register(ServiceB, load_order=load_order, close_order=[])
        manager.register(ServiceC, load_order=load_order, close_order=[])

        await manager.load_all()

        # 所有服务都应该被加载
        assert manager._services.get("service_a").is_loaded
        assert manager._services.get("service_b").is_loaded
        assert manager._services.get("service_c").is_loaded
        assert len(load_order) == 3

    @pytest.mark.asyncio
    async def test_close_all_services(self):
        """测试批量关闭所有服务"""
        manager = ServiceManager()
        close_order = []

        manager.register(ServiceA, load_order=[], close_order=close_order)
        manager.register(ServiceB, load_order=[], close_order=close_order)

        await manager.load_all()
        await manager.close_all()

        assert len(close_order) == 2
        assert "service_a" not in manager._services
        assert "service_b" not in manager._services

    @pytest.mark.asyncio
    async def test_service_idempotent_load(self):
        """测试服务重复加载是幂等的"""
        manager = ServiceManager()
        load_order = []

        manager.register(ServiceA, load_order=load_order, close_order=[])

        # 加载两次
        await manager.load("service_a")
        await manager.load("service_a")

        # 只应该加载一次
        assert load_order == ["service_a"]


# =============================================================================
# 服务间依赖测试
# =============================================================================


class TestServiceDependencies:
    """服务间依赖测试"""

    @pytest.mark.asyncio
    async def test_service_can_access_other_service(self):
        """测试服务可以访问其他服务"""
        manager = ServiceManager()
        load_order = []

        manager.register(ServiceA, load_order=load_order, close_order=[])
        manager.register(ServiceB, load_order=load_order, close_order=[])

        # 先加载 A
        await manager.load("service_a")
        # 再加载 B
        service_b = await manager.load("service_b")

        # B 应该能获取到 A 的引用
        assert service_b.service_a_ref is not None
        assert service_b.service_a_ref.name == "service_a"

    @pytest.mark.asyncio
    async def test_service_manager_injected(self):
        """测试 ServiceManager 被注入到服务"""
        manager = ServiceManager()

        manager.register(ServiceA, load_order=[], close_order=[])

        service = await manager.load("service_a")

        assert service.service_manager is manager


# =============================================================================
# 服务异常处理测试
# =============================================================================


class TestServiceExceptionHandling:
    """服务异常处理测试"""

    @pytest.mark.asyncio
    async def test_failing_service_raises_exception(self):
        """测试服务加载失败抛出异常"""
        manager = ServiceManager()
        manager.register(FailingService)

        with pytest.raises(RuntimeError, match="Service load failed"):
            await manager.load("failing_service")

    @pytest.mark.asyncio
    async def test_unload_non_existent_service(self):
        """测试卸载不存在的服务"""
        manager = ServiceManager()

        # 不应该抛出异常
        await manager.unload("non_existent")

    @pytest.mark.asyncio
    async def test_load_unregistered_service(self):
        """测试加载未注册的服务"""
        manager = ServiceManager()

        with pytest.raises(KeyError, match="未注册"):
            await manager.load("unregistered_service")


# =============================================================================
# 服务配置测试
# =============================================================================
