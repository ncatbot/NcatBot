"""
热重载端到端测试

测试 FileWatcherService 检测文件变化并触发插件重载的完整流程。
"""

import pytest
import asyncio

from ncatbot.utils.testing import E2ETestSuite
from .conftest import get_plugin_class, modify_plugin_file, WAIT_TIME



# 用于修改插件文件的替换规则
MODIFICATIONS = {
    'MARKER_VALUE: str = "original"': 'MARKER_VALUE: str = "modified"',
    'version = "1.0.0"': 'version = "1.0.1"',
}


class TestFileWatcherService:
    """FileWatcherService 基础功能测试"""

    @pytest.mark.asyncio
    async def test_service_is_running(self, test_suite: E2ETestSuite):
        """测试文件监视服务正在运行"""
        file_watcher = test_suite.services.file_watcher
        assert file_watcher is not None
        assert file_watcher.is_watching

    @pytest.mark.asyncio
    async def test_service_has_callback_set(self, test_suite: E2ETestSuite):
        """测试服务已设置回调（由 SystemManager 设置）"""
        file_watcher = test_suite.services.file_watcher
        assert file_watcher._reload_callback is not None


class TestPluginHotReload:
    """插件热重载测试"""

    @pytest.mark.asyncio
    async def test_initial_plugin_load(self, test_suite: E2ETestSuite, plugin_file):
        """测试插件初始加载"""
        plugin = await test_suite.register_plugin("reload_test_plugin")
        assert plugin is not None
        assert plugin.name == "reload_test_plugin"
        
        PluginClass = test_suite.client.get_plugin_class_by_name("reload_test_plugin")
        assert PluginClass is not None
        assert PluginClass.MARKER_VALUE == "original"
        assert PluginClass.load_count == 1

    @pytest.mark.asyncio
    async def test_file_modification_triggers_reload(self, test_suite: E2ETestSuite, plugin_file):
        """测试文件修改触发热重载"""
        # 1. 加载插件
        plugin = await test_suite.register_plugin("reload_test_plugin")
        assert plugin is not None
        
        PluginClass = test_suite.client.get_plugin_class_by_name("reload_test_plugin")
        assert PluginClass.MARKER_VALUE == "original"
        
        # 2. 修改插件文件
        modify_plugin_file(plugin_file, MODIFICATIONS)
        
        # 3. 等待自动热重载
        await asyncio.sleep(WAIT_TIME)
        
        # 4. 验证插件被重载
        PluginClass = test_suite.client.get_plugin_class_by_name("reload_test_plugin")
        assert PluginClass is not None
        assert PluginClass.MARKER_VALUE == "modified"

    @pytest.mark.asyncio
    async def test_reload_preserves_functionality(self, test_suite: E2ETestSuite, plugin_file):
        """测试重载后插件功能正常"""
        plugin = await test_suite.register_plugin("reload_test_plugin")
        assert plugin is not None
        
        PluginClass = test_suite.client.get_plugin_class_by_name("reload_test_plugin")
        assert PluginClass.get_marker() == "original"
        
        # 修改文件并等待自动重载
        modify_plugin_file(plugin_file, MODIFICATIONS)
        await asyncio.sleep(WAIT_TIME)
        
        # 重新获取插件类验证
        PluginClass = test_suite.client.get_plugin_class_by_name("reload_test_plugin")
        assert PluginClass.get_marker() == "modified"
        
        # 获取重载后的插件实例（通过名称查找）
        reloaded_plugin = None
        for p in test_suite.client.get_registered_plugins():
            if p.name == "reload_test_plugin":
                reloaded_plugin = p
                break
        assert reloaded_plugin is not None
        assert reloaded_plugin.version == "1.0.1"


class TestReloadEdgeCases:
    """热重载边缘情况测试"""

    @pytest.mark.asyncio
    async def test_rapid_modifications(self, test_suite: E2ETestSuite, plugin_file):
        """测试快速连续修改（防抖机制）"""
        plugin = await test_suite.register_plugin("reload_test_plugin")
        assert plugin is not None
        
        # 快速连续修改多次
        for i in range(3):
            modify_plugin_file(plugin_file, {
                'MARKER_VALUE: str = "original"': f'MARKER_VALUE: str = "modified_{i}"',
                f'MARKER_VALUE: str = "modified_{i-1}"': f'MARKER_VALUE: str = "modified_{i}"',
            })
        
        # 等待防抖延迟后的处理
        await asyncio.sleep(WAIT_TIME)
        
        # 验证插件被重载（加载最后一次修改的版本）
        PluginClass = test_suite.client.get_plugin_class_by_name("reload_test_plugin")
        assert "modified" in PluginClass.MARKER_VALUE

    @pytest.mark.asyncio
    async def test_file_restored_after_test(self, test_suite: E2ETestSuite, plugin_file):
        """测试完成后文件恢复正常"""
        original_content = plugin_file.read_text()
        assert 'MARKER_VALUE: str = "original"' in original_content
        
        modify_plugin_file(plugin_file, MODIFICATIONS)
        
        modified_content = plugin_file.read_text()
        assert 'MARKER_VALUE: str = "modified"' in modified_content


