"""run / dev 命令 — 启动 Bot。"""

import click

from ncatbot.utils.config.manager import MISSING


@click.command()
@click.option("--debug", is_flag=True, help="启用调试模式")
@click.option("--no-hot-reload", is_flag=True, help="禁用插件热重载")
@click.option(
    "--plugins-dir",
    default=None,
    type=str,
    help="插件目录路径（默认使用 config 中的 plugin.plugins_dir）",
)
def run(debug: bool, no_hot_reload: bool, plugins_dir: str | None):
    """启动 NcatBot（连接 NapCat + 加载插件 + 监听事件）"""
    from ncatbot.app import BotClient

    bot = BotClient(
        debug=True if debug else MISSING,
        plugins_dir=plugins_dir if plugins_dir is not None else MISSING,
        hot_reload=False if no_hot_reload else MISSING,
    )
    bot.run()


@click.command()
@click.option(
    "--plugins-dir",
    default=None,
    type=str,
    help="插件目录路径（默认使用 config 中的 plugin.plugins_dir）",
)
def dev(plugins_dir: str | None):
    """以开发模式启动（debug=True + 热重载）"""
    from ncatbot.app import BotClient

    bot = BotClient(
        debug=True,
        plugins_dir=plugins_dir if plugins_dir is not None else MISSING,
        hot_reload=True,
    )
    bot.run()
