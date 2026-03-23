"""
插件 E2E 自动化测试 — 公共 fixtures

提供 PluginTestHarness 工厂 fixture，用于离线加载 examples/ 下的示例插件。
"""

from __future__ import annotations

from pathlib import Path
from typing import List

import pytest
import pytest_asyncio

from ncatbot.testing import PluginTestHarness

# examples/ 目录（相对于项目根目录）
EXAMPLES_DIR = Path(__file__).resolve().parents[3] / "docs" / "docs" / "examples"


@pytest_asyncio.fixture
async def example_harness(request):
    """工厂 fixture：根据 marker 自动创建 PluginTestHarness。

    使用方式::

        @pytest.mark.plugin_names(["hello_world"])
        @pytest.mark.plugins_dir("01_hello_world")
        async def test_xxx(example_harness):
            ...

    也可直接传参使用 make_harness 内部函数。
    """
    # 从 marker 中读取配置
    names_marker = request.node.get_closest_marker("plugin_names")
    dir_marker = request.node.get_closest_marker("plugins_dir")

    if names_marker is None or dir_marker is None:
        pytest.skip("需要 @pytest.mark.plugin_names 和 @pytest.mark.plugins_dir")

    plugin_names: List[str] = names_marker.args[0]
    example_subdir: str = dir_marker.args[0]

    harness = PluginTestHarness(
        plugin_names=plugin_names,
        plugins_dir=EXAMPLES_DIR / example_subdir,
    )
    async with harness:
        yield harness


async def make_example_harness(
    plugin_names: List[str],
) -> PluginTestHarness:
    """直接创建 PluginTestHarness 的辅助函数（需手动管理生命周期）。"""
    harness = PluginTestHarness(
        plugin_names=plugin_names,
        plugins_dir=EXAMPLES_DIR,
    )
    return harness
