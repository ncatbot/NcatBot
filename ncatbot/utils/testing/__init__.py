"""
NcatBot 测试工具模块

提供用于插件测试的各种工具和辅助类。

端到端测试推荐使用 create_test_suite_with_mock_server：
```python
from ncatbot.utils.testing import create_test_suite_with_mock_server, get_standard_data

async with create_test_suite_with_mock_server(
    initial_data=get_standard_data()
) as suite:
    await suite.register_plugin("my_plugin")
    await suite.inject_group_message("/hello")
    suite.assert_api_called("send_group_msg")
```

同步使用（pytest fixtures）：
```python
@pytest.fixture
def test_suite():
    suite = E2ETestSuite()
    suite.setup()  # 自动创建 MockServer
    yield suite
    suite.teardown()
```
"""

from .event_factory import EventFactory
from .suite import E2ETestSuite, create_test_suite_with_mock_server

# Mock Server 组件
from .mock_server import (
    # 核心组件
    NapCatMockServer,
    MockServerClient,
    MockDatabase,
    MockApiHandler,
    # 数据创建函数
    create_bot_data,
    create_user_data,
    create_group_member_data,
    create_group_data,
    create_file_data,
    create_folder_data,
    # 预定义数据模板
    get_minimal_data,
    get_standard_data,
    get_rich_data,
    # 场景构建器
    ScenarioBuilder,
)


__all__ = [
    # 测试套件
    "E2ETestSuite",
    "create_test_suite_with_mock_server",
    "EventFactory",
    # Mock Server（WebSocket 模式）
    "NapCatMockServer",
    "MockServerClient",
    "MockDatabase",
    "MockApiHandler",
    # 数据创建函数
    "create_bot_data",
    "create_user_data",
    "create_group_member_data",
    "create_group_data",
    "create_file_data",
    "create_folder_data",
    # 预定义数据模板
    "get_minimal_data",
    "get_standard_data",
    "get_rich_data",
    # 场景构建器
    "ScenarioBuilder",
]
