"""
BotAPI 端到端测试配置

提供用于测试 BotAPI 的 fixtures。
"""

import pytest
import pytest_asyncio

from ncatbot.utils.testing import E2ETestSuite


@pytest_asyncio.fixture
async def api_suite():
    """
    创建 API 测试套件

    提供已初始化的 E2ETestSuite，可直接访问 BotAPI 进行测试。
    MockServer 使用标准测试数据。
    """
    suite = E2ETestSuite()
    await suite.setup()

    yield suite

    await suite.teardown()


@pytest.fixture
def standard_group_id() -> str:
    """标准测试群号 (来自 get_standard_data 中的群)"""
    return "200001"


@pytest.fixture
def standard_user_id() -> str:
    """标准测试用户 ID (来自 get_standard_data 中的好友)"""
    return "100001"
