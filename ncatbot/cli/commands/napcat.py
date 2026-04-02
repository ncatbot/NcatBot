"""napcat 命令组 — NapCat 管理与诊断。"""

import asyncio
import platform

import click


def _get_manager():
    from ncatbot.utils import get_config_manager

    return get_config_manager()


@click.group()
def napcat():
    """NapCat 管理"""


@napcat.group(invoke_without_command=True)
@click.pass_context
def diagnose(ctx: click.Context):
    """NapCat 诊断工具"""
    if ctx.invoked_subcommand is None:
        # 无子命令 → 运行完整诊断
        from ncatbot.adapter.napcat.debug.diagnose import diagnose as run_diagnose

        asyncio.run(run_diagnose())


@diagnose.command()
@click.option("--uri", default=None, help="WebSocket URI（默认读取配置）")
@click.option("--token", default=None, help="WebSocket Token（默认读取配置）")
def ws(uri: str | None, token: str | None):
    """检测 NapCat WebSocket 连接"""
    if uri is None or token is None:
        mgr = _get_manager()
        uri = uri or mgr.napcat.ws_uri
        token = token if token is not None else mgr.napcat.ws_token

    from ncatbot.adapter.napcat.debug.check_ws import check_ws

    asyncio.run(check_ws(uri, token))


@diagnose.command()
@click.option("--uri", default=None, help="WebUI URI（默认读取配置）")
@click.option("--token", default=None, help="WebUI Token（默认读取配置）")
def webui(uri: str | None, token: str | None):
    """检测 NapCat WebUI 状态"""
    if uri is None or token is None:
        mgr = _get_manager()
        uri = uri or mgr.napcat.webui_uri
        token = token if token is not None else mgr.napcat.webui_token

    from ncatbot.adapter.napcat.debug.check_webui import run_checks

    run_checks(uri, token)


@napcat.command()
@click.option(
    "--yes",
    "-y",
    is_flag=True,
    default=False,
    help="跳过确认，直接安装（Docker/CI 场景）",
)
def install(yes: bool):
    """安装 NapCat + QQ（支持 --yes 跳过确认）"""
    from ncatbot.adapter.napcat.setup.platform import PlatformOps
    from ncatbot.adapter.napcat.setup.installer import NapCatInstaller

    platform_ops = PlatformOps.create()
    installer = NapCatInstaller(platform_ops)

    if platform_ops.is_napcat_installed():
        click.echo("NapCat 已安装，跳过。")
        return

    ok = installer.install(skip_confirm=yes)
    if ok:
        click.echo("NapCat 安装完成。")
    else:
        click.echo("NapCat 安装失败或被取消。", err=True)
        raise SystemExit(1)


@napcat.command()
def stop():
    """停止本机 NapCat 进程（仅 Linux）。"""
    if platform.system() != "Linux":
        click.echo("napcat stop 仅支持 Linux。", err=True)
        raise SystemExit(1)

    from ncatbot.adapter.napcat.setup.platform import PlatformOps

    platform_ops = PlatformOps.create()
    platform_ops.stop_napcat()
    click.echo("NapCat 已停止。")
