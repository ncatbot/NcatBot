"""
LifecycleManager 单元测试

测试生命周期管理器的核心功能：
- 初始化和状态管理
- 启动参数验证
- 异步关闭流程
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ncatbot.core.client.lifecycle import LifecycleManager, LEGAL_ARGS
from ncatbot.utils.error import NcatBotError


class TestLifecycleManagerInit:
    """初始化测试"""

    def test_init_with_required_components(self, event_bus, mock_services):
        """测试使用必需组件初始化"""
        from ncatbot.core.client.registry import EventRegistry

        registry = EventRegistry(event_bus)

        manager = LifecycleManager(mock_services, event_bus, registry)

        assert manager.services is mock_services
        assert manager.event_bus is event_bus
        assert manager.registry is registry
        assert manager._running is False
        assert manager.api is None
        assert manager.dispatcher is None
        assert manager._main_task is None

    def test_init_state(self, event_bus, mock_services):
        """测试初始状态"""
        from ncatbot.core.client.registry import EventRegistry

        registry = EventRegistry(event_bus)

        manager = LifecycleManager(mock_services, event_bus, registry)

        assert manager._skip_plugin_load is False
        assert manager._startup_event is None
        assert manager.plugin_loader is None


class TestPrepareStartup:
    """_prepare_startup 方法测试"""

    @pytest.fixture
    def manager(self, event_bus, mock_services):
        from ncatbot.core.client.registry import EventRegistry

        registry = EventRegistry(event_bus)
        return LifecycleManager(mock_services, event_bus, registry)

    @patch("ncatbot.core.client.lifecycle.launch_napcat_service")
    @patch("ncatbot.core.client.lifecycle.ncatbot_config")
    def test_prepare_startup_normal_mode(self, mock_config, mock_launch, manager):
        """测试正常模式启动准备"""
        mock_config.debug = False

        manager._prepare_startup(mock=False)

        assert manager._test_mode is False  # 非 test 模式 (Mock 模式)
        assert manager._running is True
        assert manager.plugin_loader is not None
        mock_launch.assert_called_once()

    @patch("ncatbot.core.client.lifecycle.launch_napcat_service")
    @patch("ncatbot.core.client.lifecycle.ncatbot_config")
    def test_prepare_startup_mock_mode(self, mock_config, mock_launch, manager):
        """测试 mock 模式启动准备（不启动 NapCat）"""
        mock_config.debug = False

        manager._prepare_startup(mock=True)

        assert manager._test_mode is True  # test 模式 (Mock 模式)
        assert manager._running is True
        mock_launch.assert_not_called()

    @patch("ncatbot.core.client.lifecycle.launch_napcat_service")
    @patch("ncatbot.core.client.lifecycle.ncatbot_config")
    def test_prepare_startup_skip_plugin_load(self, mock_config, mock_launch, manager):
        """测试跳过插件加载"""
        mock_config.debug = False
        # 模拟 update_value 后 skip_plugin_load 被设置为 True
        mock_config.plugin.skip_plugin_load = True

        manager._prepare_startup(mock=True, skip_plugin_load=True)

        assert manager._skip_plugin_load is True

    @patch("ncatbot.core.client.lifecycle.ncatbot_config")
    def test_prepare_startup_illegal_arg(self, mock_config, manager):
        """测试非法参数抛出异常"""
        with pytest.raises(NcatBotError, match="非法启动参数"):
            manager._prepare_startup(illegal_param="value")


class TestShutdown:
    """shutdown 方法测试"""

    @pytest.fixture
    def manager(self, event_bus, mock_services):
        from ncatbot.core.client.registry import EventRegistry

        registry = EventRegistry(event_bus)
        return LifecycleManager(mock_services, event_bus, registry)

    @pytest.mark.asyncio
    async def test_shutdown_when_not_running(self, manager):
        """测试未运行时调用 shutdown 应该安全返回"""
        manager._running = False

        await manager.shutdown()  # 不应抛出异常

    @pytest.mark.asyncio
    async def test_shutdown_cancels_main_task(self, manager):
        """测试 shutdown 会取消主任务"""
        manager._running = True

        # 创建一个模拟的 long-running task
        async def long_running():
            try:
                await asyncio.sleep(100)
            except asyncio.CancelledError:
                raise

        manager._main_task = asyncio.create_task(long_running())
        await asyncio.sleep(0.01)  # 让任务启动

        await manager.shutdown()

        assert manager._main_task.done()
        assert manager._main_task.cancelled()

    @pytest.mark.asyncio
    async def test_shutdown_when_task_already_done(self, manager):
        """测试任务已完成时 shutdown 应该安全返回"""
        manager._running = True

        async def quick_task():
            return "done"

        manager._main_task = asyncio.create_task(quick_task())
        await manager._main_task  # 等待完成

        await manager.shutdown()  # 不应抛出异常


class TestBotExit:
    """bot_exit 方法测试"""

    @pytest.fixture
    def manager(self, event_bus, mock_services):
        from ncatbot.core.client.registry import EventRegistry

        registry = EventRegistry(event_bus)
        return LifecycleManager(mock_services, event_bus, registry)

    def test_bot_exit_when_not_running(self, manager):
        """测试未运行时调用 bot_exit"""
        manager._running = False

        manager.bot_exit()  # 不应抛出异常

    @pytest.mark.asyncio
    async def test_bot_exit_cancels_task(self, manager):
        """测试 bot_exit 会取消主任务"""
        manager._running = True

        async def long_running():
            await asyncio.sleep(100)

        manager._main_task = asyncio.create_task(long_running())
        await asyncio.sleep(0.01)

        manager.bot_exit()

        # 等待取消生效
        await asyncio.sleep(0.01)
        assert manager._main_task.cancelled() or manager._main_task.done()


class TestCleanup:
    """_cleanup 方法测试"""

    @pytest.fixture
    def manager(self, event_bus, mock_services):
        from ncatbot.core.client.registry import EventRegistry

        registry = EventRegistry(event_bus)
        return LifecycleManager(mock_services, event_bus, registry)

    @pytest.mark.asyncio
    async def test_cleanup_when_not_running(self, manager):
        """测试未运行时调用 _cleanup 应该直接返回"""
        manager._running = False

        await manager._cleanup()  # 不应抛出异常

    @pytest.mark.asyncio
    async def test_cleanup_closes_services(self, manager):
        """测试 _cleanup 会关闭服务"""
        manager._running = True
        manager.plugin_loader = MagicMock()
        manager.plugin_loader.unload_all = AsyncMock()

        await manager._cleanup()

        assert manager._running is False
        manager.plugin_loader.unload_all.assert_awaited_once()
        manager.services.close_all.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_cleanup_idempotent(self, manager):
        """测试 _cleanup 幂等性（重复调用安全）"""
        manager._running = True
        manager.plugin_loader = MagicMock()
        manager.plugin_loader.unload_all = AsyncMock()

        await manager._cleanup()
        await manager._cleanup()  # 第二次调用应该什么都不做

        # unload_all 只应调用一次
        assert manager.plugin_loader.unload_all.await_count == 1


class TestLegalArgs:
    """合法参数常量测试"""

    def test_legal_args_contains_expected_keys(self):
        """测试 LEGAL_ARGS 包含预期的键"""
        expected = {
            "bt_uin",
            "root",
            "ws_uri",
            "webui_uri",
            "ws_token",
            "webui_token",
            "ws_listen_ip",
            "remote_mode",
            "enable_webui",
            "enable_webui_interaction",
            "debug",
            "mock",
            "skip_plugin_load",
        }
        assert set(LEGAL_ARGS) == expected
