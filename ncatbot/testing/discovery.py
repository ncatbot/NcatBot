"""
插件测试自动发现

扫描插件目录，自动发现可测试的插件并生成冒烟测试代码。
"""

from __future__ import annotations

from pathlib import Path
from typing import List

from ncatbot.plugin import PluginManifest
from ncatbot.utils import get_log

LOG = get_log("PluginDiscovery")


def discover_testable_plugins(plugins_dir: Path) -> List[PluginManifest]:
    """扫描目录下所有包含 manifest.toml 的插件。

    Args:
        plugins_dir: 插件根目录

    Returns:
        可测试的 PluginManifest 列表
    """
    plugins_dir = Path(plugins_dir).resolve()
    manifests = []

    if not plugins_dir.is_dir():
        LOG.warning("插件目录不存在: %s", plugins_dir)
        return manifests

    for entry in plugins_dir.iterdir():
        if not entry.is_dir():
            continue
        manifest_path = entry / "manifest.toml"
        if not manifest_path.exists():
            continue
        try:
            manifest = PluginManifest.from_toml(manifest_path)
            manifests.append(manifest)
        except Exception as e:
            LOG.warning("跳过 %s: %s", entry.name, e)

    return manifests


def generate_smoke_test(manifest: PluginManifest) -> str:
    """为单个插件生成冒烟测试代码。

    冒烟测试验证:
    - 插件可正常加载
    - 插件可正常卸载
    - 注入基础群消息不崩溃

    Args:
        manifest: 插件清单

    Returns:
        pytest 测试代码字符串
    """
    name = manifest.name
    return f'''"""
{name} 冒烟测试（自动生成）
"""

import pytest
from ncatbot.testing import PluginTestHarness, group_message

pytestmark = pytest.mark.asyncio


async def test_{name}_loads(plugins_dir):
    """冒烟: {name} 加载成功"""
    async with PluginTestHarness(
        plugin_names=["{name}"], plugins_dir=plugins_dir
    ) as h:
        assert "{name}" in h.loaded_plugins


async def test_{name}_unloads(plugins_dir):
    """冒烟: {name} 卸载成功"""
    h = PluginTestHarness(
        plugin_names=["{name}"], plugins_dir=plugins_dir
    )
    await h.start()
    assert "{name}" in h.loaded_plugins

    await h.bot.plugin_loader.unload_plugin("{name}")
    assert "{name}" not in h.loaded_plugins

    await h.stop()


async def test_{name}_survives_event(plugins_dir):
    """冒烟: {name} 收到群消息不崩溃"""
    async with PluginTestHarness(
        plugin_names=["{name}"], plugins_dir=plugins_dir
    ) as h:
        await h.inject(group_message("test", group_id="1", user_id="1"))
        await h.settle(0.1)
'''


def generate_smoke_tests(manifests: List[PluginManifest]) -> str:
    """为多个插件批量生成冒烟测试代码。

    Args:
        manifests: 插件清单列表

    Returns:
        完整的 pytest 文件代码
    """
    header = '''"""
插件冒烟测试（自动生成）

验证所有已发现的插件可正常加载/卸载/处理事件。
"""

import pytest
from pathlib import Path
from ncatbot.testing import PluginTestHarness, group_message

pytestmark = pytest.mark.asyncio


@pytest.fixture
def plugins_dir():
    """由调用者提供的插件根目录"""
    raise NotImplementedError("请在 conftest.py 中覆盖此 fixture")

'''

    tests = []
    for m in manifests:
        tests.append(generate_smoke_test(m))

    return header + "\n".join(tests)
