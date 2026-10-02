"""
Plugin Loader 生命周期单元测试

LD-01 ~ LD-09：覆盖 load/unload/load_all/热重载消费 的核心路径。
"""

import asyncio
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ncatbot.plugin.loader.core import PluginLoader
from ncatbot.plugin.base import BasePlugin
from ncatbot.plugin.manifest import PluginManifest


class _StubPlugin(BasePlugin):
    name = "stub"
    version = "1.0.0"

    async def on_load(self):
        self._loaded = True

    async def on_close(self):
        self._closed = True


class _FailPlugin(BasePlugin):
    name = "fail"
    version = "1.0.0"

    async def on_load(self):
        raise RuntimeError("load boom")


def _make_manifest(name: str, deps=None) -> PluginManifest:
    return PluginManifest(
        name=name,
        version="1.0.0",
        main="main.py",
        dependencies=deps or {},
        plugin_path=Path("data") / name,
        folder_name=name,
    )


@pytest.fixture
def loader() -> PluginLoader:
    ld = PluginLoader()
    # 注入 mock handler dispatcher
    mock_hd = MagicMock()
    mock_hd.revoke_plugin = MagicMock()
    ld._handler_dispatcher = mock_hd
    return ld


class TestLoadPlugin:
    """LD-01 ~ LD-02: 单插件加载"""

    @pytest.mark.asyncio
    async def test_ld01_load_success(self, loader: PluginLoader):
        """LD-01: load_plugin 成功 → handler flush 到 dispatcher"""
        manifest = _make_manifest("stub")
        loader._indexer._manifests = {"stub": manifest}

        with (
            patch.object(loader._importer, "load_module") as mock_load,
            patch.object(
                loader._importer, "find_plugin_class", return_value=_StubPlugin
            ),
            patch(
                "ncatbot.plugin.loader.core.flush_pending", return_value=2
            ) as mock_flush,
            patch("ncatbot.plugin.loader.core.clear_pending"),
        ):
            mock_load.return_value = MagicMock()

            plugin = await loader.load_plugin("stub")

            assert plugin is not None
            assert "stub" in loader.plugins
            assert plugin._loaded is True
            mock_flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_ld02_load_failure_cleanup(self, loader: PluginLoader):
        """LD-02: load_plugin 异常 → handler 清理回滚"""
        manifest = _make_manifest("fail")
        loader._indexer._manifests = {"fail": manifest}

        with (
            patch.object(loader._importer, "load_module") as mock_load,
            patch.object(
                loader._importer, "find_plugin_class", return_value=_FailPlugin
            ),
            patch("ncatbot.plugin.loader.core.flush_pending"),
            patch("ncatbot.plugin.loader.core.clear_pending") as mock_clear,
        ):
            mock_load.return_value = MagicMock()

            plugin = await loader.load_plugin("fail")

            assert plugin is None
            assert "fail" not in loader.plugins
            mock_clear.assert_called_with("fail")


class TestUnloadPlugin:
    """LD-03: 卸载"""

    @pytest.mark.asyncio
    async def test_ld03_unload(self, loader: PluginLoader):
        """LD-03: unload_plugin → handler revoke + on_close"""
        manifest = _make_manifest("stub")
        loader._indexer._manifests = {"stub": manifest}

        plugin = _StubPlugin()
        plugin._manifest = manifest
        plugin.workspace = Path("data/stub")
        plugin.config = {}
        plugin.data = {}
        loader.plugins["stub"] = plugin

        with patch("ncatbot.core.clear_pending"):
            result = await loader.unload_plugin("stub")

        assert result is True
        assert "stub" not in loader.plugins
        assert plugin._closed is True
        loader._handler_dispatcher.revoke_plugin.assert_called_with("stub")


