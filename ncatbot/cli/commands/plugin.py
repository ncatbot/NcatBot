"""plugin 命令组 — 插件管理。"""

import re
import shutil
from pathlib import Path

import click

from ..utils.colors import success, error, warning, info, header, key, value, dim


def _get_manager():
    from ncatbot.utils import get_config_manager

    return get_config_manager()


def _plugins_dir() -> Path:
    mgr = _get_manager()
    return Path(mgr.plugin.plugins_dir)


def _read_manifest(plugins_dir: Path) -> dict | None:
    """读取插件的 manifest.toml 文件。"""
    manifest_path = plugins_dir / "manifest.toml"
    if not manifest_path.exists():
        return None
    try:
        import tomllib
    except ModuleNotFoundError:
        import tomli as tomllib  # type: ignore[no-redef]
    with open(manifest_path, "rb") as f:
        return tomllib.load(f)


@click.group()
def plugin():
    """插件管理"""


@plugin.command("list")
def plugin_list():
    """列出已安装的插件"""
    pdir = _plugins_dir()
    if not pdir.exists():
        click.echo(warning(f"插件目录不存在: {pdir}"))
        return

    mgr = _get_manager()
    whitelist = mgr.plugin.plugin_whitelist
    blacklist = mgr.plugin.plugin_blacklist
    load_enabled = mgr.plugin.load_plugin

    entries = sorted(
        p for p in pdir.iterdir() if p.is_dir() and not p.name.startswith(".")
    )
    if not entries:
        click.echo(info("暂无已安装的插件。"))
        return

    click.echo(header("已安装插件:"))
    click.echo(dim(f"  插件加载: {'开启' if load_enabled else '关闭'}"))
    click.echo()

    for entry in entries:
        manifest = _read_manifest(entry)
        name = manifest.get("name", entry.name) if manifest else entry.name
        ver = manifest.get("version", "?") if manifest else "?"
        author = manifest.get("author", "") if manifest else ""
        desc = manifest.get("description", "") if manifest else ""

        # 判断启用状态
        if name in blacklist:
            status = error("禁用")
        elif whitelist and name not in whitelist:
            status = warning("未在白名单")
        else:
            status = success("启用")

        line = f"  {key(name)} {dim('v' + ver)}"
        if author:
            line += f" {dim('by ' + author)}"
        line += f"  [{status}]"
        click.echo(line)
        if desc:
            click.echo(f"    {dim(desc)}")


@plugin.command()
@click.argument("name")
def create(name: str):
    """创建插件脚手架"""
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9_]*$", name):
        click.echo(error("插件名必须以字母开头，只能包含字母、数字和下划线"))
        raise SystemExit(1)

    pdir = _plugins_dir()
    target = pdir / name
    if target.exists():
        click.echo(error(f"目录已存在: {target}"))
        raise SystemExit(1)

    template_dir = Path(__file__).parent.parent / "templates" / "plugin"
    if not template_dir.exists():
        click.echo(error("插件模板不存在，请检查安装完整性"))
        raise SystemExit(1)

    pdir.mkdir(parents=True, exist_ok=True)
    shutil.copytree(template_dir, target)

    # 替换占位符
    class_name = "".join(part.capitalize() for part in name.split("_"))
    replacements = {
        "PluginName": name,
        "PluginClassName": class_name,
        "YourName": "Author",
    }
    for file_path in target.rglob("*"):
        if file_path.is_file() and file_path.suffix in (".py", ".toml", ".md"):
            content = file_path.read_text(encoding="utf-8")
            for old, new in replacements.items():
                content = content.replace(old, new)
            file_path.write_text(content, encoding="utf-8")

    click.echo(success(f"插件 {name} 已创建: {target}"))


@plugin.command()
@click.argument("name")
def remove(name: str):
    """删除插件（带确认）"""
    pdir = _plugins_dir()
    target = pdir / name
    if not target.exists():
        click.echo(error(f"插件不存在: {target}"))
        raise SystemExit(1)

    if not click.confirm(f"确认删除插件 {name} ({target})?", abort=True):
        return
    shutil.rmtree(target)
    click.echo(success(f"插件 {name} 已删除"))


@plugin.command("info")
@click.argument("name")
def plugin_info(name: str):
    """显示插件详细信息"""
    pdir = _plugins_dir()
    target = pdir / name
    if not target.exists():
        click.echo(error(f"插件不存在: {target}"))
        raise SystemExit(1)

    manifest = _read_manifest(target)
    if not manifest:
        click.echo(warning(f"插件 {name} 缺少 manifest.toml"))
        return

    click.echo(header(f"插件: {manifest.get('name', name)}"))
    fields = [
        ("版本", "version"),
        ("作者", "author"),
        ("描述", "description"),
        ("入口文件", "main"),
        ("入口类", "entry_class"),
    ]
    for label, field in fields:
        v = manifest.get(field)
        if v:
            click.echo(f"  {key(label)}: {value(str(v))}")

    deps = manifest.get("dependencies", {})
    plugin_deps = {k: v for k, v in deps.items() if k != "pip_dependencies"}
    if plugin_deps:
        click.echo(f"  {key('依赖插件')}:")
        for dep_name, dep_ver in plugin_deps.items():
            click.echo(f"    - {dep_name} {dep_ver}")

    pip_deps = manifest.get("pip_dependencies") or deps.get("pip_dependencies")
    if pip_deps:
        click.echo(f"  {key('Pip 依赖')}: {', '.join(pip_deps)}")


@plugin.command()
@click.argument("name")
def enable(name: str):
    """启用插件（从黑名单移除 / 加入白名单）"""
    mgr = _get_manager()
    blacklist = list(mgr.plugin.plugin_blacklist)
    whitelist = list(mgr.plugin.plugin_whitelist)
    changed = False

    if name in blacklist:
        blacklist.remove(name)
        mgr.update_value("plugin.plugin_blacklist", blacklist)
        changed = True

    if whitelist and name not in whitelist:
        whitelist.append(name)
        mgr.update_value("plugin.plugin_whitelist", whitelist)
        changed = True

    if changed:
        mgr.save()
        click.echo(success(f"插件 {name} 已启用"))
    else:
        click.echo(info(f"插件 {name} 已处于启用状态"))


@plugin.command()
@click.argument("name")
def disable(name: str):
    """禁用插件（加入黑名单 / 从白名单移除）"""
    mgr = _get_manager()
    blacklist = list(mgr.plugin.plugin_blacklist)
    whitelist = list(mgr.plugin.plugin_whitelist)
    changed = False

    if name in whitelist:
        whitelist.remove(name)
        mgr.update_value("plugin.plugin_whitelist", whitelist)
        changed = True

    if name not in blacklist:
        blacklist.append(name)
        mgr.update_value("plugin.plugin_blacklist", blacklist)
        changed = True

    if changed:
        mgr.save()
        click.echo(success(f"插件 {name} 已禁用"))
    else:
        click.echo(info(f"插件 {name} 已处于禁用状态"))


@plugin.command()
def on():
    """开启插件加载（load_plugin = True）"""
    mgr = _get_manager()
    mgr.update_value("plugin.load_plugin", True)
    mgr.save()
    click.echo(success("插件加载已开启"))


@plugin.command()
def off():
    """关闭插件加载（load_plugin = False）"""
    mgr = _get_manager()
    mgr.update_value("plugin.load_plugin", False)
    mgr.save()
    click.echo(success("插件加载已关闭"))