class TestManualReload:
    """手动触发重载测试（不依赖文件监视）"""

    @pytest.mark.asyncio
    async def test_manual_unload_and_load(self, test_suite: E2ETestSuite, plugin_file):
        """测试手动卸载和加载"""
        plugin = await test_suite.register_plugin("reload_test_plugin")
        assert plugin is not None
        
        PluginClass = test_suite.client.get_plugin_class_by_name("reload_test_plugin")
        assert PluginClass.MARKER_VALUE == "original"
        
        # 卸载插件
        await test_suite.unregister_plugin("reload_test_plugin")
        
        # 修改文件
        modify_plugin_file(plugin_file, MODIFICATIONS)
        
        # 重新加载插件
        plugin = await test_suite.register_plugin("reload_test_plugin")
        assert plugin is not None
        
        # 验证加载了新版本
        PluginClass = test_suite.client.get_plugin_class_by_name("reload_test_plugin")
        assert PluginClass.MARKER_VALUE == "modified"


# 命令响应修改规则
COMMAND_MODIFICATIONS = {
    'COMMAND_RESPONSE: str = "original_response"': 'COMMAND_RESPONSE: str = "modified_response"',
}


class TestCommandHotReload:
    """命令热重载端到端测试"""

    @pytest.mark.asyncio
    async def test_command_registered_after_load(self, test_suite: E2ETestSuite, plugin_file):
        """测试插件加载后命令被注册"""
        plugin = await test_suite.register_plugin("reload_test_plugin")
        assert plugin is not None
        
        # 发送命令并验证响应
        await test_suite.inject_group_message("/reload_test_cmd")
        
        # 检查是否收到原始响应
        calls = test_suite.get_api_calls("send_group_msg")
        assert len(calls) >= 1
        last_call = calls[-1]
        assert "original_response" in str(last_call.get("message", ""))

    @pytest.mark.asyncio
    async def test_command_unregistered_after_unload(self, test_suite: E2ETestSuite, plugin_file):
        """测试插件卸载后命令不再响应"""
        # 加载插件
        plugin = await test_suite.register_plugin("reload_test_plugin")
        assert plugin is not None
        
        # 清空 API 调用历史
        test_suite.clear_call_history()
        
        # 卸载插件
        await test_suite.unregister_plugin("reload_test_plugin")
        
        # 发送命令
        await test_suite.inject_group_message("/reload_test_cmd")
        
        # 验证命令无响应（没有 send_group_msg 调用）
        calls = test_suite.get_api_calls("send_group_msg")
        # 如果有调用，确保不是我们的命令响应
        for call in calls:
            msg = str(call.get("message", ""))
            assert "original_response" not in msg
            assert "modified_response" not in msg

    @pytest.mark.asyncio
    async def test_command_response_updated_after_reload(self, test_suite: E2ETestSuite, plugin_file):
        """测试热重载后命令使用新的响应内容"""
        # 1. 加载插件，验证原始响应
        plugin = await test_suite.register_plugin("reload_test_plugin")
        assert plugin is not None
        
        await test_suite.inject_group_message("/reload_test_cmd")
        calls = test_suite.get_api_calls("send_group_msg")
        assert len(calls) >= 1
        assert "original_response" in str(calls[-1].get("message", ""))
        
        # 2. 清空历史，修改文件
        test_suite.clear_call_history()
        modify_plugin_file(plugin_file, COMMAND_MODIFICATIONS)
        
        # 3. 等待自动热重载
        await asyncio.sleep(WAIT_TIME)
        
        # 4. 发送命令，验证新响应
        await test_suite.inject_group_message("/reload_test_cmd")
        calls = test_suite.get_api_calls("send_group_msg")
        assert len(calls) >= 1
        assert "modified_response" in str(calls[-1].get("message", ""))

    @pytest.mark.asyncio
    async def test_command_full_lifecycle(self, test_suite: E2ETestSuite, plugin_file):
        """测试命令的完整生命周期：加载→响应→卸载→无响应→修改→重载→新响应"""
        # 1. 加载插件
        plugin = await test_suite.register_plugin("reload_test_plugin")
        assert plugin is not None
        
        # 2. 验证命令响应
        await test_suite.inject_group_message("/reload_test_cmd")
        calls = test_suite.get_api_calls("send_group_msg")
        assert len(calls) >= 1
        assert "original_response" in str(calls[-1].get("message", ""))
        
        # 3. 卸载插件
        test_suite.clear_call_history()
        await test_suite.unregister_plugin("reload_test_plugin")
        
        # 4. 验证命令无响应
        await test_suite.inject_group_message("/reload_test_cmd")
        calls = test_suite.get_api_calls("send_group_msg")
        for call in calls:
            msg = str(call.get("message", ""))
            assert "original_response" not in msg
        
        # 5. 修改文件并重新加载
        test_suite.clear_call_history()
        modify_plugin_file(plugin_file, COMMAND_MODIFICATIONS)
        plugin = await test_suite.register_plugin("reload_test_plugin")
        assert plugin is not None
        
        # 6. 验证新的命令响应
        await test_suite.inject_group_message("/reload_test_cmd")
        calls = test_suite.get_api_calls("send_group_msg")
        assert len(calls) >= 1
        assert "modified_response" in str(calls[-1].get("message", ""))