class TestLoadAll:
    """LD-04 ~ LD-05: 批量加载"""

    @pytest.mark.asyncio
    async def test_ld04_topological_order(self, loader: PluginLoader):
        """LD-04: load_all 按依赖拓扑排序加载"""
        m_a = _make_manifest("a", deps={"b": ">=1.0.0"})
        m_b = _make_manifest("b")
        manifests = {"a": m_a, "b": m_b}

        load_order = []

        async def fake_load(name):
            load_order.append(name)
            p = _StubPlugin()
            p.name = name
            loader.plugins[name] = p
            return p

        with (
            patch.object(loader._indexer, "scan", return_value=manifests),
            patch.object(loader._importer, "add_plugin_root"),
            patch.object(loader, "load_plugin", side_effect=fake_load),
            patch.object(loader, "_check_pip_deps_batch", return_value=set()),
        ):
            loaded = await loader.load_all(Path("plugins"))

        # b 应在 a 之前加载
        assert load_order.index("b") < load_order.index("a")
        assert set(loaded) == {"a", "b"}

    @pytest.mark.asyncio
    async def test_ld05_missing_dependency_skip(self, loader: PluginLoader):
        """LD-05: load_all 缺失依赖 → 跳过该插件继续"""
        m_a = _make_manifest("a", deps={"nonexistent": ">=1.0.0"})
        m_b = _make_manifest("b")
        manifests = {"a": m_a, "b": m_b}

        async def fake_load(name):
            p = _StubPlugin()
            p.name = name
            loader.plugins[name] = p
            return p

        with (
            patch.object(loader._indexer, "scan", return_value=manifests),
            patch.object(loader._importer, "add_plugin_root"),
            patch.object(loader, "load_plugin", side_effect=fake_load),
            patch.object(loader, "_check_pip_deps_batch", return_value=set()),
        ):
            # DependencyResolver 在 resolve 时会忽略未索引的依赖
            # 但 validate_versions 可能报警告
            real_resolver = loader._resolver

            def fake_resolve(m):
                # 只返回有效插件
                return ["b", "a"]

            with patch.object(real_resolver, "resolve", side_effect=fake_resolve):
                with patch.object(real_resolver, "validate_versions"):
                    loaded = await loader.load_all(Path("plugins"))

        assert "b" in loaded


class TestInstantiate:
    """LD-06: _instantiate 注入元数据"""

    def test_ld06_injects_name_and_version(self, loader: PluginLoader):
        """LD-06: _instantiate 从 manifest 注入 name/version/author/description"""
        manifest = _make_manifest("my_plugin")
        manifest.author = "TestAuthor"
        manifest.description = "A test plugin"

        plugin = loader._instantiate(_StubPlugin, manifest)

        assert plugin.name == "my_plugin"
        assert plugin.version == "1.0.0"
        assert plugin.author == "TestAuthor"
        assert plugin.description == "A test plugin"
        assert plugin.workspace == Path("data/my_plugin")

    def test_ld06_logger_property(self, loader: PluginLoader):
        """LD-06: 实例化后 plugin.logger 可正常使用"""
        manifest = _make_manifest("logger_test")
        plugin = loader._instantiate(_StubPlugin, manifest)

        assert plugin.logger is not None
        # logger 不应抛异常
        plugin.logger.info("test log from plugin")


