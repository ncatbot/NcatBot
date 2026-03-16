"""
__init__.py 导入入口模块导致 handler 重复注册的回归测试

规范:
  R-10: __init__.py 中 ``from .main import X`` 不导致入口模块被 exec 两次
  R-11: load_module 复用 __init__ 已导入的入口模块，pending 数量正确
"""

import sys
import textwrap
from pathlib import Path

import pytest

from ncatbot.plugin.loader.importer import ModuleImporter
from ncatbot.plugin.manifest import PluginManifest
from ncatbot.core.registry.registrar import _pending_handlers
from ncatbot.core.registry.context import set_current_plugin, _current_plugin_ctx


@pytest.fixture(autouse=True)
def clean_state():
    """清理 pending 和 sys.modules 中的测试模块。"""
    _pending_handlers.clear()
    yield
    _pending_handlers.clear()
    for key in list(sys.modules):
        if key.startswith("_test_dedup_plugin"):
            del sys.modules[key]


@pytest.fixture
def plugin_with_init(tmp_path: Path) -> PluginManifest:
    """创建一个含 __init__.py 导入入口模块的临时插件。"""
    plugin_dir = tmp_path / "_test_dedup_plugin"
    plugin_dir.mkdir()

    # __init__.py 中从 main 导入插件类 —— 这是触发 bug 的关键模式
    (plugin_dir / "__init__.py").write_text(
        "from .main import FakePlugin\n",
        encoding="utf-8",
    )

    # main.py 含装饰器注册的 handler
    (plugin_dir / "main.py").write_text(
        textwrap.dedent("""\
            from ncatbot.plugin import NcatBotPlugin
            from ncatbot.core import registrar

            class FakePlugin(NcatBotPlugin):
                name = "FakeDedup"
                version = "0.0.1"

                @registrar.on_command("hello")
                async def cmd_hello(self, event):
                    pass

                @registrar.on_command("bye")
                async def cmd_bye(self, event):
                    pass
        """),
        encoding="utf-8",
    )

    return PluginManifest(
        name="FakeDedup",
        version="0.0.1",
        main="main.py",
        entry_class="FakePlugin",
        plugin_dir=plugin_dir,
        folder_name="_test_dedup_plugin",
    )


# ---- R-10: __init__.py 导入不导致双重 exec ----


def test_init_import_no_double_exec(plugin_with_init: PluginManifest):
    """R-10: __init__.py 中 from .main import X 不导致 handler 重复注册。

    修复前: load_module 先 exec __init__.py（间接导入 main），
            再重新 exec main.py → 装饰器运行两次 → pending 中出现重复函数对象。
    修复后: load_module 发现 main 已在 sys.modules，直接复用。
    """
    importer = ModuleImporter()
    importer.add_plugin_root(plugin_with_init.plugin_dir.parent)

    token = set_current_plugin("FakeDedup")
    try:
        importer.load_module(plugin_with_init)
    finally:
        _current_plugin_ctx.reset(token)

    pending = _pending_handlers.get("FakeDedup", [])
    func_names = [f.__name__ for f in pending]

    # 每个 handler 只应出现一次
    assert func_names.count("cmd_hello") == 1, (
        f"cmd_hello 在 pending 中出现 {func_names.count('cmd_hello')} 次 (应为 1)"
    )
    assert func_names.count("cmd_bye") == 1, (
        f"cmd_bye 在 pending 中出现 {func_names.count('cmd_bye')} 次 (应为 1)"
    )
    assert len(pending) == 2


# ---- R-11: 无 __init__ 导入时行为不变 ----


def test_no_init_import_still_works(tmp_path: Path):
    """R-11: 无 __init__.py 导入入口模块时，load_module 仍正常加载。"""
    plugin_dir = tmp_path / "_test_dedup_noinit"
    plugin_dir.mkdir()

    # 空 __init__.py（不导入 main）
    (plugin_dir / "__init__.py").write_text("", encoding="utf-8")

    (plugin_dir / "main.py").write_text(
        textwrap.dedent("""\
            from ncatbot.plugin import NcatBotPlugin
            from ncatbot.core import registrar

            class SimplePlugin(NcatBotPlugin):
                name = "SimpleNoInit"
                version = "0.0.1"

                @registrar.on_command("ping")
                async def cmd_ping(self, event):
                    pass
        """),
        encoding="utf-8",
    )

    manifest = PluginManifest(
        name="SimpleNoInit",
        version="0.0.1",
        main="main.py",
        entry_class="SimplePlugin",
        plugin_dir=plugin_dir,
        folder_name="_test_dedup_noinit",
    )

    importer = ModuleImporter()
    importer.add_plugin_root(tmp_path)

    token = set_current_plugin("SimpleNoInit")
    try:
        module = importer.load_module(manifest)
    finally:
        _current_plugin_ctx.reset(token)

    pending = _pending_handlers.get("SimpleNoInit", [])
    assert len(pending) == 1
    assert pending[0].__name__ == "cmd_ping"
    assert hasattr(module, "SimplePlugin")

    # 清理
    for key in list(sys.modules):
        if key.startswith("_test_dedup_noinit"):
            del sys.modules[key]
