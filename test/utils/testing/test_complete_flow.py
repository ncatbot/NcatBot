"""完整测试流程集成测试

测试 E2ETestSuite 的完整工作流程。
"""

import pytest
import sys
from pathlib import Path

from ncatbot.utils.testing import E2ETestSuite


FIXTURES_DIR = Path(__file__).parent / "fixtures"
PLUGIN_DIR = FIXTURES_DIR / "hello_plugin"


def _cleanup_modules():
    """清理插件模块缓存"""
    modules_to_remove = [
        name
        for name in list(sys.modules.keys())
        if "ncatbot_plugin" in name or "hello_plugin" in name
    ]
    for name in modules_to_remove:
        sys.modules.pop(name, None)


class TestCompleteFlow:
    """完整流程测试"""

    @pytest.mark.asyncio
    async def test_full_test_flow(self):
        """测试完整的端到端测试流程"""
        _cleanup_modules()

        # 1. 初始化测试套件
        suite = E2ETestSuite()
        await suite.setup()

        try:
            # 2. 注册插件
            suite.index_plugin(str(PLUGIN_DIR))
            await suite.register_plugin("hello_plugin")

            # 3. 发送测试消息
            await suite.inject_private_message("/hello")

            # 4. 验证回复
            suite.assert_reply_sent("你好")

            # 5. 检查 API 调用
            calls = suite.get_api_calls("send_private_msg")
            assert len(calls) > 0

            # 6. 清理历史
            suite.clear_call_history()
            calls_after_clear = suite.get_api_calls("send_private_msg")
            assert len(calls_after_clear) == 0

        finally:
            # 7. 清理
            await suite.teardown()
            _cleanup_modules()

    @pytest.mark.asyncio
    async def test_context_manager_flow(self):
        """测试上下文管理器方式的测试流程"""
        _cleanup_modules()

        async with E2ETestSuite() as suite:
            suite.index_plugin(str(PLUGIN_DIR))
            await suite.register_plugin("hello_plugin")

            await suite.inject_private_message("/hello")
            suite.assert_reply_sent("你好")

        _cleanup_modules()

    @pytest.mark.asyncio
    async def test_multiple_commands(self):
        """测试多个命令的连续执行"""
        _cleanup_modules()

        async with E2ETestSuite() as suite:
            suite.index_plugin(str(PLUGIN_DIR))
            await suite.register_plugin("hello_plugin")

            # 测试 hello 命令
            await suite.inject_private_message("/hello")
            suite.assert_reply_sent("你好")

            # 清理后测试 echo 命令
            suite.clear_call_history()
            await suite.inject_private_message("/echo 测试文本")
            suite.assert_reply_sent("测试文本")

            # 测试带选项的 echo 命令
            suite.clear_call_history()
            await suite.inject_private_message("/echo 详细测试 -v")
            suite.assert_reply_sent("verbose")

        _cleanup_modules()

    @pytest.mark.asyncio
    async def test_alias_command(self):
        """测试命令别名"""
        _cleanup_modules()

        async with E2ETestSuite() as suite:
            suite.index_plugin(str(PLUGIN_DIR))
            await suite.register_plugin("hello_plugin")

            # 使用别名 hi 代替 hello
            await suite.inject_private_message("/hi")
            suite.assert_reply_sent("你好")

        _cleanup_modules()