class TestReloadConsumer:
    """LD-07: _reload_consumer 热重载消费逻辑"""

    @pytest.mark.asyncio
    async def test_ld07_reload_after_failed_load_retries(self, loader: PluginLoader):
        """LD-07: 热重载失败后再次文件变更仍应尝试重新加载

        场景：
          1. 插件已加载 → 文件变更 → reload_plugin → load_plugin 失败（插件从 plugins 中移除）
          2. 再次文件变更 → _reload_consumer 应重新尝试加载，而非跳过
        """
        manifest = _make_manifest("my_plugin")
        manifest.folder_name = "04_my_plugin"
        loader._indexer._manifests = {"my_plugin": manifest}

        # 模拟插件最初已加载
        stub = _StubPlugin()
        stub._manifest = manifest
        stub.workspace = Path("data/my_plugin")
        stub.config = {}
        stub.data = {}
        loader.plugins["my_plugin"] = stub

        reload_attempts = []
        load_attempts = []

        async def mock_reload(name):
            reload_attempts.append(name)
            # 模拟 reload 失败：unload 成功（从 plugins 移除），但 load 失败
            loader.plugins.pop(name, None)
            return False

        async def mock_load(name):
            load_attempts.append(name)
            # 模拟第二次加载成功
            p = _StubPlugin()
            p._manifest = manifest
            loader.plugins[name] = p
            return p

        loader.reload_plugin = mock_reload
        loader.load_plugin = mock_load

        # 启动 consumer
        task = asyncio.create_task(loader._reload_consumer())

        # 第一次文件变更 → 应触发 reload_plugin
        await loader._reload_queue.put("04_my_plugin")
        await asyncio.sleep(0.05)

        assert reload_attempts == ["my_plugin"], "第一次变更应触发 reload"

        # 此时 my_plugin 已不在 plugins 中（reload 失败移除了它）
        assert "my_plugin" not in loader.plugins

        # 第二次文件变更 → 应仍然尝试加载（而非跳过）
        await loader._reload_queue.put("04_my_plugin")
        await asyncio.sleep(0.05)

        # 关键断言：第二次变更应触发某种加载尝试
        total_attempts = len(reload_attempts) + len(load_attempts)
        assert total_attempts >= 2, (
            f"第二次文件变更后应触发加载尝试，但仅有 {total_attempts} 次: "
            f"reload={reload_attempts}, load={load_attempts}"
        )

        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    @pytest.mark.asyncio
    async def test_ld08_runtime_added_plugin_auto_indexed(
        self, loader: PluginLoader, tmp_path: Path
    ):
        """LD-08: 运行时新放入的插件目录应自动索引并加载

        场景：
          1. Bot 启动时 load_all 扫描了 plugins/，此时无 new_plugin
          2. 用户运行时将 new_plugin 文件夹放入 plugins/
          3. FileWatcher 检测到变更，发送文件夹名到队列
          4. _reload_consumer 应自动索引该插件并加载，而非跳过
        """
        # 构建临时插件目录
        plugin_dir = tmp_path / "05_new_plugin"
        plugin_dir.mkdir()
        manifest_toml = plugin_dir / "manifest.toml"
        manifest_toml.write_text(
            'name = "new_plugin"\nversion = "1.0.0"\nmain = "main.py"\n'
        )
        main_py = plugin_dir / "main.py"
        main_py.write_text("# placeholder")

        # 模拟 load_all 已经执行过，设置 plugins_dir
        loader._plugins_dir = tmp_path
        # 索引器中无 new_plugin（模拟启动时不存在）
        assert loader._indexer.get_by_folder("05_new_plugin") is None

        load_attempts = []

        async def mock_load(name):
            load_attempts.append(name)
            p = _StubPlugin()
            loader.plugins[name] = p
            return p

        loader.load_plugin = mock_load

        # 启动 consumer
        task = asyncio.create_task(loader._reload_consumer())

        # 模拟 FileWatcher 发送文件夹名
        await loader._reload_queue.put("05_new_plugin")
        await asyncio.sleep(0.05)

        # 关键断言：新插件应被自动索引并尝试加载
        assert load_attempts == ["new_plugin"], (
            f"运行时新增插件应被自动索引并加载，但 load_attempts={load_attempts}"
        )
        # 索引器中应已有该插件
        assert loader._indexer.get_by_folder("05_new_plugin") is not None

        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task


class TestPluginEnableConfig:
    """LD-09: plugin_blacklist / plugin_whitelist 控制插件是否加载"""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("blacklist", "whitelist", "expected"),
        [
            (["b"], [], {"a", "c"}),
            ([], ["a", "c"], {"a", "c"}),
            (["a"], ["a", "b"], {"b"}),
        ],
    )
    async def test_ld09_blacklist_whitelist_skip_load(
        self, loader: PluginLoader, blacklist, whitelist, expected
    ):
        """LD-09: load_all 跳过黑名单中的插件，白名单非空时只加载白名单内的插件"""
        manifests = {name: _make_manifest(name) for name in ("a", "b", "c")}
        loader._indexer._manifests = manifests

        config = MagicMock()
        config.plugin.plugin_blacklist = blacklist
        config.plugin.plugin_whitelist = whitelist

        with (
            patch("ncatbot.plugin.loader.core.get_config_manager", return_value=config),
            patch.object(loader._indexer, "scan", return_value=manifests),
            patch.object(loader._importer, "add_plugin_root"),
            patch.object(loader._importer, "load_module") as mock_load,
            patch.object(
                loader._importer, "find_plugin_class", return_value=_StubPlugin
            ),
            patch.object(loader, "_check_pip_deps_batch", return_value=set()),
            patch("ncatbot.plugin.loader.core.flush_pending"),
            patch("ncatbot.plugin.loader.core.clear_pending"),
        ):
            loaded = await loader.load_all(Path("plugins"))

        assert set(loaded) == expected
        assert set(loader.plugins) == expected
        assert {call.args[0].name for call in mock_load.call_args_list} == expected
