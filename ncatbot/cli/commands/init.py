"""init 命令 — 初始化项目结构。"""

import getpass
import re
from pathlib import Path

import click
import yaml

from ..utils.colors import success, warning, info


@click.command()
@click.option("--dir", "target_dir", default=".", help="目标目录")
def init(target_dir: str):
    """初始化 NcatBot 项目（创建 config.yaml + plugins/ + 模板插件）"""
    target = Path(target_dir).resolve()
    config_path = target / "config.yaml"
    plugins_path = target / "plugins"

    if config_path.exists():
        click.echo(warning(f"config.yaml 已存在: {config_path}"))
        if not click.confirm("是否覆盖?"):
            click.echo(info("已跳过 config.yaml"))
            _ensure_plugins_dir(plugins_path)
            _generate_template_plugin(plugins_path)
            return

    bot_uin = click.prompt("请输入机器人 QQ 号", type=str)
    root = click.prompt("请输入管理员 QQ 号", type=str)

    config_data = _build_default_config(bot_uin=bot_uin, root=root)

    target.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(
            config_data,
            f,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False,
        )

    click.echo(success(f"config.yaml 已创建: {config_path}"))
    _ensure_plugins_dir(plugins_path)
    _generate_template_plugin(plugins_path)
    click.echo()
    click.echo(info("下一步: 运行 'ncatbot run' 启动机器人"))


def _build_default_config(bot_uin: str, root: str) -> dict:
    """构建 init 命令的默认配置（新 adapters 结构）。"""
    return {
        "adapters": [
            {
                "config": {
                    "enable_webui": True,
                    "webui_token": "napcat_webui",
                    "webui_uri": "http://localhost:6099",
                    "ws_token": "napcat_ws",
                    "ws_uri": "ws://localhost:3001",
                },
                "enabled": True,
                "platform": "qq",
                "type": "napcat",
            }
        ],
        "bot_uin": bot_uin,
        "check_ncatbot_update": True,
        "debug": False,
        "enable_webui_interaction": True,
        "logging": {
            "event_log_levels": {
                "meta_event": "NONE",
            }
        },
        "plugin": {
            "auto_install_pip_deps": True,
            "load_plugin": True,
            "plugin_blacklist": [],
            "plugin_configs": {},
            "plugin_whitelist": [],
            "plugins_dir": "plugins",
        },
        "root": root,
        "skip_ncatbot_install_check": False,
        "websocket_timeout": 15,
    }


def _ensure_plugins_dir(path: Path):
    if not path.exists():
        path.mkdir(parents=True)
        click.echo(success(f"plugins/ 目录已创建: {path}"))
    else:
        click.echo(info(f"plugins/ 目录已存在: {path}"))


def _sanitize_plugin_name(name: str) -> str:
    """将用户名转换为合法的 Python 标识符作为插件名。"""
    sanitized = re.sub(r"[^a-zA-Z0-9_]", "_", name)
    if sanitized and sanitized[0].isdigit():
        sanitized = "_" + sanitized
    return sanitized or "my_plugin"


def _generate_template_plugin(plugins_path: Path):
    """在 plugins/ 下生成以当前用户名命名的模板插件。"""
    username = getpass.getuser()
    plugin_name = _sanitize_plugin_name(username) + "_plugin"
    class_name = plugin_name.title().replace("_", "") + "Plugin"
    plugin_dir = plugins_path / plugin_name

    if plugin_dir.exists():
        click.echo(info(f"模板插件已存在，跳过: {plugin_dir}"))
        return

    plugin_dir.mkdir(parents=True)

    manifest_content = f"""\
name = "{plugin_name}"
version = "0.1.0"
main = "plugin.py"
author = "{username}"
description = "NcatBot 模板插件 — 发送 hello 回复 hi"
entry_class = "{class_name}"
pip_dependencies = []

[dependencies]
"""

    plugin_py_content = f"""\
\"\"\"模板插件 — 发送 hello 回复 hi。\"\"\"

from ncatbot.plugin import NcatBotPlugin
from ncatbot.core import registrar
from ncatbot.event.qq import GroupMessageEvent, PrivateMessageEvent


class {class_name}(NcatBotPlugin):

    async def on_load(self):
        self.logger.info(f"{{self.name}} 已加载")

    async def on_close(self):
        self.logger.info(f"{{self.name}} 已卸载")

    @registrar.qq.on_group_command("hello", ignore_case=True)
    async def on_group_hello(self, event: GroupMessageEvent):
        await event.reply(text="hi")

    @registrar.on_private_command("hello", ignore_case=True)
    async def on_private_hello(self, event: PrivateMessageEvent):
        await event.reply(text="hi")
"""

    (plugin_dir / "manifest.toml").write_text(manifest_content, encoding="utf-8")
    (plugin_dir / "plugin.py").write_text(plugin_py_content, encoding="utf-8")
    click.echo(success(f"模板插件已创建: {plugin_dir}"))
