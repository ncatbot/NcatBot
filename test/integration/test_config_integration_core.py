"""
插件配置服务核心集成测试

测试 PluginConfigService 与其他核心组件的集成：
- 与 ServiceManager 的集成
- 与 PluginLoader 的集成
- 精细化保存集成
"""

import pytest
import asyncio
import tempfile
import os
from unittest.mock import patch
import yaml

from ncatbot.core.service import ServiceManager
from ncatbot.core.service.builtin.plugin_config import PluginConfigService
from ncatbot.core.client.event_bus import EventBus


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def temp_config_file():
    """创建临时配置文件"""
    fd, path = tempfile.mkstemp(suffix=".yaml")
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def temp_plugin_dir():
    """创建临时插件目录"""
    import tempfile
    import shutil

    dirpath = tempfile.mkdtemp()
    yield dirpath
    shutil.rmtree(dirpath, ignore_errors=True)


@pytest.fixture
async def service_manager_with_config(temp_config_file):
    """创建带有配置服务的 ServiceManager"""
    manager = ServiceManager()

    # 注册配置服务
    with patch(
        "ncatbot.core.service.builtin.plugin_config.service.CONFIG_PATH",
        temp_config_file,
    ):
        manager.register(PluginConfigService)
        await manager.load("plugin_config")

    yield manager

    await manager.close_all()


# =============================================================================
# ServiceManager 集成测试
# =============================================================================


class TestServiceManagerIntegration:
    """ServiceManager 集成测试"""

    @pytest.mark.asyncio
    async def test_register_and_load_plugin_config_service(self, temp_config_file):
        """测试注册和加载插件配置服务"""
        manager = ServiceManager()

        with patch(
            "ncatbot.core.service.builtin.plugin_config.service.CONFIG_PATH",
            temp_config_file,
        ):
            manager.register(PluginConfigService)
            await manager.load("plugin_config")

            # 通过属性访问
            assert manager.plugin_config is not None
            assert isinstance(manager.plugin_config, PluginConfigService)

            await manager.close_all()

    @pytest.mark.asyncio
    async def test_service_manager_access_pattern(self, temp_config_file):
        """测试 ServiceManager 访问模式"""
        manager = ServiceManager()

        with patch(
            "ncatbot.core.service.builtin.plugin_config.service.CONFIG_PATH",
            temp_config_file,
        ):
            manager.register(PluginConfigService)
            await manager.load("plugin_config")

            config_service = manager.plugin_config

            # 注册配置
            config_service.register_config(
                "test_plugin",
                "api_key",
                default_value="default",
            )

            assert config_service.get("test_plugin", "api_key") == "default"

            await manager.close_all()

    @pytest.mark.asyncio
    async def test_multiple_plugins_share_service(self, temp_config_file):
        """测试多个插件共享服务"""
        manager = ServiceManager()

        with patch(
            "ncatbot.core.service.builtin.plugin_config.service.CONFIG_PATH",
            temp_config_file,
        ):
            manager.register(PluginConfigService)
            await manager.load("plugin_config")

            config_service = manager.plugin_config

            # 模拟多个插件
            config_service.set("plugin_a", "key", "value_a")
            config_service.set("plugin_b", "key", "value_b")

            assert config_service.get("plugin_a", "key") == "value_a"
            assert config_service.get("plugin_b", "key") == "value_b"

            await manager.close_all()


# =============================================================================
# PluginLoader 集成测试
# =============================================================================


class TestPluginLoaderIntegration:
    """PluginLoader 集成测试"""

    @pytest.mark.asyncio
    async def test_plugin_loader_receives_service_manager(
        self, temp_config_file, temp_plugin_dir
    ):
        """测试 PluginLoader 接收 ServiceManager 注入"""
        from ncatbot.plugin_system.loader import PluginLoader

        manager = ServiceManager()
        event_bus = EventBus()

        with patch(
            "ncatbot.core.service.builtin.plugin_config.service.CONFIG_PATH",
            temp_config_file,
        ):
            manager.register(PluginConfigService)
            await manager.load("plugin_config")

            # 创建 PluginLoader 并注入 ServiceManager
            loader = PluginLoader(event_bus, manager, debug=True)

            # 验证 ServiceManager 已注入
            assert loader._service_manager is manager
            assert loader._service_manager.plugin_config is not None

            await manager.close_all()

    @pytest.mark.asyncio
    async def test_plugin_can_access_config_service(self, temp_config_file):
        """测试插件可以访问配置服务"""
        from ncatbot.core.service import ServiceManager

        manager = ServiceManager()

        with patch(
            "ncatbot.core.service.builtin.plugin_config.service.CONFIG_PATH",
            temp_config_file,
        ):
            manager.register(PluginConfigService)
            await manager.load("plugin_config")

            # 模拟插件访问服务
            config_service = manager.plugin_config

            # 注册配置
            config_service.register_config(
                "test_plugin",
                "api_key",
                default_value="",
                description="API Key",
            )

            # 获取配置包装器
            wrapper = config_service.get_plugin_config_wrapper("test_plugin")

            assert wrapper["api_key"] == ""

            # 更新配置
            wrapper.update("api_key", "new_key")

            assert wrapper["api_key"] == "new_key"

            await manager.close_all()


