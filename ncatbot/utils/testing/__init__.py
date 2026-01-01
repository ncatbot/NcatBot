"""
NcatBot 测试工具模块

提供用于插件测试的各种工具和辅助类。

端到端测试推荐使用 E2ETestSuite：
```python
from ncatbot.utils.testing import E2ETestSuite, EventFactory

async with E2ETestSuite() as suite:
    await suite.register_plugin(MyPlugin)
    await suite.inject_group_message("/hello")
    suite.assert_api_called("send_group_msg")
```
"""

from .event_factory import EventFactory
from .mock_api import MockAPIAdapter
from .mock_services import MockMessageRouter, MockPreUploadService, MockWebSocket
from .suite import E2ETestSuite, create_test_suite
from .test_helper import E2ETestHelper

# 向后兼容别名
TestSuite = E2ETestSuite
TestHelper = E2ETestHelper

__all__ = [
    "E2ETestSuite",
    "E2ETestHelper",
    "TestSuite",  # 向后兼容别名
    "TestHelper",  # 向后兼容别名
    "create_test_suite",
    "EventFactory",
    "MockMessageRouter",
    "MockPreUploadService",
    "MockWebSocket",
    "MockAPIAdapter",
]
