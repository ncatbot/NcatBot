"""
配置服务单元测试

测试 PluginConfigService 和 PluginConfig 的功能
"""

import pytest
import tempfile
import os
import asyncio
from pathlib import Path
from unittest.mock import patch
import yaml

from ncatbot.core.service.builtin.plugin_config import (
    PluginConfigService,
    PluginConfig,
    ConfigPersistence,
)


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
def config_service(temp_config_file):
    """创建配置服务实例"""
    with patch(
        "ncatbot.core.service.builtin.plugin_config.service.CONFIG_PATH",
        temp_config_file,
    ):
        service = PluginConfigService()
        service._config_path = Path(temp_config_file)
        service._persistence = ConfigPersistence(Path(temp_config_file))
        return service


# =============================================================================
# PluginConfigService 单元测试
# =============================================================================


class TestPluginConfigService:
    """插件配置服务测试"""

    @pytest.mark.asyncio
    async def test_service_load(self, config_service):
        """测试服务加载"""
        await config_service.on_load()
        assert config_service._configs == {}

    @pytest.mark.asyncio
    async def test_register_config(self, config_service):
        """测试注册配置"""
        await config_service.on_load()

        item = config_service.register_config(
            plugin_name="my_plugin",
            name="api_key",
            default_value="",
            description="API 密钥",
            value_type=str,
        )

        assert item.name == "api_key"
        assert "my_plugin" in config_service._config_items
        assert "api_key" in config_service._config_items["my_plugin"]

        # 默认值应该被设置
        assert config_service.get("my_plugin", "api_key") == ""

    @pytest.mark.asyncio
    async def test_register_duplicate_config_raises(self, config_service):
        """测试重复注册配置抛出异常"""
        await config_service.on_load()

        config_service.register_config("plugin", "key", "default")

        with pytest.raises(ValueError, match="已存在"):
            config_service.register_config("plugin", "key", "other")

    @pytest.mark.asyncio
    async def test_get_set_config(self, config_service):
        """测试获取和设置配置"""
        await config_service.on_load()

        # 设置配置
        old, new = config_service.set("my_plugin", "key", "value")

        assert old is None
        assert new == "value"
        assert config_service.get("my_plugin", "key") == "value"

    @pytest.mark.asyncio
    async def test_set_with_type_conversion(self, config_service):
        """测试设置配置时的类型转换"""
        await config_service.on_load()

        # 注册整数类型配置
        config_service.register_config("plugin", "count", 0, value_type=int)

        # 设置字符串值，应该被转换为整数
        config_service.set("plugin", "count", "42")

        assert config_service.get("plugin", "count") == 42

    @pytest.mark.asyncio
    async def test_set_with_on_change_callback(self, config_service):
        """测试设置配置时触发回调"""
        await config_service.on_load()

        callback_called = []

        def on_change(old, new):
            callback_called.append((old, new))

        config_service.register_config("plugin", "key", "default", on_change=on_change)

        config_service.set("plugin", "key", "new_value")

        assert len(callback_called) == 1
        assert callback_called[0] == ("default", "new_value")

    @pytest.mark.asyncio
    async def test_set_atomic_saves_immediately(self, config_service, temp_config_file):
        """测试原子设置立即保存"""
        await config_service.on_load()

        config_service.set_atomic("plugin", "key", "value")

        # 等待异步保存完成
        await asyncio.sleep(0.01)

        # 验证文件内容
        with open(temp_config_file, "r") as f:
            data = yaml.safe_load(f)

        assert data["plugin_config"]["plugin"]["key"] == "value"

    @pytest.mark.asyncio
    async def test_get_plugin_config(self, config_service):
        """测试获取插件所有配置"""
        await config_service.on_load()

        config_service.set("plugin", "key1", "value1")
        config_service.set("plugin", "key2", "value2")

        configs = config_service.get_plugin_config("plugin")

        assert configs == {"key1": "value1", "key2": "value2"}

        # 返回的是副本，修改不影响原数据
        configs["key1"] = "modified"
        assert config_service.get("plugin", "key1") == "value1"

    @pytest.mark.asyncio
    async def test_delete_config_item(self, config_service, temp_config_file):
        """测试删除配置项"""
        await config_service.on_load()

        config_service.set_atomic("plugin", "key1", "value1")
        config_service.set_atomic("plugin", "key2", "value2")

        # 等待异步保存完成
        await asyncio.sleep(0.01)

        config_service.delete_config_item("plugin", "key1")

        # 等待异步保存完成
        await asyncio.sleep(0.01)

        assert config_service.get("plugin", "key1") is None
        assert config_service.get("plugin", "key2") == "value2"

        # 验证文件
        with open(temp_config_file, "r") as f:
            data = yaml.safe_load(f)

        assert "key1" not in data["plugin_config"]["plugin"]

    @pytest.mark.asyncio
    async def test_delete_plugin_config(self, config_service):
        """测试删除插件所有配置"""
        await config_service.on_load()

        config_service.set("plugin", "key1", "value1")
        config_service.register_config("plugin", "key2", "default")

        config_service.delete_plugin_config("plugin")

        assert config_service.get_plugin_config("plugin") == {}
        assert config_service.get_registered_configs("plugin") == {}

    @pytest.mark.asyncio
    async def test_migrate_from_legacy(self, config_service, temp_config_file):
        """测试从旧格式迁移"""
        await config_service.on_load()

        legacy_config = {"api_key": "legacy_key", "enabled": True}

        await config_service.migrate_from_legacy("plugin", legacy_config)

        assert config_service.get("plugin", "api_key") == "legacy_key"
        assert config_service.get("plugin", "enabled") is True

    @pytest.mark.asyncio
    async def test_migrate_does_not_overwrite_existing(self, config_service):
        """测试迁移不覆盖已有配置"""
        await config_service.on_load()

        # 先设置一个值
        config_service.set("plugin", "api_key", "existing_key")

        # 迁移
        legacy_config = {"api_key": "legacy_key", "new_key": "new_value"}
        await config_service.migrate_from_legacy("plugin", legacy_config)

        # 已有的不被覆盖
        assert config_service.get("plugin", "api_key") == "existing_key"
        # 新的被添加
        assert config_service.get("plugin", "new_key") == "new_value"


