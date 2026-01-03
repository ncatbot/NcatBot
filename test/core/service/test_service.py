"""
服务层单元测试

测试 BaseService 和 ServiceManager。
"""

import pytest

from ncatbot.core.service import BaseService, ServiceManager


# =============================================================================
# 测试服务实现
# =============================================================================


class DummyService(BaseService):
    """用于测试的虚拟服务"""

    name = "dummy"
    description = "测试服务"

    def __init__(self, **config):
        super().__init__(**config)
        self.load_count = 0
        self.close_count = 0

    async def on_load(self):
        self.load_count += 1

    async def on_close(self):
        self.close_count += 1


class AnotherService(BaseService):
    """另一个测试服务"""

    name = "another"
    description = "另一个测试服务"

    async def on_load(self):
        pass

    async def on_close(self):
        pass


# =============================================================================
# BaseService 测试
# =============================================================================


class TestBaseService:
    """测试 BaseService 基类"""

    def test_service_must_have_name(self):
        """测试服务必须定义 name 属性"""

        class NoNameService(BaseService):
            async def on_load(self):
                pass

            async def on_close(self):
                pass

        with pytest.raises(ValueError, match="必须定义 name 属性"):
            NoNameService()

    def test_service_initialization(self):
        """测试服务初始化"""
        service = DummyService(param1="value1")

        assert service.name == "dummy"
        assert service.config == {"param1": "value1"}
        assert not service.is_loaded

    @pytest.mark.asyncio
    async def test_service_load(self):
        """测试服务加载"""
        service = DummyService()

        await service._load()

        assert service.is_loaded
        assert service.load_count == 1

    @pytest.mark.asyncio
    async def test_service_load_idempotent(self):
        """测试服务重复加载不会执行多次"""
        service = DummyService()

        await service._load()
        await service._load()

        assert service.load_count == 1

    @pytest.mark.asyncio
    async def test_service_close(self):
        """测试服务关闭"""
        service = DummyService()

        await service._load()
        await service._close()

        assert not service.is_loaded
        assert service.close_count == 1


# =============================================================================
# ServiceManager 测试
# =============================================================================


class TestServiceManager:
    """测试 ServiceManager 服务管理器"""

    def test_manager_initialization(self):
        """测试管理器初始化"""
        manager = ServiceManager()

        assert len(manager.list_services()) == 0

    def test_register_service(self):
        """测试注册服务"""
        manager = ServiceManager()

        manager.register(DummyService, param="value")

        # 服务已注册但未加载
        assert not manager.has("dummy")

    @pytest.mark.asyncio
    async def test_load_service(self):
        """测试加载服务"""
        manager = ServiceManager()
        manager.register(DummyService)

        service = await manager.load("dummy")

        assert service.is_loaded
        assert "dummy" in manager.list_services()
        # 验证 ServiceManager 被注入
        assert service.service_manager is manager

    @pytest.mark.asyncio
    async def test_load_nonexistent_service(self):
        """测试加载未注册的服务"""
        manager = ServiceManager()

        with pytest.raises(KeyError):
            await manager.load("nonexistent")

    @pytest.mark.asyncio
    async def test_unload_service(self):
        """测试卸载服务"""
        manager = ServiceManager()
        manager.register(DummyService)

        await manager.load("dummy")
        await manager.unload("dummy")

        assert not manager.has("dummy")

    @pytest.mark.asyncio
    async def test_load_all(self):
        """测试加载所有服务"""
        manager = ServiceManager()
        manager.register(DummyService)
        manager.register(AnotherService)

        await manager.load_all()

        assert len(manager.list_services()) == 2

    @pytest.mark.asyncio
    async def test_close_all(self):
        """测试关闭所有服务"""
        manager = ServiceManager()
        manager.register(DummyService)
        manager.register(AnotherService)

        await manager.load_all()
        await manager.close_all()

        assert len(manager.list_services()) == 0

    def test_get_service(self):
        """测试获取服务"""
        manager = ServiceManager()

        assert manager.get("dummy") is None

    def test_has_service(self):
        """测试检查服务是否存在"""
        manager = ServiceManager()

        assert not manager.has("dummy")


# =============================================================================
# 集成测试
# =============================================================================


class TestServiceIntegration:
    """测试服务层集成功能"""

    @pytest.mark.asyncio
    async def test_full_service_lifecycle(self):
        """测试完整的服务生命周期"""
        manager = ServiceManager()

        # 注册服务
        manager.register(DummyService, param="value")

        # 加载所有服务
        await manager.load_all()

        # 使用服务
        dummy = manager.get("dummy")

        assert dummy.is_loaded

        # 关闭所有服务
        await manager.close_all()

        assert not dummy.is_loaded
