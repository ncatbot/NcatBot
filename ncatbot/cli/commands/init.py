"""init 命令 — 初始化项目结构。"""

import getpass
import re
from pathlib import Path
from typing import Any, Dict, List

import click
import yaml

from ..utils.colors import success, warning, info
from .adapter import adapter_interactive, _print_summary


# ---------------------------------------------------------------------------
# init 命令入口
# ---------------------------------------------------------------------------


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

    bot_uin = click.prompt(
        "请输入机器人 QQ 号（如不适用可留空）", default="", show_default=False
    )
    root = click.prompt(
        "请输入管理员 QQ 号（如不适用可留空）", default="", show_default=False
    )

    adapters = adapter_interactive(default_first=True)
    _print_summary(adapters)

    config_data: Dict[str, Any] = {
        "bot_uin": bot_uin,
        "root": root,
        "debug": False,
        "adapters": adapters,
        "plugin": {
            "plugins_dir": "plugins",
            "load_plugin": True,
            "plugin_whitelist": [],
            "plugin_blacklist": [],
        },
    }

    target.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(
            config_data,
            f,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False,
        )

    click.echo(success(f"\nconfig.yaml 已创建: {config_path}"))
    _ensure_plugins_dir(plugins_path)
    _generate_template_plugin(plugins_path, adapters)
    click.echo()
    click.echo(info("下一步: 运行 'ncatbot run' 启动机器人"))


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


def _to_class_name(plugin_name: str) -> str:
    """从插件名（合法标识符）派生入口类名。

    生成 CamelCase 名称并以 Plugin 结尾，保证结果始终是合法的 Python 标识符
    （数字开头时前置下划线），避免数字开头的用户名生成非法类名。
    """
    camel = "".join(part.capitalize() for part in plugin_name.split("_") if part)
    if not camel.endswith("Plugin"):
        camel += "Plugin"
    if not camel or camel[0].isdigit():
        camel = "_" + camel
    return camel


# ---------------------------------------------------------------------------
# 各平台模板插件内容
# ---------------------------------------------------------------------------

_PLUGIN_TEMPLATES: Dict[str, Dict[str, str]] = {
    "qq": {
        "description": "NcatBot 模板插件 — 发送 hello 回复 hi (QQ)",
        "code": """\
\"\"\"模板插件 — 发送 hello 回复 hi (QQ)。\"\"\"

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
""",
    },
    "bilibili": {
        "description": "NcatBot 模板插件 — Bilibili 弹幕回复",
        "code": """\
\"\"\"模板插件 — Bilibili 弹幕回复。\"\"\"

from ncatbot.plugin import NcatBotPlugin
from ncatbot.core import registrar
from ncatbot.event.bilibili import LiveDanmakuEvent


class {class_name}(NcatBotPlugin):

    async def on_load(self):
        self.logger.info(f"{{self.name}} 已加载")

    async def on_close(self):
        self.logger.info(f"{{self.name}} 已卸载")

    @registrar.bilibili.on_live_danmaku()
    async def on_danmaku(self, event: LiveDanmakuEvent):
        self.logger.info("收到弹幕: %s", event.content)
""",
    },
    "github": {
        "description": "NcatBot 模板插件 — GitHub 事件监听",
        "code": """\
\"\"\"模板插件 — GitHub 事件监听。\"\"\"

from ncatbot.plugin import NcatBotPlugin
from ncatbot.core import registrar
from ncatbot.event.github import GitHubPushEvent


class {class_name}(NcatBotPlugin):

    async def on_load(self):
        self.logger.info(f"{{self.name}} 已加载")

    async def on_close(self):
        self.logger.info(f"{{self.name}} 已卸载")

    @registrar.github.on_push()
    async def on_push(self, event: GitHubPushEvent):
        self.logger.info("收到 Push 事件: %s", event.repo)
""",
    },
    "ai": {
        "description": "NcatBot 模板插件 — AI 对话",
        "code": """\
\"\"\"模板插件 — AI 对话。

前置配置（config.yaml）:
  adapters:
    - type: ai
      config:
        api_key: "sk-xxxx"
        base_url: "https://api.openai.com/v1"   # 可选，兼容国内 LLM
        completion_model: "gpt-4"
\"\"\"

from ncatbot.plugin import NcatBotPlugin
from ncatbot.core import registrar


class {class_name}(NcatBotPlugin):

    async def on_load(self):
        self.logger.info(f"{{self.name}} 已加载")

    async def on_close(self):
        self.logger.info(f"{{self.name}} 已卸载")

    @registrar.on_command("ai对话")
    async def on_ai_chat(self, event, prompt: str):
        \"\"\"AI 对话：发送 'ai对话 你的问题' 获取 AI 回复。\"\"\"
        try:
            reply = await self.api.ai.chat_text(prompt)
        except Exception as e:
            reply = f"AI 调用失败: {{e}}"
        await event.reply(text=reply)
""",
    },
    "lark": {
        "description": "NcatBot 模板插件 — 飞书消息回复",
        "code": """\
\"\"\"模板插件 — 飞书消息回复。\"\"\"

from ncatbot.plugin import NcatBotPlugin
from ncatbot.core import registrar
from ncatbot.event.lark import LarkMessageEvent


class {class_name}(NcatBotPlugin):

    async def on_load(self):
        self.logger.info(f"{{self.name}} 已加载")

    async def on_close(self):
        self.logger.info(f"{{self.name}} 已卸载")

    @registrar.lark.on_message()
    async def on_message(self, event: LarkMessageEvent):
        self.logger.info("收到飞书消息: %s", event.text)
""",
    },
}


def _generate_template_plugin(
    plugins_path: Path, adapters: List[Dict[str, Any]] | None = None
):
    """在 plugins/ 下生成以当前用户名命名的模板插件。"""
    username = getpass.getuser()
    plugin_name = _sanitize_plugin_name(username) + "_plugin"
    class_name = _to_class_name(plugin_name)
    plugins_dir = plugins_path / plugin_name

    if plugins_dir.exists():
        click.echo(info(f"模板插件已存在，跳过: {plugins_dir}"))
        return

    # 根据第一个适配器的平台选择模板，默认 qq
    platform = "qq"
    if adapters:
        platform = adapters[0].get("platform", "qq")
    tmpl = _PLUGIN_TEMPLATES.get(platform, _PLUGIN_TEMPLATES["qq"])

    plugins_dir.mkdir(parents=True)

    manifest_content = f"""\
name = "{plugin_name}"
version = "0.1.0"
main = "plugin.py"
author = "{username}"
description = "{tmpl["description"]}"
entry_class = "{class_name}"
pip_dependencies = []

[dependencies]
"""

    plugin_py_content = tmpl["code"].format(class_name=class_name)

    (plugins_dir / "manifest.toml").write_text(manifest_content, encoding="utf-8")
    (plugins_dir / "plugin.py").write_text(plugin_py_content, encoding="utf-8")
    click.echo(success(f"模板插件已创建: {plugins_dir}"))
