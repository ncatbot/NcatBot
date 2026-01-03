"""
test/integration/test_startup_flow.py

Bot 启动流程集成测试
覆盖：参数验证、异步启动流、异常处理、资源清理及线程模式。
"""

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch

from ncatbot.core.client.lifecycle import LifecycleManager, NcatBotError
from ncatbot.core.api import BotAPI
from ncatbot.core.service import ServiceManager
from ncatbot.core.client.registry import EventRegistry

# ======================= Fixtures =======================


@pytest.fixture
def mock_services():
    """Mock ServiceManager"""
    services = MagicMock(spec=ServiceManager)
    services.load_all = AsyncMock()
    services.close_all = AsyncMock()

    # Mock message_router and websocket behavior
    router = MagicMock()
    router.send = AsyncMock(return_value={"status": "ok", "data": {}})
    router.websocket = MagicMock()

    # 模拟 websocket.listen 是一个耗时的异步操作
    async def mock_listen():
        try:
            # 模拟持续监听，直到被取消
            while True:
                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            pass

    router.websocket.listen = AsyncMock(side_effect=mock_listen)

    services.message_router = router
    return services


@pytest.fixture
def manager(mock_services, event_bus):
    """LifecycleManager 实例"""
    registry = MagicMock(spec=EventRegistry)

    # Patch Config 防止读取真实配置文件
    with patch("ncatbot.core.client.lifecycle.ncatbot_config") as mock_cfg:
        mock_cfg.debug = True
        # 模拟插件配置路径
        mock_cfg.plugin.plugins_dir = "plugins"

        manager = LifecycleManager(mock_services, event_bus, registry)
        yield manager

        # Teardown: 确保测试后关闭
        if manager._running:
            # 这里不使用 await manager.shutdown() 避免 loop 关闭问题，手动清理
            manager._running = False


# ======================= Tests =======================


class TestLifecycleValidation:
    """测试参数验证阶段"""

    def test_invalid_args(self, manager: LifecycleManager):
        """测试传入非法参数抛出异常"""
        # _prepare_startup 是同步方法，但在 run_backend_async 中被调用
        # 我们直接测试 run 接口的参数校验逻辑
        with pytest.raises(NcatBotError, match="非法启动参数"):
            # 使用 asyncio.run 来运行 async 方法，确保异常能抛出
            asyncio.run(manager.run_backend_async(invalid_param=1))

    def test_config_update(self, manager: LifecycleManager):
        """测试合法参数更新配置"""
        with (
            patch("ncatbot.core.client.lifecycle.ncatbot_config") as mock_cfg,
            patch("ncatbot.core.client.lifecycle.launch_napcat_service"),
            patch("ncatbot.plugin_system.PluginLoader"),
        ):
            manager._prepare_startup(bt_uin="123456", mock=True)
            mock_cfg.update_value.assert_any_call("bt_uin", "123456")