# =============================================================================
# PluginConfig 只读包装器测试
# =============================================================================


class TestPluginConfig:
    """只读配置包装器测试"""

    @pytest.mark.asyncio
    async def test_get_config_wrapper(self, config_service):
        """测试获取配置包装器"""
        await config_service.on_load()

        config_service.set("plugin", "key", "value")

        wrapper = config_service.get_plugin_config_wrapper("plugin")

        assert isinstance(wrapper, PluginConfig)
        assert wrapper["key"] == "value"

    @pytest.mark.asyncio
    async def test_wrapper_is_readonly(self, config_service):
        """测试包装器是只读的"""
        await config_service.on_load()

        config_service.set("plugin", "key", "value")
        wrapper = config_service.get_plugin_config_wrapper("plugin")

        with pytest.raises(TypeError, match="不支持直接赋值"):
            wrapper["key"] = "new_value"

    @pytest.mark.asyncio
    async def test_wrapper_update_method(self, config_service, temp_config_file):
        """测试包装器的 update 方法"""
        await config_service.on_load()

        config_service.set("plugin", "key", "old_value")
        wrapper = config_service.get_plugin_config_wrapper("plugin")

        old, new = wrapper.update("key", "new_value")

        # 等待异步保存完成
        await asyncio.sleep(0.01)

        assert old == "old_value"
        assert new == "new_value"
        assert wrapper["key"] == "new_value"

        # 验证文件
        with open(temp_config_file, "r") as f:
            data = yaml.safe_load(f)
        assert data["plugin_config"]["plugin"]["key"] == "new_value"

    @pytest.mark.asyncio
    async def test_wrapper_remove_method(self, config_service, temp_config_file):
        """测试包装器的 remove 方法"""
        await config_service.on_load()

        config_service.set_atomic("plugin", "key", "value")
        wrapper = config_service.get_plugin_config_wrapper("plugin")

        old_value = wrapper.remove("key")

        assert old_value == "value"
        assert "key" not in wrapper

    @pytest.mark.asyncio
    async def test_wrapper_bulk_update(self, config_service, temp_config_file):
        """测试包装器的批量更新"""
        await config_service.on_load()

        wrapper = config_service.get_plugin_config_wrapper("plugin")

        wrapper.bulk_update({"key1": "val1", "key2": "val2"})

        # 等待异步保存完成
        await asyncio.sleep(0.01)

        assert wrapper["key1"] == "val1"
        assert wrapper["key2"] == "val2"

        # 验证文件
        with open(temp_config_file, "r") as f:
            data = yaml.safe_load(f)
        assert data["plugin_config"]["plugin"]["key1"] == "val1"
        assert data["plugin_config"]["plugin"]["key2"] == "val2"

    @pytest.mark.asyncio
    async def test_wrapper_mapping_interface(self, config_service):
        """测试包装器实现 Mapping 接口"""
        await config_service.on_load()

        config_service.set("plugin", "key1", "val1")
        config_service.set("plugin", "key2", "val2")
        wrapper = config_service.get_plugin_config_wrapper("plugin")

        # len
        assert len(wrapper) == 2

        # iter
        assert set(wrapper) == {"key1", "key2"}

        # contains
        assert "key1" in wrapper
        assert "missing" not in wrapper

        # get with default
        assert wrapper.get("missing", "default") == "default"

        # keys, values, items
        assert set(wrapper.keys()) == {"key1", "key2"}
        assert set(wrapper.values()) == {"val1", "val2"}
        assert dict(wrapper.items()) == {"key1": "val1", "key2": "val2"}
