"""UnifiedRegistry 端到端测试共享 fixtures"""

import pytest
import pytest_asyncio
from pathlib import Path

from ncatbot.utils.testing import E2ETestSuite
from ncatbot.utils import status

# 测试插件目录
FIXTURES_DIR = Path(__file__).parent / "fixtures"
PLUGINS_DIR = FIXTURES_DIR / "plugins"

# 各插件目录
BASIC_PLUGIN_DIR = PLUGINS_DIR / "basic_command_plugin"
FILTER_PLUGIN_DIR = PLUGINS_DIR / "filter_test_plugin"
PARAMS_PLUGIN_DIR = PLUGINS_DIR / "params_test_plugin"
GROUPS_PLUGIN_DIR = PLUGINS_DIR / "command_groups_plugin"


@pytest_asyncio.fixture
async def basic_command_suite():
    """创建基础命令测试套件"""
    suite = E2ETestSuite()
    await suite.setup()
    suite.index_plugin(str(BASIC_PLUGIN_DIR))
    await suite.register_plugin("basic_command_plugin")

    yield suite

    await suite.teardown()


@pytest_asyncio.fixture
async def filter_suite():
    """创建过滤器测试套件"""
    suite = E2ETestSuite()
    await suite.setup()
    suite.index_plugin(str(FILTER_PLUGIN_DIR))
    await suite.register_plugin("filter_test_plugin")

    yield suite

    await suite.teardown()


@pytest_asyncio.fixture
async def params_suite():
    """创建参数测试套件"""
    suite = E2ETestSuite()
    await suite.setup()
    suite.index_plugin(str(PARAMS_PLUGIN_DIR))
    await suite.register_plugin("params_test_plugin")

    yield suite

    await suite.teardown()


@pytest_asyncio.fixture
async def groups_suite():
    """创建命令分组测试套件"""
    suite = E2ETestSuite()
    await suite.setup()
    suite.index_plugin(str(GROUPS_PLUGIN_DIR))
    await suite.register_plugin("command_groups_plugin")

    yield suite

    await suite.teardown()


@pytest.fixture
def mock_admin():
    """模拟管理员权限"""
    original_manager = status.global_access_manager

    class AdminManager:
        def user_has_role(self, user_id, role):
            return True

    status.global_access_manager = AdminManager()
    yield
    status.global_access_manager = original_manager


@pytest.fixture
def mock_non_admin():
    """模拟非管理员权限"""
    original_manager = status.global_access_manager

    class NonAdminManager:
        def user_has_role(self, user_id, role):
            return False

    status.global_access_manager = NonAdminManager()
    yield
    status.global_access_manager = original_manager
