"""
热重载测试共享 fixtures

策略：
- 使用  让 PluginLoader 正常加载内置插件
- 在测试时临时设置 plugins_dir 避免与默认目录冲突
- 测试手动 index 和 load 测试插件，完全控制加载流程
"""

import pytest
import pytest_asyncio
import re
import sys
from pathlib import Path
from typing import Dict, Optional, TYPE_CHECKING

from ncatbot.utils.testing import E2ETestSuite
from ncatbot.utils import ncatbot_config
from ncatbot.core.service.builtin.unified_registry import command_registry

if TYPE_CHECKING:
    from ncatbot.utils.testing import E2ETestSuite

# 测试插件目录
FIXTURES_DIR = Path(__file__).parent / "fixtures"
PLUGINS_DIR = FIXTURES_DIR / "plugins"
RELOAD_PLUGIN_DIR = PLUGINS_DIR / "reload_test_plugin"
RELOAD_PLUGIN_MAIN = RELOAD_PLUGIN_DIR / "main.py"

# 原始文件内容的快照
_ORIGINAL_CONTENT = None

# 等待热重载完成的时间（需要足够长以确保稳定）
WAIT_TIME = 0.05


def _get_original_content() -> Optional[str]:
    """获取插件文件的原始内容"""
    global _ORIGINAL_CONTENT
    if _ORIGINAL_CONTENT is None and RELOAD_PLUGIN_MAIN.exists():
        content = RELOAD_PLUGIN_MAIN.read_text()
        # 检查是否是原始状态（MARKER_VALUE 和 COMMAND_RESPONSE 都是 original）
        is_original = (
            'MARKER_VALUE: str = "original"' in content and
            'COMMAND_RESPONSE: str = "original_response"' in content
        )
        if is_original:
            _ORIGINAL_CONTENT = content
        else:
            _ORIGINAL_CONTENT = _restore_original_content(content)
    return _ORIGINAL_CONTENT


def _restore_original_content(content: str) -> str:
    """将修改后的内容还原为原始状态"""
    content = content.replace('MARKER_VALUE: str = "modified"', 'MARKER_VALUE: str = "original"')
    content = content.replace('version = "1.0.1"', 'version = "1.0.0"')
    content = re.sub(r'MARKER_VALUE: str = "modified_\d+"', 'MARKER_VALUE: str = "original"', content)
    # 还原命令响应
    content = content.replace('COMMAND_RESPONSE: str = "modified_response"', 'COMMAND_RESPONSE: str = "original_response"')
    return content


def _reset_plugin_file():
    """重置插件文件到原始状态，并重置 mtime 到当前时间"""
    import os
    import time
    
    original = _get_original_content()
    if original:
        RELOAD_PLUGIN_MAIN.write_text(original)
        # 重置 mtime 到当前时间，避免使用之前测试留下的"未来"时间
        current_time = time.time()
        os.utime(str(RELOAD_PLUGIN_MAIN), (current_time, current_time))


def get_plugin_class(plugin_name: str):
    """从已加载的模块中获取插件类"""
    for module_name, module in sys.modules.items():
        if f"ncatbot_plugin." in module_name and module_name.endswith(".main"):
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type)
                    and hasattr(attr, "name")
                    and getattr(attr, "name", None) == plugin_name
                ):
                    return attr
    return None


def modify_plugin_file(file_path: Path, replacements: Dict[str, str]) -> str:
    """修改插件文件内容
    """

    content = file_path.read_text()
    for old, new in replacements.items():
        content = content.replace(old, new)
    file_path.write_text(content)
    
    return content


# 模块导入时初始化原始内容快照
_get_original_content()


