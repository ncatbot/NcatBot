"""
插件生命周期测试共享 fixtures
"""

import pytest
import pytest_asyncio
import sys
from pathlib import Path

from ncatbot.utils.testing import E2ETestSuite

# 测试插件目录
PLUGINS_DIR = Path(__file__).parent / "plugins"


def get_plugin_class(plugin_name: str):
    """从已加载的模块中获取插件类（用于访问类变量）

    注意：必须在插件加载后调用此函数
    """
    # 插件模块名格式: ncatbot_plugin.<sanitized_name>.main
    for module_name, module in sys.modules.items():
        if "ncatbot_plugin." in module_name and module_name.endswith(".main"):
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type)
                    and hasattr(attr, "name")
                    and getattr(attr, "name", None) == plugin_name
                ):
                    return attr
    return None


def reset_plugin_counters(plugin_name: str):
    """重置指定插件的计数器"""
    plugin_class = get_plugin_class(plugin_name)
    if plugin_class and hasattr(plugin_class, "reset_counters"):
        plugin_class.reset_counters()


@pytest_asyncio.fixture
async def test_suite():
    """创建测试套件并索引所有测试插件"""
    suite = E2ETestSuite()
    await suite.setup()

    # 索引所有测试插件
    for plugin_dir in PLUGINS_DIR.iterdir():
        if plugin_dir.is_dir() and (plugin_dir / "manifest.toml").exists():
            suite.index_plugin(str(plugin_dir))

    yield suite
    await suite.teardown()


@pytest_asyncio.fixture
async def test_suite_skip_builtin():
    """创建跳过内置插件的测试套件"""
    suite = E2ETestSuite()
    await suite.setup()

    # 索引所有测试插件
    for plugin_dir in PLUGINS_DIR.iterdir():
        if plugin_dir.is_dir() and (plugin_dir / "manifest.toml").exists():
            suite.index_plugin(str(plugin_dir))

    yield suite
    await suite.teardown()


# ==================== 插件名 fixtures ====================


@pytest.fixture
def basic_plugin_name() -> str:
    """返回基础测试插件名"""
    return "basic_test_plugin"


@pytest.fixture
def command_plugin_name() -> str:
    """返回命令测试插件名"""
    return "command_test_plugin"


@pytest.fixture
def config_plugin_name() -> str:
    """返回配置测试插件名"""
    return "config_test_plugin"


@pytest.fixture
def handler_plugin_name() -> str:
    """返回事件处理器测试插件名"""
    return "handler_test_plugin"


@pytest.fixture
def full_feature_plugin_name() -> str:
    """返回完整功能测试插件名"""
    return "full_feature_plugin"
