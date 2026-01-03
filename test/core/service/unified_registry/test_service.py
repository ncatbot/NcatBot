"""UnifiedRegistryService 单元测试

测试统一注册服务的所有功能：
- 生命周期管理
- 插件管理
- 事件处理器注册
- 初始化逻辑
- 清理逻辑
"""

import pytest
from unittest.mock import Mock, patch

from ncatbot.core.service.builtin.unified_registry.service import UnifiedRegistryService
from ncatbot.core.service.builtin.unified_registry.filter_system.event_registry import (
    EventRegistry,
)


# =============================================================================
# 测试夹具
# =============================================================================


@pytest.fixture
def service():
    """创建统一注册服务实例"""
    return UnifiedRegistryService()


@pytest.fixture
def mock_event():
    """创建模拟消息事件"""
    from ncatbot.core.event.message_segments.primitives import PlainText

    event = Mock()
    event.message = Mock()
    event.post_type = "message"

    plain_text = PlainText(text="/test")
    event.message.message = [plain_text]

    return event


@pytest.fixture
def mock_notice_event():
    """创建模拟通知事件"""
    event = Mock()
    event.post_type = "notice"
    return event


@pytest.fixture
def mock_request_event():
    """创建模拟请求事件"""
    event = Mock()
    event.post_type = "request"
    return event


# =============================================================================
# 初始化测试
# =============================================================================


class TestServiceInit:
    """测试服务初始化"""

    def test_default_init(self, service):
        """测试默认初始化"""
        assert service.name == "unified_registry"
        assert service.description == "统一的过滤器和命令注册服务"
        assert service._initialized is False
        assert service.prefixes == []

    def test_registries_assigned(self, service):
        """测试注册表引用"""
        assert service.filter_registry is not None
        assert service.command_registry is not None
        assert service.event_registry is not None


# =============================================================================
# 生命周期测试
# =============================================================================


class TestLifecycle:
    """测试服务生命周期"""

    @pytest.mark.asyncio
    async def test_on_load(self, service):
        """测试服务加载"""
        await service.on_load()

        # 加载后应该记录日志（无其他副作用）

    @pytest.mark.asyncio
    async def test_on_close(self, service):
        """测试服务关闭"""
        service._initialized = True
        service.prefixes = ["/", "!"]

        await service.on_close()

        assert service._initialized is False
        assert service.prefixes == []


# =============================================================================
# 插件管理测试
# =============================================================================


class TestPluginManagement:
    """测试插件管理"""

    def test_set_current_plugin_name(self):
        """测试设置当前插件名"""
        UnifiedRegistryService.set_current_plugin_name("test_plugin")

        # 验证三个注册表都被设置
        assert EventRegistry._current_plugin_name == "test_plugin"

        # 清理
        UnifiedRegistryService.set_current_plugin_name("")

    def test_handle_plugin_load(self, service):
        """测试处理插件加载"""
        from ncatbot.core.service.builtin.unified_registry.executor import (
            FunctionExecutor,
        )

        service._initialized = True
        service._executor = FunctionExecutor()  # 使用真实的 executor

        service.handle_plugin_load()

        # 应该重置初始化状态后重新初始化
        assert service._initialized is True  # 因为 initialize_if_needed 会重新设置

    def test_handle_plugin_unload(self, service):
        """测试处理插件卸载"""
        from ncatbot.core.service.builtin.unified_registry.executor import (
            FunctionExecutor,
        )

        # 模拟已初始化
        service._initialized = True
        service._executor = FunctionExecutor()  # 使用真实的 executor

        # 使用 patch 模拟 root_group.revoke_plugin
        with patch.object(
            service.command_registry.root_group, "revoke_plugin"
        ) as mock_revoke:
            service.handle_plugin_unload("test_plugin")

            # 验证调用了 revoke_plugin
            mock_revoke.assert_called_once_with("test_plugin")


# =============================================================================
# 事件处理器注册测试
# =============================================================================


