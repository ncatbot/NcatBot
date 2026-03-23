"""内置 SystemManagerPlugin 的 ``!`` 命令：权限与配置门控。"""

import pytest

import ncatbot.utils.config.manager as config_manager_mod
from ncatbot.core.registry.registrar import _pending_handlers
from ncatbot.testing import PluginTestHarness
from ncatbot.testing.factory import group_message, private_message
from ncatbot.utils.config.manager import get_config_manager


@pytest.fixture(autouse=True)
def reset_config_singleton(monkeypatch):
    config_manager_mod._default_manager = None
    yield
    config_manager_mod._default_manager = None


@pytest.fixture(autouse=True)
def clean_pending():
    _pending_handlers.clear()
    yield
    _pending_handlers.clear()


def _minimal_config(tmp_path, monkeypatch) -> None:
    p = tmp_path / "cfg.yaml"
    p.write_text(
        "bot_uin: '111111'\n"
        "root: '10001'\n"
        "adapters:\n"
        "  - type: napcat\n"
        "    platform: qq\n"
        "    enabled: true\n"
        "    config: {}\n"
        "plugin:\n"
        "  enable_builtin_commands: true\n"
        "  builtin_commands_group_allowed: false\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("NCATBOT_CONFIG_PATH", str(p))


@pytest.mark.asyncio
async def test_sysinfo_private_root_replies(tmp_path, monkeypatch):
    _minimal_config(tmp_path, monkeypatch)
    get_config_manager(str(tmp_path / "cfg.yaml"))

    h = PluginTestHarness([], tmp_path, skip_builtin=False)
    await h.start()
    try:
        await h.inject(private_message("!sysinfo", user_id="10001"))
        await h.settle(0.15)
        assert h.mock_api.called("send_private_msg")
        calls = h.mock_api.get_calls("send_private_msg")
        assert calls
        text = str(calls[-1].args)
        assert "NcatBot" in text or "ncatbot" in text.lower()
    finally:
        await h.stop()


@pytest.mark.asyncio
async def test_sysinfo_denied_non_root(tmp_path, monkeypatch):
    _minimal_config(tmp_path, monkeypatch)
    get_config_manager(str(tmp_path / "cfg.yaml"))

    h = PluginTestHarness([], tmp_path, skip_builtin=False)
    await h.start()
    try:
        h.mock_api.reset()
        await h.inject(private_message("!sysinfo", user_id="99999"))
        await h.settle(0.15)
        assert h.mock_api.called("send_private_msg")
        text = str(h.mock_api.get_calls("send_private_msg")[-1].args)
        assert "无权" in text
    finally:
        await h.stop()


@pytest.mark.asyncio
async def test_sysinfo_denied_in_group_when_not_allowed(tmp_path, monkeypatch):
    _minimal_config(tmp_path, monkeypatch)
    get_config_manager(str(tmp_path / "cfg.yaml"))

    h = PluginTestHarness([], tmp_path, skip_builtin=False)
    await h.start()
    try:
        h.mock_api.reset()
        await h.inject(group_message("!sysinfo", user_id="10001", group_id="1"))
        await h.settle(0.15)
        assert h.mock_api.called("send_group_msg")
        text = str(h.mock_api.get_calls("send_group_msg")[-1].args)
        assert "私聊" in text
    finally:
        await h.stop()


@pytest.mark.asyncio
async def test_builtin_toggle_off_then_on(tmp_path, monkeypatch):
    _minimal_config(tmp_path, monkeypatch)
    mgr = get_config_manager(str(tmp_path / "cfg.yaml"))

    h = PluginTestHarness([], tmp_path, skip_builtin=False)
    await h.start()
    try:
        await h.inject(private_message("!builtin off", user_id="10001"))
        await h.settle(0.15)
        assert mgr.config.plugin.enable_builtin_commands is False

        await h.inject(private_message("!sysinfo", user_id="10001"))
        await h.settle(0.15)
        calls_off = h.mock_api.get_calls("send_private_msg")
        assert "关闭" in str(calls_off[-1].args) or "关闭" in str(calls_off[-1])

        await h.inject(private_message("!builtin on", user_id="10001"))
        await h.settle(0.15)
        assert mgr.config.plugin.enable_builtin_commands is True

        h.mock_api.reset()
        await h.inject(private_message("!sysinfo", user_id="10001"))
        await h.settle(0.15)
        assert h.mock_api.called("send_private_msg")
        ok_text = str(h.mock_api.get_calls("send_private_msg")[-1].args)
        assert "NcatBot" in ok_text or "Python" in ok_text
    finally:
        await h.stop()


def test_plugin_config_defaults():
    from ncatbot.utils.config.models import PluginConfig

    p = PluginConfig()
    assert p.enable_builtin_commands is True
    assert p.builtin_commands.reload is True
    assert p.builtin_commands_group_allowed is False
