"""NcatBot CLI 主入口 — click group 定义。"""

import importlib.metadata

import click

from .commands.run import run, dev
from .commands.config import config
from .commands.plugin import plugin
from .commands.napcat import napcat
from .commands.init import init
from .commands.adapter import adapter
from .commands.ref import ref


def _get_version() -> str:
    try:
        return importlib.metadata.version("ncatbot5")
    except importlib.metadata.PackageNotFoundError:
        return "dev"


@click.group(invoke_without_command=True)
@click.version_option(version=_get_version(), prog_name="NcatBot")
@click.pass_context
def cli(ctx: click.Context):
    """NcatBot — QQ 机器人框架 CLI"""
    if ctx.invoked_subcommand is None:
        from ncatbot.utils import is_interactive

        if not is_interactive():
            click.echo(ctx.get_help())
            return

        from .utils.repl import start_repl

        start_repl(ctx)


cli.add_command(run)
cli.add_command(dev)
cli.add_command(config)
cli.add_command(plugin)
cli.add_command(napcat)
cli.add_command(init)
cli.add_command(adapter)
cli.add_command(ref)
