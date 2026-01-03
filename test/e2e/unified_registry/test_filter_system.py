"""过滤器系统 E2E 测试

测试 filter_system 的功能，包括：
- 基础过滤器 (GroupFilter, PrivateFilter, AdminFilter, RootFilter)
- 组合过滤器 (| 和 &)
- 自定义过滤器 (CustomFilter)
- 指定群号过滤器
- 过滤器类基础功能
"""

import sys
from pathlib import Path

import pytest

from ncatbot.utils.testing import E2ETestSuite
from ncatbot.core.service.builtin.unified_registry.filter_system.base import (
    CombinedFilter,
)
from ncatbot.core.service.builtin.unified_registry.filter_system.builtin import (
    GroupFilter,
    PrivateFilter,
    CustomFilter,
    TrueFilter,
    NonSelfFilter,
    MessageSentFilter,
    GroupAdminFilter,
    GroupOwnerFilter,
)


# 测试插件目录
FIXTURES_DIR = Path(__file__).parent / "fixtures"
PLUGINS_DIR = FIXTURES_DIR / "plugins"
FILTER_PLUGIN_DIR = PLUGINS_DIR / "filter_test_plugin"


def _cleanup_modules():
    """清理插件模块缓存"""
    modules_to_remove = [
        name
        for name in list(sys.modules.keys())
        if "filter_test_plugin" in name or "ncatbot_plugin" in name
    ]
    for name in modules_to_remove:
        sys.modules.pop(name, None)


class MockEvent:
    """模拟消息事件"""

    def __init__(
        self,
        user_id=12345,
        self_id=99999,
        group_id=None,
        raw_message="test",
        sender=None,
    ):
        self.user_id = user_id
        self.self_id = self_id
        self.group_id = group_id
        self.raw_message = raw_message
        self.sender = sender or MockSender()

    def is_group_event(self):
        return self.group_id is not None


class MockSender:
    """模拟发送者信息"""

    def __init__(self, role="member"):
        self.role = role


# ==========================================================================
# 基础过滤器单元测试
# ==========================================================================


class TestGroupFilterUnit:
    """GroupFilter 单元测试"""

    def test_group_filter_passes_group_event(self):
        """测试群聊事件通过"""
        f = GroupFilter()
        event = MockEvent(group_id=123456)
        assert f.check(event) is True

    def test_group_filter_blocks_private_event(self):
        """测试私聊事件被拦截"""
        f = GroupFilter()
        event = MockEvent(group_id=None)
        assert f.check(event) is False

    def test_group_filter_with_allowed_single(self):
        """测试指定单个群号"""
        f = GroupFilter(allowed=123456)
        event = MockEvent(group_id=123456)
        assert f.check(event) is True

        event2 = MockEvent(group_id=789012)
        assert f.check(event2) is False

    def test_group_filter_with_allowed_list(self):
        """测试指定多个群号"""
        f = GroupFilter(allowed=[123456, 789012])
        assert f.check(MockEvent(group_id=123456)) is True
        assert f.check(MockEvent(group_id=789012)) is True
        assert f.check(MockEvent(group_id=111111)) is False

    def test_group_filter_with_string_id(self):
        """测试字符串群号"""
        f = GroupFilter(allowed="123456")
        assert f.check(MockEvent(group_id=123456)) is True
        assert f.check(MockEvent(group_id="123456")) is True


class TestPrivateFilterUnit:
    """PrivateFilter 单元测试"""

    def test_private_filter_passes_private_event(self):
        """测试私聊事件通过"""
        f = PrivateFilter()
        event = MockEvent(group_id=None)
        assert f.check(event) is True

    def test_private_filter_blocks_group_event(self):
        """测试群聊事件被拦截"""
        f = PrivateFilter()
        event = MockEvent(group_id=123456)
        assert f.check(event) is False


class TestNonSelfFilterUnit:
    """NonSelfFilter 单元测试"""

    def test_non_self_filter_passes_other_user(self):
        """测试其他用户消息通过"""
        f = NonSelfFilter()
        event = MockEvent(user_id=12345, self_id=99999)
        assert f.check(event) is True

    def test_non_self_filter_blocks_self(self):
        """测试自己的消息被拦截"""
        f = NonSelfFilter()
        event = MockEvent(user_id=99999, self_id=99999)
        assert f.check(event) is False


