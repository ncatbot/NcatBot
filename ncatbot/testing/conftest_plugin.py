"""
pytest 插件 — 自动发现并参数化插件冒烟测试

用法: 在 conftest.py 中导入此模块，或通过 pytest --plugins-dir=docs/docs/examples/ 使用。

功能:
  - @pytest.mark.plugin(name="xxx") marker 支持
  - --plugins-dir CLI 选项
  - 自动参数化冒烟测试
"""

from __future__ import annotations

from pathlib import Path
from typing import List

import pytest

from .discovery import discover_testable_plugins


def pytest_addoption(parser):
    """注册 --plugins-dir 命令行选项"""
    parser.addoption(
        "--plugins-dir",
        action="store",
        default=None,
        help="插件根目录路径（用于自动发现插件冒烟测试）",
    )


def pytest_configure(config):
    """注册自定义 marker"""
    config.addinivalue_line(
        "markers",
        "plugin(name): 标记为特定插件的测试",
    )
    config.addinivalue_line(
        "markers",
        "plugin_names(names): 指定要加载的插件名列表",
    )
    config.addinivalue_line(
        "markers",
        "plugins_dir(dir): 指定插件目录名",
    )


@pytest.fixture
def plugins_dir(request) -> Path:
    """从 --plugins-dir 选项获取插件根目录"""
    opt = request.config.getoption("--plugins-dir", default=None)
    if opt is None:
        pytest.skip("需要 --plugins-dir 参数")
    return Path(opt).resolve()


def pytest_collection_modifyitems(config, items):
    """根据 --plugins-dir 过滤插件测试"""
    plugins_dir_opt = config.getoption("--plugins-dir", default=None)
    if plugins_dir_opt is None:
        return

    # 如果指定了 plugins-dir，则只运行带 @pytest.mark.plugin 的测试
    # 其他测试跳过
    for item in items:
        if "plugin" not in item.keywords and "plugin_names" not in item.keywords:
            item.add_marker(pytest.mark.skip(reason="不在 --plugins-dir 测试范围内"))


def get_testable_plugin_names(plugins_dir: str) -> List[str]:
    """辅助函数：获取目录下所有可测试插件名"""
    manifests = discover_testable_plugins(Path(plugins_dir))
    return [m.name for m in manifests]
