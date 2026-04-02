"""CLI 冒烟：--help 与真实参数绑定（mock 副作用）。

规范: CX-01 ~ CX-10（见 tests/unit/cli/README.md）
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from click.testing import CliRunner

from ncatbot.cli.main import cli
from ncatbot.utils.config.manager import MISSING


def run_help(args: list[str]):
    runner = CliRunner()
    r = runner.invoke(cli, args, catch_exceptions=False)
    assert r.exit_code == 0


def test_cli_root_help():
    """CX-01: 根命令 --help 可正常退出"""
    run_help(["--help"])


def test_cli_subcommands_help():
    """CX-02: 各一级子命令 --help 可正常退出"""
    for sub in (
        "run",
        "dev",
        "config",
        "plugin",
        "napcat",
        "init",
        "adapter",
        "ref",
    ):
        run_help([sub, "--help"])


def test_cli_napcat_diagnose_help():
    """CX-03: napcat diagnose 子组 --help 可正常退出"""
    run_help(["napcat", "diagnose", "--help"])


def test_run_invokes_bot_client_with_bound_options(tmp_path):
    """CX-04: run 解析 --debug/--no-hot-reload/--plugins-dir 并调用 BotClient（mock）"""
    pdir = str(tmp_path / "plugs")
    runner = CliRunner()
    with patch("ncatbot.app.BotClient") as mock_bc:
        mock_bc.return_value.run = MagicMock()
        r = runner.invoke(
            cli,
            [
                "run",
                "--debug",
                "--no-hot-reload",
                "--plugins-dir",
                pdir,
                "--bot-uin",
                "9999999",
            ],
            catch_exceptions=False,
        )
    assert r.exit_code == 0
    mock_bc.assert_called_once()
    _, kwargs = mock_bc.call_args
    assert kwargs["debug"] is True
    assert kwargs["plugins_dir"] == pdir
    assert kwargs["hot_reload"] is False
    mock_bc.return_value.run.assert_called_once()


def test_run_plugins_dir_only_passes_missing_for_debug_and_hot_reload(tmp_path):
    """CX-05: run 仅传 --plugins-dir 时 debug/hot_reload 为 MISSING"""
    pdir = str(tmp_path / "plugs")
    runner = CliRunner()
    with patch("ncatbot.app.BotClient") as mock_bc:
        mock_bc.return_value.run = MagicMock()
        r = runner.invoke(
            cli,
            ["run", "--plugins-dir", pdir, "--bot-uin", "9999999"],
            catch_exceptions=False,
        )
    assert r.exit_code == 0
    _, kwargs = mock_bc.call_args
    assert kwargs["debug"] is MISSING
    assert kwargs["plugins_dir"] == pdir
    assert kwargs["hot_reload"] is MISSING


def test_dev_invokes_bot_client(tmp_path):
    """CX-06: dev 绑定参数并调用 BotClient（mock）"""
    pdir = str(tmp_path / "plugs")
    runner = CliRunner()
    with patch("ncatbot.app.BotClient") as mock_bc:
        mock_bc.return_value.run = MagicMock()
        r = runner.invoke(
            cli,
            ["dev", "--plugins-dir", pdir],
            catch_exceptions=False,
        )
    assert r.exit_code == 0
    _, kwargs = mock_bc.call_args
    assert kwargs["debug"] is True
    assert kwargs["plugins_dir"] == pdir
    assert kwargs["hot_reload"] is True
    mock_bc.return_value.run.assert_called_once()


def test_run_rejects_legacy_plugins_dir_option():
    """CX-07: 已废弃的 --plugin-dir 无法解析，防止选项名回归"""
    runner = CliRunner()
    r = runner.invoke(cli, ["run", "--plugin-dir", "x"], catch_exceptions=True)
    assert r.exit_code != 0


@pytest.fixture
def reset_config_singleton():
    import ncatbot.utils.config.manager as mm

    mm._default_manager = None
    yield
    mm._default_manager = None


def test_config_show_executes_callback(tmp_path, monkeypatch, reset_config_singleton):
    """CX-08: config show 进入回调并输出配置（临时 config.yaml）"""
    cfg = tmp_path / "c.yaml"
    cfg.write_text(
        "adapters:\n  - type: napcat\n    platform: qq\n    enabled: true\n    config: {}\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("NCATBOT_CONFIG_PATH", str(cfg))
    runner = CliRunner()
    r = runner.invoke(cli, ["config", "show"], catch_exceptions=False)
    assert r.exit_code == 0
    assert "当前配置" in r.output


def test_napcat_install_yes_short_option_early_exit():
    """CX-09: napcat install -y 绑定到 skip_confirm 路径（已安装则早退）"""
    runner = CliRunner()
    mock_ops = MagicMock()
    mock_ops.is_napcat_installed.return_value = True
    with patch(
        "ncatbot.adapter.napcat.setup.platform.PlatformOps.create",
        return_value=mock_ops,
    ):
        r = runner.invoke(cli, ["napcat", "install", "-y"], catch_exceptions=False)
    assert r.exit_code == 0
    assert "已安装" in r.output or "跳过" in r.output


def test_napcat_diagnose_ws_binds_uri_token():
    """CX-10: napcat diagnose ws 将 --uri/--token 传入 check_ws（mock）"""
    runner = CliRunner()
    mock_check = AsyncMock(return_value=None)
    with patch(
        "ncatbot.adapter.napcat.debug.check_ws.check_ws",
        mock_check,
    ):
        r = runner.invoke(
            cli,
            [
                "napcat",
                "diagnose",
                "ws",
                "--uri",
                "ws://127.0.0.1:1",
                "--token",
                "tok",
            ],
            catch_exceptions=False,
        )
    assert r.exit_code == 0
    mock_check.assert_called_once()
    assert mock_check.call_args[0][0] == "ws://127.0.0.1:1"
    assert mock_check.call_args[0][1] == "tok"


def test_napcat_stop_calls_platform_ops_on_linux():
    """CX-12: napcat stop 在 Linux 下调用平台 stop 逻辑"""
    runner = CliRunner()
    mock_ops = MagicMock()
    with (
        patch("platform.system", return_value="Linux"),
        patch(
            "ncatbot.adapter.napcat.setup.platform.PlatformOps.create",
            return_value=mock_ops,
        ),
    ):
        r = runner.invoke(cli, ["napcat", "stop"], catch_exceptions=False)

    assert r.exit_code == 0
    mock_ops.stop_napcat.assert_called_once()
    assert "NapCat 已停止" in r.output


def test_napcat_stop_rejects_non_linux():
    """CX-13: napcat stop 在非 Linux 平台拒绝执行"""
    runner = CliRunner()
    with patch("platform.system", return_value="Windows"):
        r = runner.invoke(cli, ["napcat", "stop"], catch_exceptions=False)

    assert r.exit_code == 1
    assert "仅支持 Linux" in r.output


def test_ref_downloads_and_extracts(tmp_path):
    """CX-11: ref --vscode 从 Release 下载并解压 user-reference.zip（mock 网络）"""
    import io
    import zipfile as zf

    # 构造一个内存 zip 包含一个测试文件
    buf = io.BytesIO()
    with zf.ZipFile(buf, "w") as z:
        z.writestr("docs/test.md", "hello")
    zip_bytes = buf.getvalue()

    fake_release = {
        "tag_name": "v0.0.1",
        "assets": [
            {
                "name": "ncatbot5-0.0.1-user-reference.zip",
                "browser_download_url": "https://github.com/fake/download.zip",
            }
        ],
    }

    class FakeResponse:
        status_code = 200

        def json(self):
            return fake_release

        def raise_for_status(self):
            pass

    def fake_download(url, file_name):
        """写入预构建的 zip 文件。"""
        with open(file_name, "wb") as f:
            f.write(zip_bytes)

    runner = CliRunner()
    with (
        patch("ncatbot.cli.commands.ref.httpx.get", return_value=FakeResponse()),
        patch("ncatbot.utils.network.download_file", fake_download),
        patch("ncatbot.utils.download_file", fake_download),
    ):
        r = runner.invoke(
            cli,
            ["ref", "--dir", str(tmp_path), "--no-proxy", "--vscode"],
            catch_exceptions=False,
        )
    assert r.exit_code == 0
    assert (tmp_path / "docs" / "test.md").exists()
    assert (tmp_path / "docs" / "test.md").read_text() == "hello"