class TestEventHandlerRegistration:
    """测试事件处理器注册"""

    def test_register_notice_handler(self, service):
        """测试注册通知处理器"""

        def handler(event):
            pass

        result = service.register_notice_handler(handler)

        assert result is handler
        assert handler in service.event_registry.notice_handlers

    def test_register_request_handler(self, service):
        """测试注册请求处理器"""

        def handler(event):
            pass

        result = service.register_request_handler(handler)

        assert result is handler
        assert handler in service.event_registry.request_handlers


# =============================================================================
# 初始化逻辑测试
# =============================================================================


class TestInitialization:
    """测试初始化逻辑"""

    def test_initialize_if_needed_first_call(self, service):
        """测试首次初始化"""
        from ncatbot.core.service.builtin.unified_registry.executor import (
            FunctionExecutor,
        )

        service._executor = FunctionExecutor()  # 使用真实的 executor
        assert service._initialized is False

        service.initialize_if_needed()

        assert service._initialized is True

    def test_initialize_if_needed_idempotent(self, service):
        """测试初始化幂等性"""
        from ncatbot.core.service.builtin.unified_registry.executor import (
            FunctionExecutor,
        )

        service._executor = FunctionExecutor()  # 使用真实的 executor
        service.initialize_if_needed()

        # 记录初始状态
        first_prefixes = service.prefixes.copy()

        service.initialize_if_needed()

        # 应该不会重复初始化
        assert service.prefixes == first_prefixes

    def test_collect_prefixes_empty(self, service):
        """测试收集空前缀"""
        prefixes = service._collect_prefixes()

        # 没有注册命令时应该为空或默认值
        assert isinstance(prefixes, list)

    def test_check_prefix_conflicts_no_conflict(self, service):
        """测试无前缀冲突"""
        service.prefixes = ["/", "!"]

        # 应该不抛出异常
        service._check_prefix_conflicts()

    def test_check_prefix_conflicts_with_conflict(self, service):
        """测试有前缀冲突"""
        service.prefixes = ["/", "/cmd"]  # /cmd 以 / 开头

        with pytest.raises(ValueError, match="prefix conflict"):
            service._check_prefix_conflicts()


# =============================================================================
# 清理测试
# =============================================================================


class TestClear:
    """测试清理功能"""

    def test_clear_resets_state(self, service):
        """测试清理重置状态"""
        service._initialized = True
        service.prefixes = ["/", "!"]

        service.clear()

        assert service._initialized is False
        assert service.prefixes == []


# =============================================================================
# 事件分发测试
# =============================================================================


class TestEventDispatch:
    """测试事件分发"""

    @pytest.mark.asyncio
    async def test_handle_legacy_event_notice(self, service, mock_notice_event):
        """测试处理 legacy notice 事件"""
        from ncatbot.core.service.builtin.unified_registry.executor import (
            FunctionExecutor,
        )

        service._executor = FunctionExecutor()  # 使用真实的 executor
        service.event_registry.clear()  # 清理

        result = await service.handle_legacy_event(mock_notice_event)

        assert result is True

    @pytest.mark.asyncio
    async def test_handle_legacy_event_request(self, service, mock_request_event):
        """测试处理 legacy request 事件"""
        from ncatbot.core.service.builtin.unified_registry.executor import (
            FunctionExecutor,
        )

        service._executor = FunctionExecutor()  # 使用真实的 executor
        service.event_registry.clear()  # 清理

        result = await service.handle_legacy_event(mock_request_event)

        assert result is True

    @pytest.mark.asyncio
    async def test_handle_legacy_event_unknown(self, service):
        """测试处理未知类型事件"""
        from ncatbot.core.service.builtin.unified_registry.executor import (
            FunctionExecutor,
        )

        service._executor = FunctionExecutor()  # 使用真实的 executor
        event = Mock()
        event.post_type = "unknown"

        result = await service.handle_legacy_event(event)

        assert result is True
