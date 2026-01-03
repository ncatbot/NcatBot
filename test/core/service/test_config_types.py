"""
配置类型单元测试

测试 ConfigItem 和 ConfigPersistence 的功能
"""

import pytest
import tempfile
import os
from pathlib import Path
import yaml

from ncatbot.core.service.builtin.plugin_config import (
    ConfigItem,
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
def persistence(temp_config_file):
    """创建持久化处理器"""
    return ConfigPersistence(Path(temp_config_file))


# =============================================================================
# ConfigItem 单元测试
# =============================================================================


class TestConfigItem:
    """配置项测试"""

    def test_create_config_item(self):
        """测试创建配置项"""
        item = ConfigItem(
            name="api_key",
            default_value="",
            description="API 密钥",
            value_type=str,
            metadata={"required": True},
            plugin_name="my_plugin",
        )

        assert item.name == "api_key"
        assert item.default_value == ""
        assert item.description == "API 密钥"
        assert item.value_type is str
        assert item.metadata == {"required": True}
        assert item.plugin_name == "my_plugin"

    def test_parse_value_string(self):
        """测试解析字符串值"""
        item = ConfigItem("test", "", "", str, None, "plugin")
        assert item.parse_value("hello") == "hello"
        assert item.parse_value(123) == "123"

    def test_parse_value_int(self):
        """测试解析整数值"""
        item = ConfigItem("test", 0, "", int, None, "plugin")
        assert item.parse_value("42") == 42
        assert item.parse_value(42) == 42

    def test_parse_value_float(self):
        """测试解析浮点数值"""
        item = ConfigItem("test", 0.0, "", float, None, "plugin")
        assert item.parse_value("3.14") == 3.14
        assert item.parse_value(3.14) == 3.14

    def test_parse_value_bool(self):
        """测试解析布尔值"""
        item = ConfigItem("test", False, "", bool, None, "plugin")

        # True 值
        assert item.parse_value("true") is True
        assert item.parse_value("True") is True
        assert item.parse_value("1") is True
        assert item.parse_value("yes") is True
        assert item.parse_value(True) is True

        # False 值
        assert item.parse_value("false") is False
        assert item.parse_value("False") is False
        assert item.parse_value("0") is False
        assert item.parse_value("no") is False
        assert item.parse_value(False) is False

    def test_parse_value_dict(self):
        """测试解析字典值"""
        item = ConfigItem("test", {}, "", dict, None, "plugin")

        # 直接传入字典
        assert item.parse_value({"key": "value"}) == {"key": "value"}

        # JSON 字符串
        assert item.parse_value('{"key": "value"}') == {"key": "value"}

    def test_parse_value_list(self):
        """测试解析列表值"""
        item = ConfigItem("test", [], "", list, None, "plugin")

        # 直接传入列表
        assert item.parse_value([1, 2, 3]) == [1, 2, 3]

        # JSON 字符串
        assert item.parse_value("[1, 2, 3]") == [1, 2, 3]

    def test_parse_invalid_bool_raises(self):
        """测试无效布尔值抛出异常"""
        item = ConfigItem("test", False, "", bool, None, "plugin")

        with pytest.raises(ValueError, match="Invalid boolean value"):
            item.parse_value("invalid")

    def test_parse_invalid_dict_raises(self):
        """测试无效字典值抛出异常"""
        item = ConfigItem("test", {}, "", dict, None, "plugin")

        with pytest.raises(ValueError, match="无法将"):
            item.parse_value("not a dict")

    def test_config_item_equality(self):
        """测试配置项相等性"""
        item1 = ConfigItem("test", "", "", str, None, "plugin")
        item2 = ConfigItem("test", "default", "desc", str, None, "plugin")
        item3 = ConfigItem("other", "", "", str, None, "plugin")

        assert item1 == item2  # 同名同插件
        assert item1 != item3  # 不同名
        assert item1 == "test"  # 与字符串比较


# =============================================================================
# ConfigPersistence 单元测试
# =============================================================================


class TestConfigPersistence:
    """配置持久化测试"""

    @pytest.mark.asyncio
    async def test_load_empty_file(self, persistence, temp_config_file):
        """测试加载空文件"""
        configs = await persistence.load_all()
        assert configs == {}

    @pytest.mark.asyncio
    async def test_load_existing_config(self, persistence, temp_config_file):
        """测试加载已有配置"""
        # 写入测试数据
        data = {"plugin_config": {"my_plugin": {"api_key": "test123", "enabled": True}}}
        with open(temp_config_file, "w") as f:
            yaml.dump(data, f)

        configs = await persistence.load_all()

        assert "my_plugin" in configs
        assert configs["my_plugin"]["api_key"] == "test123"
        assert configs["my_plugin"]["enabled"] is True

    @pytest.mark.asyncio
    async def test_save_all(self, persistence, temp_config_file):
        """测试保存所有配置"""
        configs = {
            "plugin_a": {"key1": "value1"},
            "plugin_b": {"key2": "value2"},
        }

        await persistence.save_all(configs)

        # 验证文件内容
        with open(temp_config_file, "r") as f:
            data = yaml.safe_load(f)

        assert data["plugin_config"] == configs

    def test_save_item_sync(self, persistence, temp_config_file):
        """测试同步保存单个配置项"""
        configs = {"my_plugin": {"api_key": "new_key", "other": "value"}}

        persistence._save_item_sync(configs, "my_plugin", "api_key")

        # 验证文件内容
        with open(temp_config_file, "r") as f:
            data = yaml.safe_load(f)

        assert data["plugin_config"]["my_plugin"]["api_key"] == "new_key"

    def test_save_item_sync_deleted(self, persistence, temp_config_file):
        """测试同步删除配置项"""
        # 先写入数据
        initial_data = {
            "plugin_config": {"my_plugin": {"api_key": "old", "other": "value"}}
        }
        with open(temp_config_file, "w") as f:
            yaml.dump(initial_data, f)

        configs = {"my_plugin": {"other": "value"}}
        persistence._save_item_sync(configs, "my_plugin", "api_key", deleted=True)

        # 验证文件内容
        with open(temp_config_file, "r") as f:
            data = yaml.safe_load(f)

        assert "api_key" not in data["plugin_config"]["my_plugin"]
        assert data["plugin_config"]["my_plugin"]["other"] == "value"

    def test_save_items_sync(self, persistence, temp_config_file):
        """测试同步保存多个配置项"""
        configs = {"my_plugin": {"key1": "val1", "key2": "val2", "key3": "val3"}}

        persistence._save_items_sync(configs, "my_plugin", ["key1", "key2"])

        # 验证文件内容
        with open(temp_config_file, "r") as f:
            data = yaml.safe_load(f)

        assert data["plugin_config"]["my_plugin"]["key1"] == "val1"
        assert data["plugin_config"]["my_plugin"]["key2"] == "val2"

    def test_save_preserves_other_data(self, persistence, temp_config_file):
        """测试保存时保留其他数据"""
        # 先写入其他数据
        initial_data = {
            "other_key": "other_value",
            "plugin_config": {"existing_plugin": {"key": "value"}},
        }
        with open(temp_config_file, "w") as f:
            yaml.dump(initial_data, f)

        configs = {"new_plugin": {"new_key": "new_value"}}
        persistence._save_item_sync(configs, "new_plugin", "new_key")

        # 验证其他数据保留
        with open(temp_config_file, "r") as f:
            data = yaml.safe_load(f)

        assert data["other_key"] == "other_value"
        assert data["plugin_config"]["existing_plugin"]["key"] == "value"
        assert data["plugin_config"]["new_plugin"]["new_key"] == "new_value"


# =============================================================================
# 异步持久化测试
# =============================================================================


class TestAsyncPersistence:
    """异步持久化测试"""

    @pytest.mark.asyncio
    async def test_async_save_item(self, persistence, temp_config_file):
        """测试异步保存单个配置项"""
        configs = {"plugin": {"key": "value"}}

        await persistence._save_item_async(configs, "plugin", "key")

        with open(temp_config_file, "r") as f:
            data = yaml.safe_load(f)

        assert data["plugin_config"]["plugin"]["key"] == "value"

    @pytest.mark.asyncio
    async def test_async_save_items(self, persistence, temp_config_file):
        """测试异步保存多个配置项"""
        configs = {"plugin": {"key1": "val1", "key2": "val2"}}

        await persistence._save_items_async(configs, "plugin", ["key1", "key2"])

        with open(temp_config_file, "r") as f:
            data = yaml.safe_load(f)

        assert data["plugin_config"]["plugin"]["key1"] == "val1"
        assert data["plugin_config"]["plugin"]["key2"] == "val2"