class TestMessageSentFilterUnit:
    """MessageSentFilter 单元测试"""

    def test_message_sent_filter_passes_self(self):
        """测试自己发送的消息通过"""
        f = MessageSentFilter()
        event = MockEvent(user_id=99999, self_id=99999)
        assert f.check(event) is True

    def test_message_sent_filter_blocks_other(self):
        """测试他人消息被拦截"""
        f = MessageSentFilter()
        event = MockEvent(user_id=12345, self_id=99999)
        assert f.check(event) is False


class TestTrueFilterUnit:
    """TrueFilter 单元测试"""

    def test_true_filter_always_passes(self):
        """测试 TrueFilter 总是通过"""
        f = TrueFilter()
        assert f.check(MockEvent()) is True
        assert f.check(MockEvent(group_id=123)) is True


class TestCustomFilterUnit:
    """CustomFilter 单元测试"""

    def test_custom_filter_with_lambda(self):
        """测试使用 lambda 的自定义过滤器"""
        f = CustomFilter(lambda e: e.user_id == 12345, "user_check")
        assert f.check(MockEvent(user_id=12345)) is True
        assert f.check(MockEvent(user_id=99999)) is False

    def test_custom_filter_name(self):
        """测试自定义过滤器名称"""

        def my_filter(event):
            return True

        f = CustomFilter(my_filter, "my_custom")
        assert f.name == "my_custom"


class TestGroupAdminFilterUnit:
    """GroupAdminFilter 单元测试"""

    def test_group_admin_filter_passes_admin(self):
        """测试群管理员通过"""
        f = GroupAdminFilter()
        event = MockEvent(group_id=123, sender=MockSender(role="admin"))
        assert f.check(event) is True

    def test_group_admin_filter_passes_owner(self):
        """测试群主通过"""
        f = GroupAdminFilter()
        event = MockEvent(group_id=123, sender=MockSender(role="owner"))
        assert f.check(event) is True

    def test_group_admin_filter_blocks_member(self):
        """测试普通成员被拦截"""
        f = GroupAdminFilter()
        event = MockEvent(group_id=123, sender=MockSender(role="member"))
        assert f.check(event) is False

    def test_group_admin_filter_blocks_private(self):
        """测试私聊被拦截"""
        f = GroupAdminFilter()
        event = MockEvent(group_id=None, sender=MockSender(role="admin"))
        assert f.check(event) is False


class TestGroupOwnerFilterUnit:
    """GroupOwnerFilter 单元测试"""

    def test_group_owner_filter_passes_owner(self):
        """测试群主通过"""
        f = GroupOwnerFilter()
        event = MockEvent(group_id=123, sender=MockSender(role="owner"))
        assert f.check(event) is True

    def test_group_owner_filter_blocks_admin(self):
        """测试管理员被拦截"""
        f = GroupOwnerFilter()
        event = MockEvent(group_id=123, sender=MockSender(role="admin"))
        assert f.check(event) is False


# ==========================================================================
# 组合过滤器单元测试
# ==========================================================================


class TestCombinedFilterUnit:
    """CombinedFilter 单元测试"""

    def test_or_filter_passes_when_left_passes(self):
        """测试 OR 组合：左边通过时通过"""
        f = CombinedFilter(GroupFilter(), PrivateFilter(), "or")
        event = MockEvent(group_id=123)
        assert f.check(event) is True

    def test_or_filter_passes_when_right_passes(self):
        """测试 OR 组合：右边通过时通过"""
        f = CombinedFilter(GroupFilter(), PrivateFilter(), "or")
        event = MockEvent(group_id=None)
        assert f.check(event) is True

    def test_and_filter_passes_when_both_pass(self):
        """测试 AND 组合：两边都通过时通过"""
        # 创建两个都会通过的过滤器
        f = CombinedFilter(GroupFilter(), TrueFilter(), "and")
        event = MockEvent(group_id=123)
        assert f.check(event) is True

    def test_and_filter_fails_when_left_fails(self):
        """测试 AND 组合：左边失败时失败"""
        f = CombinedFilter(GroupFilter(), TrueFilter(), "and")
        event = MockEvent(group_id=None)  # 私聊，GroupFilter 失败
        assert f.check(event) is False

    def test_operator_or(self):
        """测试 | 操作符"""
        f = GroupFilter() | PrivateFilter()
        assert isinstance(f, CombinedFilter)
        assert f.mode == "or"

    def test_operator_and(self):
        """测试 & 操作符"""
        f = GroupFilter() & TrueFilter()
        assert isinstance(f, CombinedFilter)
        assert f.mode == "and"

    def test_invalid_mode_raises(self):
        """测试无效模式抛出异常"""
        with pytest.raises(ValueError):
            CombinedFilter(GroupFilter(), PrivateFilter(), "invalid")

    def test_invalid_operand_raises(self):
        """测试无效操作数抛出异常"""
        f = GroupFilter()
        with pytest.raises(TypeError):
            f | "not_a_filter"
        with pytest.raises(TypeError):
            f & 123


