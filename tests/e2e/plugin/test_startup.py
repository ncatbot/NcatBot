"""插件启动回调：首次启动、运行中重载及异常隔离。"""

from pathlib import Path

import pytest

import ncatbot.utils.config.manager as config_manager_mod
from ncatbot.adapter.mock import MockAdapter
from ncatbot.app import BotClient
from ncatbot.core import registrar
from ncatbot.testing import PluginTestHarness

pytestmark = pytest.mark.asyncio


@pytest.fixture(autouse=True)
def reset_config(monkeypatch, tmp_path):
    config_manager_mod._default_manager = None
    config = tmp_path / "config.yaml"
    config.write_text("bot_uin: '111111'\nroot: '10001'\n", encoding="utf-8")
    monkeypatch.setenv("NCATBOT_CONFIG_PATH", str(config))
    yield
    config_manager_mod._default_manager = None


def write_probe(plugins_root: Path, trace: Path, name: str, *, fail=False):
    plugin_dir = plugins_root / name
    plugin_dir.mkdir(parents=True)
    class_name = f"{name.title()}Plugin"
    (plugin_dir / "manifest.toml").write_text(
        f'name = "{name}"\nversion = "1.0.0"\nmain = "main.py"\n'
        f'entry_class = "{class_name}"\n',
        encoding="utf-8",
    )
    (plugin_dir / "main.py").write_text(
        "from pathlib import Path\n"
        "from ncatbot.core import registrar\n"
        "from ncatbot.plugin import NcatBotPlugin\n"
        f"TRACE = Path({str(trace)!r})\n"
        "def record(value):\n"
        "    with TRACE.open('a') as stream:\n"
        "        stream.write(value + '\\n')\n"
        f"class {class_name}(NcatBotPlugin):\n"
        f"    name = {name!r}\n"
        "    version = '1.0.0'\n"
        "    async def on_load(self):\n"
        "        record(f'load:{self.name}:{\"beta\" in self._plugin_loader.plugins}')\n"
        "    @registrar.on_message()\n"
        "    async def on_message(self, event):\n"
        "        pass\n"
        "    @registrar.on_startup()\n"
        "    async def ready(self):\n"
        "        handlers = self._plugin_loader._handler_dispatcher.get_handlers('message')\n"
        "        names = {entry.plugin_name for entry in handlers}\n"
        '        record(f\'startup:{self.name}:{"beta" in self._plugin_loader.plugins}:{"alpha" in names and "beta" in names}\')\n'
        + ("        raise RuntimeError('startup failed')\n" if fail else ""),
        encoding="utf-8",
    )


def read_trace(trace: Path) -> list[str]:
    return trace.read_text().splitlines() if trace.exists() else []


async def test_plugin_startup_runs_after_all_plugins_and_handlers(tmp_path):
    """PL-54: on_load 逐个执行，startup 等全部插件及 handler 就绪。"""
    plugins = tmp_path / "plugins"
    trace = tmp_path / "trace.txt"
    write_probe(plugins, trace, "alpha")
    write_probe(plugins, trace, "beta")
    bot = BotClient(
        adapters=[MockAdapter(platform="qq")], plugins_dir=plugins, hot_reload=False
    )

    @bot.on_startup()
    async def bot_ready():
        with trace.open("a") as stream:
            stream.write("bot:startup\n")

    try:
        await bot.run_async()
        lines = read_trace(trace)
        assert len(lines) == 5
        assert {line.split(":")[1] for line in lines[:2]} == {"alpha", "beta"}
        assert all(line.startswith("load:") for line in lines[:2])
        assert set(lines[2:4]) == {
            "startup:alpha:True:True",
            "startup:beta:True:True",
        }
        assert lines[4] == "bot:startup"
        await bot.plugin_loader.run_startup()
        assert len(read_trace(trace)) == 5
    finally:
        await bot.shutdown()


async def test_plugin_startup_runs_for_reload_and_late_load(tmp_path):
    """PL-55: 运行中重载与手动加载仅触发目标插件的新实例 startup。"""
    plugins = tmp_path / "plugins"
    trace = tmp_path / "trace.txt"
    write_probe(plugins, trace, "alpha")
    write_probe(plugins, trace, "beta")
    bot = BotClient(
        adapters=[MockAdapter(platform="qq")], plugins_dir=plugins, hot_reload=False
    )
    try:
        await bot.run_async()
        trace.write_text("")
        assert await bot.plugin_loader.reload_plugin("alpha")
        assert read_trace(trace) == ["load:alpha:True", "startup:alpha:True:True"]

        trace.write_text("")
        assert await bot.plugin_loader.unload_plugin("beta")
        assert await bot.plugin_loader.load_plugin("beta") is not None
        assert read_trace(trace) == ["load:beta:False", "startup:beta:True:True"]
    finally:
        await bot.shutdown()


async def test_plugin_startup_failure_does_not_block_next_plugin(tmp_path):
    """PL-56: 单个 startup 抛错不会阻止其他插件执行。"""
    plugins = tmp_path / "plugins"
    trace = tmp_path / "trace.txt"
    write_probe(plugins, trace, "alpha", fail=True)
    write_probe(plugins, trace, "beta")
    bot = BotClient(
        adapters=[MockAdapter(platform="qq")], plugins_dir=plugins, hot_reload=False
    )
    try:
        await bot.run_async()
        assert "startup:beta:True:True" in read_trace(trace)
        assert bot.plugin_loader.get_plugin("alpha") is not None
    finally:
        await bot.shutdown()


async def test_plugin_startup_requires_async_callback():
    """PL-57: startup 装饰器拒绝同步函数，避免无声忽略返回值。"""
    with pytest.raises(TypeError, match="async def"):
        registrar.on_startup()(lambda self: None)


async def test_plugin_harness_runs_startup_after_selected_plugins(tmp_path):
    """PL-58: 选择性加载的离线插件测试也会触发 startup。"""
    plugins = tmp_path / "plugins"
    trace = tmp_path / "trace.txt"
    write_probe(plugins, trace, "alpha")
    write_probe(plugins, trace, "beta")

    async with PluginTestHarness(
        plugin_names=["alpha", "beta"], plugins_dir=plugins, skip_builtin=True
    ):
        lines = read_trace(trace)
        assert len(lines) == 4
        assert {line.split(":")[1] for line in lines[:2]} == {"alpha", "beta"}
        assert all(line.startswith("load:") for line in lines[:2])
        assert set(lines[2:]) == {
            "startup:alpha:True:True",
            "startup:beta:True:True",
        }