@pytest_asyncio.fixture
async def test_suite():
    """创建测试套件（每个测试完全隔离）
    
    策略：
    1. 保存原始 plugins_dir 配置
    2. 临时设置 plugins_dir 为空目录（避免自动加载测试插件）
    3. setup 后手动添加监视目录和索引插件
    4. 测试使用 register_plugin 来加载插件
    5. teardown 时恢复原始配置（在 suite.teardown 之前）
    """
    # 重置插件文件到原始状态
    _reset_plugin_file()
    
    # 保存原始配置
    original_plugins_dir = ncatbot_config.plugin.plugins_dir
    
    # 设置为不存在的空目录，避免自动加载
    ncatbot_config.plugin.plugins_dir = str(FIXTURES_DIR / "empty_plugins")
    
    suite = E2ETestSuite()
    await suite.setup()
    
    # 暂停 watcher，防止检测到初始化阶段的文件操作
    file_watcher = suite.services.file_watcher
    file_watcher.pause()
    
    # 确保监视测试插件目录
    file_watcher.add_watch_dir(str(PLUGINS_DIR))
    
    # 索引测试插件（不会自动加载）
    suite.index_plugin(str(RELOAD_PLUGIN_DIR))
    
    # 重置插件文件的 mtime（在 FileWatcher 恢复之前）
    # 确保 mtime 不是"未来"时间，并清除可能已经被缓存的值
    import os
    import time
    import asyncio
    
    current_time = time.time()
    os.utime(str(RELOAD_PLUGIN_MAIN), (current_time, current_time))
    
    # 清除 FileWatcher 的文件缓存，确保下次扫描会重新读取 mtime
    file_watcher._file_cache.clear()
    file_watcher._first_scan_done = False
    
    # 等待初始扫描完成，清空 pending 队列，然后恢复
    with file_watcher._pending_lock:
        file_watcher._pending_dirs.clear()
    file_watcher.resume()
    
    # 等待 FileWatcher 完成首次扫描
    # 这确保了后续的 modify_plugin_file 会被检测为变化
    for _ in range(10):  # 最多等待 0.1 秒
        await asyncio.sleep(0.01)
        if file_watcher._first_scan_done:
            break
    
    yield suite
    
    # teardown 前先暂停 FileWatcher，防止触发更多热重载
    file_watcher.pause()
    
    # 等待可能正在执行的热重载回调完成
    # 因为 _trigger_reload 使用 asyncio.run 创建独立事件循环执行回调
    # 需要给它足够时间完成
    await asyncio.sleep(0.1)
    
    # 清空 pending 队列，防止后续处理
    with file_watcher._pending_lock:
        file_watcher._pending_dirs.clear()
    
    # 关键：在 teardown 之前恢复原始配置
    # 这样 PluginConfigService 保存时不会写入测试目录路径
    ncatbot_config.plugin.plugins_dir = original_plugins_dir
    
    await suite.teardown()
    
    _reset_plugin_file()


@pytest.fixture
def plugin_file():
    """提供插件文件路径"""
    return RELOAD_PLUGIN_MAIN


# ==================== 辅助函数 ====================


def check_command_registered(command_name: str) -> bool:
    """检查命令是否已注册"""
    all_commands = command_registry.get_all_commands()
    return any(command_name in path for path in all_commands.keys())


def check_alias_registered(alias_name: str) -> bool:
    """检查别名是否已注册"""
    all_aliases = command_registry.get_all_aliases()
    return any(alias_name in path for path in all_aliases.keys())


def check_config_registered(suite: "E2ETestSuite", plugin_name: str) -> bool:
    """检查插件配置是否已注册"""
    config_service = suite.services.plugin_config
    registered = config_service.get_registered_configs(plugin_name)
    return len(registered) > 0


def check_handler_registered(suite: "E2ETestSuite", plugin_name: str) -> int:
    """检查事件处理器是否已注册，返回处理器数量"""
    event_bus = suite.event_bus
    # 获取与插件关联的处理器数量
    count = 0
    # EventBus 使用 _handler_meta 存储插件元数据
    for hid, meta in event_bus._handler_meta.items():
        if meta.get("name") == plugin_name:
            count += 1
    return count


@pytest.fixture
def reset_plugin_counters():
    """重置插件计数器和插件文件"""
    # 测试前重置
    _reset_plugin_file()
    plugin_class = get_plugin_class("reload_test_plugin")
    if plugin_class and hasattr(plugin_class, "reset_counters"):
        plugin_class.reset_counters()
    
    yield
    
    # 测试后重置
    _reset_plugin_file()
    plugin_class = get_plugin_class("reload_test_plugin")
    if plugin_class and hasattr(plugin_class, "reset_counters"):
        plugin_class.reset_counters()
