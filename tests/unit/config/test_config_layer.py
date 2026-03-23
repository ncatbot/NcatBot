"""分层解析、合并保存与运行时覆盖。

规范: CE-01 ~ CE-05（见 tests/unit/config/README.md）
"""

import pytest
import yaml

from ncatbot.utils.config.manager import get_config_manager
from ncatbot.utils.config.storage import ConfigStorage


@pytest.fixture(autouse=True)
def reset_config_singleton(monkeypatch):
    """每个用例前重置全局 ConfigManager。"""
    import ncatbot.utils.config.manager as mm

    mm._default_manager = None
    yield
    mm._default_manager = None


def test_yaml_wins_over_env(tmp_path, monkeypatch):
    """CE-01: yaml 中已存在 bot_uin 时优先于 NCATBOT_BOT_UIN"""
    p = tmp_path / "c.yaml"
    p.write_text("bot_uin: '111111'\n", encoding="utf-8")
    monkeypatch.setenv("NCATBOT_BOT_UIN", "222222")
    monkeypatch.setenv("NCATBOT_CONFIG_PATH", str(p))

    st = ConfigStorage(str(p))
    cfg = st.load()
    assert cfg.bot_uin == "111111"
    assert st._env_only_bot_uin is False


def test_env_bot_uin_when_key_absent(tmp_path, monkeypatch):
    """CE-02: yaml 未写 bot_uin 时从 NCATBOT_BOT_UIN 解析并标记 env-only"""
    p = tmp_path / "c.yaml"
    p.write_text("{}", encoding="utf-8")
    monkeypatch.setenv("NCATBOT_BOT_UIN", "777888")
    monkeypatch.setenv("NCATBOT_CONFIG_PATH", str(p))

    st = ConfigStorage(str(p))
    cfg = st.load()
    assert cfg.bot_uin == "777888"
    assert st._env_only_bot_uin is True


def test_save_does_not_persist_env_only_bot_uin(tmp_path, monkeypatch):
    """CE-03: save 合并写盘时不将仅来自 env 的 bot_uin 写入 yaml"""
    p = tmp_path / "c.yaml"
    p.write_text(
        "adapters:\n  - type: napcat\n    platform: qq\n    enabled: true\n    config: {}\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("NCATBOT_BOT_UIN", "999888")
    monkeypatch.setenv("NCATBOT_CONFIG_PATH", str(p))

    mgr = get_config_manager(str(p))
    assert mgr.config.bot_uin == "999888"
    mgr.save()

    raw = yaml.safe_load(p.read_text(encoding="utf-8"))
    assert "bot_uin" not in raw


def test_runtime_overrides_effective(tmp_path, monkeypatch):
    """CE-04: apply_runtime_overrides 影响 effective_*，clear 后恢复持久化配置"""
    p = tmp_path / "c.yaml"
    p.write_text(
        "debug: false\nplugin:\n  plugins_dir: plugins\n  hot_reload: true\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("NCATBOT_CONFIG_PATH", str(p))

    mgr = get_config_manager(str(p))
    assert mgr.effective_debug is False
    mgr.apply_runtime_overrides(debug=True, plugins_dir="custom", hot_reload=False)
    assert mgr.effective_debug is True
    assert mgr.effective_plugins_dir() == "custom"
    assert mgr.effective_hot_reload() is False
    mgr.clear_runtime_overrides()
    assert mgr.effective_debug is False


def test_update_value_persists_bot_uin_after_env(tmp_path, monkeypatch):
    """CE-05: update_value 写入 bot_uin 后 save 可将该值持久化到 yaml"""
    p = tmp_path / "c.yaml"
    p.write_text("{}", encoding="utf-8")
    monkeypatch.setenv("NCATBOT_BOT_UIN", "111")
    monkeypatch.setenv("NCATBOT_CONFIG_PATH", str(p))

    mgr = get_config_manager(str(p))
    assert mgr.config.bot_uin == "111"
    assert mgr._storage._env_only_bot_uin is True
    mgr.update_value("bot_uin", "222")
    mgr.save()
    raw = yaml.safe_load(p.read_text(encoding="utf-8"))
    assert raw.get("bot_uin") == "222"
