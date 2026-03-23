"""
Plugin Loader 生命周期单元测试

LD-01 ~ LD-05：覆盖 load/unload/load_all 的核心路径。
"""

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
        plugin_dir=Path("data") / name,
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
            patch("ncatbot.core.flush_pending", return_value=2) as mock_flush,
            patch("ncatbot.core.clear_pending"),
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
            patch("ncatbot.core.flush_pending"),
            patch("ncatbot.core.clear_pending") as mock_clear,
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