# =============================================================================
# 精细化保存集成测试
# =============================================================================


class TestFinegrainedPersistence:
    """精细化保存集成测试"""

    @pytest.mark.asyncio
    async def test_single_item_save_preserves_other_config(self, temp_config_file):
        """测试单项保存保留其他配置"""
        # 预先写入一些配置
        initial_data = {
            "other_section": {"key": "value"},
            "plugin_config": {
                "plugin_a": {"key1": "val1", "key2": "val2"},
                "plugin_b": {"key3": "val3"},
            },
        }
        with open(temp_config_file, "w") as f:
            yaml.dump(initial_data, f)

        manager = ServiceManager()

        with patch(
            "ncatbot.core.service.builtin.plugin_config.service.CONFIG_PATH",
            temp_config_file,
        ):
            manager.register(PluginConfigService)
            await manager.load("plugin_config")

            config_service = manager.plugin_config

            # 只修改一个配置项
            config_service.set_atomic("plugin_a", "key1", "new_val1")

            await manager.close_all()

        # 验证文件
        with open(temp_config_file, "r") as f:
            data = yaml.safe_load(f)

        # 被修改的值
        assert data["plugin_config"]["plugin_a"]["key1"] == "new_val1"

        # 其他值保持不变
        assert data["plugin_config"]["plugin_a"]["key2"] == "val2"
        assert data["plugin_config"]["plugin_b"]["key3"] == "val3"
        assert data["other_section"]["key"] == "value"

    @pytest.mark.asyncio
    async def test_concurrent_config_updates(self, temp_config_file):
        """测试并发配置更新"""
        manager = ServiceManager()

        with patch(
            "ncatbot.core.service.builtin.plugin_config.service.CONFIG_PATH",
            temp_config_file,
        ):
            manager.register(PluginConfigService)
            await manager.load("plugin_config")

            config_service = manager.plugin_config

            # 并发更新多个配置
            async def update_config(plugin_name, key, value):
                config_service.set_atomic(plugin_name, key, value)
                await asyncio.sleep(0.01)  # 小延迟模拟实际操作

            await asyncio.gather(
                update_config("plugin_a", "key1", "val1"),
                update_config("plugin_a", "key2", "val2"),
                update_config("plugin_b", "key1", "valb1"),
            )

            # 验证所有配置都正确设置
            assert config_service.get("plugin_a", "key1") == "val1"
            assert config_service.get("plugin_a", "key2") == "val2"
            assert config_service.get("plugin_b", "key1") == "valb1"

            await manager.close_all()

    @pytest.mark.asyncio
    async def test_bulk_update_saves_all_items(self, temp_config_file):
        """测试批量更新保存所有项"""
        manager = ServiceManager()

        with patch(
            "ncatbot.core.service.builtin.plugin_config.service.CONFIG_PATH",
            temp_config_file,
        ):
            manager.register(PluginConfigService)
            await manager.load("plugin_config")

            config_service = manager.plugin_config
            wrapper = config_service.get_plugin_config_wrapper("plugin")

            wrapper.bulk_update(
                {
                    "key1": "val1",
                    "key2": "val2",
                    "key3": "val3",
                }
            )

            await manager.close_all()

        # 验证文件
        with open(temp_config_file, "r") as f:
            data = yaml.safe_load(f)

        assert data["plugin_config"]["plugin"]["key1"] == "val1"
        assert data["plugin_config"]["plugin"]["key2"] == "val2"
        assert data["plugin_config"]["plugin"]["key3"] == "val3"