class TestLifecycleAsyncFlow:
    """测试核心异步流程 (run_backend_async)"""

    @pytest.mark.asyncio
    async def test_run_backend_success(self, manager: LifecycleManager):
        """测试标准成功启动流程"""
        # 关键修正：PluginLoader 的实例方法必须是 AsyncMock
        with (
            patch("ncatbot.plugin_system.PluginLoader") as MockLoaderClass,
            patch("ncatbot.core.client.lifecycle.launch_napcat_service"),
            patch("ncatbot.core.client.lifecycle.ncatbot_config") as mock_config,
        ):
            # 配置 ncatbot_config mock
            mock_config.plugin.skip_plugin_load = False
            mock_config.plugin.plugins_dir = "/tmp/test_plugins"
            mock_config.debug = False

            # 配置 PluginLoader 实例
            mock_loader_instance = MockLoaderClass.return_value
            mock_loader_instance.load_external_plugins = AsyncMock()
            mock_loader_instance.load_builtin_plugins = AsyncMock()
            mock_loader_instance.unload_all = AsyncMock()

            # 1. 启动
            api = await manager.run_backend_async(mock=True, skip_plugin_load=False)

            # 2. 验证 API 返回
            assert isinstance(api, BotAPI)
            assert manager._running is True

            # 3. 验证调用链
            manager.services.load_all.assert_awaited_once()
            # 验证外部插件加载被调用（根据代码逻辑）
            mock_loader_instance.load_external_plugins.assert_awaited()
            mock_loader_instance.load_builtin_plugins.assert_awaited()
            # 验证 ws.listen 正在后台运行 (未完成)
            assert manager._main_task is not None
            assert not manager._main_task.done()

            # 4. 清理
            await manager.shutdown()
            assert manager._running is False
            manager.services.close_all.assert_awaited()

    @pytest.mark.asyncio
    async def test_startup_failure_service_async(self, manager: LifecycleManager):
        """测试服务加载失败导致启动终止"""
        manager.services.load_all.side_effect = Exception("Service Crash")

        # 修复：必须获取 Mock 实例并配置异步方法，防止 finally 块中的 await 报错
        with patch("ncatbot.plugin_system.PluginLoader") as MockLoaderClass:
            mock_loader = MockLoaderClass.return_value
            mock_loader.unload_all = AsyncMock()  # <--- 关键修复：让 unload_all 可等待

            # 即使这里 PluginLoader 是正常的，Service 挂了也该抛出异常
            with pytest.raises(Exception, match="Service Crash"):
                await manager.run_backend_async(mock=True)

            # 验证状态回滚
            assert manager._running is False


class TestLifecycleThreaded:
    """
    测试新增的线程启动模式 (run_backend)
    注意：请确保 LifecycleManager 已实现此方法
    """

    def test_run_in_thread_success(self, manager: LifecycleManager):
        """测试在子线程中成功启动"""
        # 必须 Mock 掉所有涉及 IO/Subprocess 的东西
        with (
            patch("ncatbot.plugin_system.PluginLoader") as MockLoader,
            patch("ncatbot.core.client.lifecycle.launch_napcat_service"),
        ):
            # 修复 PluginLoader 的 AsyncMock 问题
            instance = MockLoader.return_value
            instance.load_external_plugins = AsyncMock()
            instance.load_builtin_plugins = AsyncMock()
            instance.unload_all = AsyncMock()

            # 调用同步方法
            api = manager.run_backend(mock=True, daemon=True)

            assert isinstance(api, BotAPI)
            assert manager._running is True

            # 清理
            manager.bot_exit()

            # 给一点时间让线程退出
            import time

            for _ in range(10):
                if not manager._running:
                    break
                time.sleep(0.05)

            assert manager._running is False

    def test_run_in_thread_failure(self, manager: LifecycleManager):
        """测试子线程启动失败，异常应传播回主线程"""
        with patch("ncatbot.plugin_system.PluginLoader") as MockLoader:
            instance = MockLoader.return_value
            instance.load_builtin_plugins = AsyncMock()
            instance.unload_all = AsyncMock()
            instance.load_external_plugins = AsyncMock(
                side_effect=RuntimeError("Thread Boot Fail")
            )
            manager.services.load_all.side_effect = RuntimeError("Thread Boot Fail")
            with pytest.raises(NcatBotError) as excinfo:
                manager.run_backend(mock=True, daemon=True)
            assert "Thread Boot Fail" in str(excinfo.value)
            assert manager._running is False


class TestLifecycleShutdown:
    """测试关闭逻辑"""

    @pytest.mark.asyncio
    async def test_shutdown_idempotent(self, manager: LifecycleManager):
        """测试多次关闭是安全的"""
        manager._running = False
        await manager.shutdown()
        manager.services.close_all.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_bot_exit_trigger(self, manager: LifecycleManager):
        """测试 bot_exit 能触发后台任务取消"""
        manager._running = True

        # 创建一个模拟的长时间运行任务
        async def dummy_task():
            try:
                await asyncio.sleep(5)
            except asyncio.CancelledError:
                # 模拟任务被取消时的清理
                raise

        manager._main_task = asyncio.create_task(dummy_task())

        # 调用退出
        manager.bot_exit()

        # 关键修正：必须捕获 CancelledError
        try:
            await manager._main_task
        except asyncio.CancelledError:
            pass  # 这是预期的结果

        assert manager._main_task.cancelled() or manager._main_task.done()
