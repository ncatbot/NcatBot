"""ref 命令 — 下载 AI 用户参考资料。"""

import shutil
import zipfile
from pathlib import Path

import click
import httpx

from ..utils.colors import error, info, success, warning

GITHUB_API_LATEST = "https://api.github.com/repos/ncatbot/NcatBot/releases/latest"
GITHUB_API_TAG = "https://api.github.com/repos/ncatbot/NcatBot/releases/tags/v{version}"
ASSET_PREFIX = "ncatbot5-"
ASSET_SUFFIX = "-user-reference.zip"

IDE_CHOICES = ["vscode", "trae", "cursor"]


def _find_asset(release: dict) -> tuple[str, str] | None:
    """从 Release JSON 中查找 user-reference 资源，返回 (name, url) 或 None。"""
    for asset in release.get("assets", []):
        name = asset.get("name", "")
        if name.startswith(ASSET_PREFIX) and name.endswith(ASSET_SUFFIX):
            return name, asset["browser_download_url"]
    return None


def _resolve_ide(vscode: bool, trae: bool, cursor: bool) -> str:
    """根据 flag 或交互选择确定 IDE 类型。"""
    selected = [
        name
        for name, flag in [("vscode", vscode), ("trae", trae), ("cursor", cursor)]
        if flag
    ]
    if len(selected) > 1:
        raise click.UsageError("只能指定一个 IDE 类型（--vscode / --trae / --cursor）")
    if selected:
        return selected[0]

    # 交互选择
    click.echo(info("请选择你使用的 IDE："))
    for i, name in enumerate(IDE_CHOICES, 1):
        click.echo(f"  {i}. {name}")
    choice = click.prompt("输入编号", type=click.IntRange(1, len(IDE_CHOICES)))
    return IDE_CHOICES[choice - 1]


def _post_extract_ide(target: Path, ide: str) -> None:
    """根据 IDE 类型执行解压后处理。"""
    if ide == "trae":
        agents_dir = target / ".agents"
        trae_dir = target / ".trae"
        if agents_dir.exists():
            if trae_dir.exists():
                click.echo(warning(".trae 目录已存在，先删除旧目录..."))
                shutil.rmtree(trae_dir)
            agents_dir.rename(trae_dir)
            click.echo(success("✓ 已将 .agents 重命名为 .trae（Trae 要求）"))
        else:
            click.echo(warning(".agents 目录不存在，跳过重命名"))


@click.command()
@click.option("--dir", "target_dir", default=".", help="解压目标目录（默认当前目录）")
@click.option("--version", "version", default=None, help="指定版本号（默认最新）")
@click.option("--no-proxy", is_flag=True, help="禁用 GitHub 代理，直连下载")
@click.option("--vscode", is_flag=True, help="适配 VSCode（默认格式）")
@click.option("--trae", is_flag=True, help="适配 Trae（将 .agents 重命名为 .trae）")
@click.option("--cursor", is_flag=True, help="适配 Cursor（与 VSCode 相同）")
def ref(
    target_dir: str,
    version: str | None,
    no_proxy: bool,
    vscode: bool,
    trae: bool,
    cursor: bool,
):
    """下载 AI 用户参考资料（user-reference.zip）并解压到项目目录。"""
    target = Path(target_dir).resolve()

    # IDE 选择
    ide = _resolve_ide(vscode, trae, cursor)
    click.echo(info(f"IDE: {ide}"))

    # 查询 Release
    click.echo(info("正在查询 GitHub Release..."))
    api_url = GITHUB_API_TAG.format(version=version) if version else GITHUB_API_LATEST
    try:
        resp = httpx.get(
            api_url,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "ncatbot",
            },
            timeout=15,
            follow_redirects=True,
        )
        resp.raise_for_status()
        release = resp.json()
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            click.echo(error("未找到指定版本的 Release"))
        else:
            click.echo(error(f"GitHub API 请求失败: {exc.response.status_code}"))
        raise SystemExit(1)
    except (httpx.ConnectError, httpx.TimeoutException):
        click.echo(error("无法连接到 GitHub，请检查网络或稍后重试"))
        raise SystemExit(1)

    tag_name = release.get("tag_name", "unknown")
    click.echo(info(f"Release: {tag_name}"))

    # 查找资源
    result = _find_asset(release)
    if result is None:
        click.echo(error("该 Release 中未找到 user-reference.zip 资源"))
        raise SystemExit(1)
    asset_name, asset_url = result
    click.echo(info(f"资源: {asset_name}"))

    # 代理
    if not no_proxy:
        from ncatbot.utils import get_proxy_url

        proxy = get_proxy_url()
        if proxy:
            asset_url = f"{proxy.rstrip('/')}/{asset_url}"
            click.echo(info(f"使用代理: {proxy}"))

    # 下载
    click.echo(info("正在下载..."))
    tmp_zip = target / asset_name
    try:
        from ncatbot.utils import download_file

        download_file(asset_url, str(tmp_zip))
    except Exception as exc:
        click.echo(error(f"下载失败: {exc}"))
        tmp_zip.unlink(missing_ok=True)
        raise SystemExit(1)

    # 解压
    click.echo(info(f"正在解压到 {target} ..."))
    try:
        with zipfile.ZipFile(tmp_zip, "r") as zf:
            zf.extractall(target)
    except zipfile.BadZipFile:
        click.echo(error("下载的文件不是有效的 ZIP 文件"))
        tmp_zip.unlink(missing_ok=True)
        raise SystemExit(1)

    tmp_zip.unlink(missing_ok=True)

    # IDE 后处理
    _post_extract_ide(target, ide)

    click.echo(success(f"✓ 用户参考资料已解压到 {target}"))
