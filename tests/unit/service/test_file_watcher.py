"""FileWatcherService 行为测试。

规范: FW-01 — 插件目录变更检测与 effective_hot_reload 对齐（独立于 debug）
"""

import pytest

from ncatbot.service.builtin.file_watcher.service import FileWatcherService
from ncatbot.utils.config.manager import get_config_manager


@pytest.fixture(autouse=True)
def reset_config_singleton(monkeypatch):
    import ncatbot.utils.config.manager as mm

    mm._default_manager = None
    yield
    mm._default_manager = None


def test_on_file_changed_queues_when_hot_reload_true_debug_false(tmp_path, monkeypatch):
    """FW-01a: hot_reload 开启且 debug 关闭时仍记录待处理插件目录"""
    cfg = tmp_path / "c.yaml"
    cfg.write_text(
        "debug: false\nplugin:\n  plugins_dir: plugins\n  hot_reload: true\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("NCATBOT_CONFIG_PATH", str(cfg))

    mgr = get_config_manager(str(cfg))
    assert mgr.effective_debug is False
    assert mgr.effective_hot_reload() is True

    plugin_root = tmp_path / "plugins"
    (plugin_root / "myplugin").mkdir(parents=True)
    py_path = plugin_root / "myplugin" / "x.py"
    py_path.write_text("# x", encoding="utf-8")

    fw = FileWatcherService()
    fw._on_file_changed(str(py_path), str(plugin_root))
    assert fw.pending_count == 1


def test_on_file_changed_skips_when_hot_reload_false(tmp_path, monkeypatch):
    """FW-01b: hot_reload 关闭时不记录插件变更"""
    cfg = tmp_path / "c.yaml"
    cfg.write_text(
        "debug: true\nplugin:\n  plugins_dir: plugins\n  hot_reload: false\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("NCATBOT_CONFIG_PATH", str(cfg))

    mgr = get_config_manager(str(cfg))
    assert mgr.effective_debug is True
    assert mgr.effective_hot_reload() is False

    plugin_root = tmp_path / "plugins"
    (plugin_root / "myplugin").mkdir(parents=True)
    py_path = plugin_root / "myplugin" / "x.py"
    py_path.write_text("# x", encoding="utf-8")

    fw = FileWatcherService()
    fw._on_file_changed(str(py_path), str(plugin_root))
    assert fw.pending_count == 0
