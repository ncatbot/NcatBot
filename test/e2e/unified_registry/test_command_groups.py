"""命令分组端到端测试

测试：
- 使用 group() 创建的命令组
- 组内子命令（层级命令）
- 独立命令
"""

import pytest


class TestIndependentCommands:
    """独立命令测试（对照组）"""

    @pytest.mark.asyncio
    async def test_independent_commands_complete(self, groups_suite):
        """测试独立命令功能（综合测试）

        测试内容：
        - 帮助命令
        - 带参数的帮助命令
        """
        # 1. 测试帮助命令
        await groups_suite.inject_private_message("/help")
        groups_suite.assert_reply_sent("可用命令组: user, config")

        # 2. 测试带参数的帮助命令
        groups_suite.clear_call_history()
        await groups_suite.inject_private_message("/help deploy")
        groups_suite.assert_reply_sent("命令 deploy 的帮助信息")


class TestUserGroupCommands:
    """用户组命令测试（层级命令）"""

    @pytest.mark.asyncio
    async def test_user_group_commands_complete(self, groups_suite):
        """测试用户组命令功能（综合测试）

        测试内容：
        - 用户信息命令
        - 用户列表命令
        - 用户列表带页码
        - 用户搜索命令
        """
        # 1. 测试用户信息命令
        await groups_suite.inject_private_message("/user info 12345")
        groups_suite.assert_reply_sent("用户 12345 的信息")

        # 2. 测试用户列表命令
        groups_suite.clear_call_history()
        await groups_suite.inject_private_message("/user list")
        groups_suite.assert_reply_sent("用户列表 (第 1 页)")

        # 3. 测试用户列表带页码
        groups_suite.clear_call_history()
        await groups_suite.inject_private_message("/user list 3")
        groups_suite.assert_reply_sent("用户列表 (第 3 页)")

        # 4. 测试用户搜索命令
        groups_suite.clear_call_history()
        await groups_suite.inject_private_message("/user search admin")
        groups_suite.assert_reply_sent("搜索用户: admin")


class TestConfigGroupCommands:
    """配置组命令测试（层级命令）"""

    @pytest.mark.asyncio
    async def test_config_group_commands_complete(self, groups_suite):
        """测试配置组命令功能（综合测试）

        测试内容：
        - 获取配置命令
        - 设置配置命令
        - 列出配置命令
        """
        # 1. 测试获取配置命令
        await groups_suite.inject_private_message("/config get debug_mode")
        groups_suite.assert_reply_sent("配置项 debug_mode 的值: (mock)")

        # 2. 测试设置配置命令
        groups_suite.clear_call_history()
        await groups_suite.inject_private_message("/config set debug_mode true")
        groups_suite.assert_reply_sent("已设置 debug_mode = true")

        # 3. 测试列出配置命令
        groups_suite.clear_call_history()
        await groups_suite.inject_private_message("/config list")
        groups_suite.assert_reply_sent("所有配置项列表")