# ==========================================================================
# 过滤器基类测试
# ==========================================================================


class TestBaseFilterUnit:
    """BaseFilter 单元测试"""

    def test_filter_str_repr(self):
        """测试过滤器字符串表示"""
        f = GroupFilter()
        assert "GroupFilter" in str(f)
        assert "GroupFilter" in repr(f)

    def test_filter_custom_name(self):
        """测试自定义名称"""
        f = GroupFilter(name="MyCustomGroup")
        assert f.name == "MyCustomGroup"


# ==========================================================================
# E2E 测试
# ==========================================================================


class TestFilterSystemE2E:
    """过滤器系统 E2E 测试"""

    @pytest.mark.asyncio
    async def test_plugin_loads_successfully(self):
        """测试插件加载成功"""
        _cleanup_modules()

        from ncatbot.core.service.builtin.unified_registry import command_registry

        async with E2ETestSuite() as suite:
            suite.index_plugin(str(FILTER_PLUGIN_DIR))
            await suite.register_plugin("filter_test_plugin")

            all_commands = command_registry.get_all_commands()
            assert any("group_only" in path for path in all_commands.keys())
            assert any("private_only" in path for path in all_commands.keys())
            assert any("special_group" in path for path in all_commands.keys())

        _cleanup_modules()

    @pytest.mark.asyncio
    async def test_true_filter_always_passes(self):
        """测试 TrueFilter 命令总是可用"""
        _cleanup_modules()

        async with E2ETestSuite() as suite:
            suite.index_plugin(str(FILTER_PLUGIN_DIR))
            await suite.register_plugin("filter_test_plugin")

            # 群聊中可用
            await suite.inject_group_message("/always_pass")
            suite.assert_reply_sent("总是通过")

            suite.clear_call_history()

            # 私聊中也可用
            await suite.inject_private_message("/always_pass")
            suite.assert_reply_sent("总是通过")

        _cleanup_modules()

    @pytest.mark.asyncio
    async def test_combined_or_filter(self):
        """测试组合过滤器 (OR)"""
        _cleanup_modules()

        async with E2ETestSuite() as suite:
            suite.index_plugin(str(FILTER_PLUGIN_DIR))
            await suite.register_plugin("filter_test_plugin")

            # any_chat 使用 GroupFilter | PrivateFilter
            # 群聊中可用
            await suite.inject_group_message("/any_chat")
            suite.assert_reply_sent("任意聊天类型")

            suite.clear_call_history()

            # 私聊中也可用
            await suite.inject_private_message("/any_chat")
            suite.assert_reply_sent("任意聊天类型")

        _cleanup_modules()

    @pytest.mark.asyncio
    async def test_specified_group_filter(self):
        """测试指定群号过滤器"""
        _cleanup_modules()

        async with E2ETestSuite() as suite:
            suite.index_plugin(str(FILTER_PLUGIN_DIR))
            await suite.register_plugin("filter_test_plugin")

            # 在指定群 123456 中可用
            await suite.inject_group_message("/special_group", group_id=123456)
            suite.assert_reply_sent("这是特定群专用命令")

            suite.clear_call_history()

            # 在其他群中不可用
            await suite.inject_group_message("/special_group", group_id=999999)
            suite.assert_no_reply()

        _cleanup_modules()

    @pytest.mark.asyncio
    async def test_multiple_group_filter(self):
        """测试多群号过滤器"""
        _cleanup_modules()

        async with E2ETestSuite() as suite:
            suite.index_plugin(str(FILTER_PLUGIN_DIR))
            await suite.register_plugin("filter_test_plugin")

            # 在群 123456 中可用
            await suite.inject_group_message("/multi_group", group_id=123456)
            suite.assert_reply_sent("这是多群专用命令")

            suite.clear_call_history()

            # 在群 789012 中也可用
            await suite.inject_group_message("/multi_group", group_id=789012)
            suite.assert_reply_sent("这是多群专用命令")

            suite.clear_call_history()

            # 在其他群中不可用
            await suite.inject_group_message("/multi_group", group_id=999999)
            suite.assert_no_reply()

        _cleanup_modules()
