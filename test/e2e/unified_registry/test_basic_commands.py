"""基础命令端到端测试

测试：
- 简单命令执行
- 带参数命令
- 带选项命令
- 命令别名
"""

import pytest


class TestSimpleCommands:
    """简单命令测试"""

    @pytest.mark.asyncio
    async def test_simple_commands_complete(self, basic_command_suite):
        """测试简单命令功能（综合测试）

        测试内容：
        - 简单问候命令
        - ping 命令
        - 群聊中的命令
        """
        # 1. 测试简单问候命令
        await basic_command_suite.inject_private_message("/hello")
        basic_command_suite.assert_reply_sent("你好！我是机器人。")

        # 2. 测试 ping 命令
        basic_command_suite.clear_call_history()
        await basic_command_suite.inject_private_message("/ping")
        basic_command_suite.assert_reply_sent("pong!")

        # 3. 测试群聊中的命令
        basic_command_suite.clear_call_history()
        await basic_command_suite.inject_group_message("/hello")
        basic_command_suite.assert_reply_sent("你好！我是机器人。")


class TestParameterCommands:
    """带参数命令测试"""

    @pytest.mark.asyncio
    async def test_parameter_commands_complete(self, basic_command_suite):
        """测试带参数命令功能（综合测试）

        测试内容：
        - 回显命令
        - 加法命令
        - 带默认参数的命令
        - 自定义参数的命令
        """
        # 1. 测试回显命令
        await basic_command_suite.inject_private_message("/echo 测试文本")
        basic_command_suite.assert_reply_sent("你说的是: 测试文本")

        # 2. 测试加法命令
        basic_command_suite.clear_call_history()
        await basic_command_suite.inject_private_message("/add 10 20")
        basic_command_suite.assert_reply_sent("10 + 20 = 30")

        # 3. 测试带默认参数的命令
        basic_command_suite.clear_call_history()
        await basic_command_suite.inject_private_message("/greet 小明")
        basic_command_suite.assert_reply_sent("你好, 小明!")

        # 4. 测试自定义参数的命令
        basic_command_suite.clear_call_history()
        await basic_command_suite.inject_private_message("/greet 小明 早上好")
        basic_command_suite.assert_reply_sent("早上好, 小明!")


class TestOptionCommands:
    """带选项命令测试"""

    @pytest.mark.asyncio
    async def test_option_commands_complete(self, basic_command_suite):
        """测试带选项命令功能（综合测试）

        测试内容：
        - 基础部署命令
        - 指定环境的部署命令
        - 详细模式的部署命令
        - 强制模式的部署命令
        """
        # 1. 测试基础部署命令
        await basic_command_suite.inject_private_message("/deploy myapp")
        basic_command_suite.assert_reply_sent("正在部署 myapp 到 dev 环境")

        # 2. 测试指定环境的部署命令
        basic_command_suite.clear_call_history()
        await basic_command_suite.inject_private_message("/deploy myapp --env=prod")
        basic_command_suite.assert_reply_sent("正在部署 myapp 到 prod 环境")

        # 3. 测试详细模式的部署命令
        basic_command_suite.clear_call_history()
        await basic_command_suite.inject_private_message("/deploy myapp -v")
        basic_command_suite.assert_reply_sent("详细信息: 开始部署流程...")

        # 4. 测试强制模式的部署命令
        basic_command_suite.clear_call_history()
        await basic_command_suite.inject_private_message("/deploy myapp --force")
        basic_command_suite.assert_reply_sent("(强制模式)")


class TestAliasCommands:
    """命令别名测试"""

    @pytest.mark.asyncio
    async def test_alias_commands_complete(self, basic_command_suite):
        """测试命令别名功能（综合测试）

        测试内容：
        - 主命令
        - 别名 stat
        - 别名 st
        """
        # 1. 测试主命令
        await basic_command_suite.inject_private_message("/status")
        basic_command_suite.assert_reply_sent("机器人运行正常")

        # 2. 测试别名 stat
        basic_command_suite.clear_call_history()
        await basic_command_suite.inject_private_message("/stat")
        basic_command_suite.assert_reply_sent("机器人运行正常")

        # 3. 测试别名 st
        basic_command_suite.clear_call_history()
        await basic_command_suite.inject_private_message("/st")
        basic_command_suite.assert_reply_sent("机器人运行正常")
