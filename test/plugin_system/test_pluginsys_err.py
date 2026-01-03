"""Tests for ncatbot.plugin_system.pluginsys_err module."""


class TestPluginSystemError:
    """Tests for base PluginSystemError class."""

    def test_plugin_system_error_basic(self):
        """Test basic PluginSystemError."""
        from ncatbot.plugin_system.pluginsys_err import PluginSystemError

        error = PluginSystemError("base error")
        assert isinstance(error, Exception)


class TestPluginCircularDependencyError:
    """Tests for PluginCircularDependencyError."""

    def test_circular_dependency_str(self):
        """Test string representation."""
        from ncatbot.plugin_system.pluginsys_err import PluginCircularDependencyError

        error = PluginCircularDependencyError(dependency_chain=["A", "B", "C", "A"])
        msg = str(error)
        assert "循环依赖" in msg
        assert "A -> B -> C -> A" in msg

    def test_circular_dependency_is_plugin_system_error(self):
        """Test inheritance."""
        from ncatbot.plugin_system.pluginsys_err import (
            PluginCircularDependencyError,
            PluginSystemError,
        )

        error = PluginCircularDependencyError(dependency_chain=["A", "B"])
        assert isinstance(error, PluginSystemError)


class TestPluginNotFoundError:
    """Tests for PluginNotFoundError."""

    def test_not_found_str(self):
        """Test string representation."""
        from ncatbot.plugin_system.pluginsys_err import PluginNotFoundError

        error = PluginNotFoundError(plugin_name="MyPlugin")
        msg = str(error)
        assert "MyPlugin" in msg
        assert "未找到" in msg

    def test_not_found_attributes(self):
        """Test error attributes."""
        from ncatbot.plugin_system.pluginsys_err import PluginNotFoundError

        error = PluginNotFoundError(plugin_name="TestPlugin")
        assert error.plugin_name == "TestPlugin"


class TestPluginLoadError:
    """Tests for PluginLoadError."""

    def test_load_error_str(self):
        """Test string representation."""
        from ncatbot.plugin_system.pluginsys_err import PluginLoadError

        error = PluginLoadError(
            plugin_name="BrokenPlugin", reason="Syntax error in main.py"
        )
        msg = str(error)
        assert "BrokenPlugin" in msg
        assert "无法加载" in msg
        assert "Syntax error" in msg

    def test_load_error_attributes(self):
        """Test error attributes."""
        from ncatbot.plugin_system.pluginsys_err import PluginLoadError

        error = PluginLoadError(plugin_name="Test", reason="reason")
        assert error.plugin_name == "Test"
        assert error.reason == "reason"


class TestPluginDependencyError:
    """Tests for PluginDependencyError."""

    def test_dependency_error_str(self):
        """Test string representation."""
        from ncatbot.plugin_system.pluginsys_err import PluginDependencyError

        error = PluginDependencyError(
            plugin_name="MyPlugin",
            missing_dependency="DatabasePlugin",
            version_constraints=">=1.0.0",
        )
        msg = str(error)
        assert "MyPlugin" in msg
        assert "DatabasePlugin" in msg
        assert ">=1.0.0" in msg
        assert "缺少依赖" in msg


class TestPluginVersionError:
    """Tests for PluginVersionError."""

    def test_version_error_str(self):
        """Test string representation."""
        from ncatbot.plugin_system.pluginsys_err import PluginVersionError

        error = PluginVersionError(
            plugin_name="MyPlugin",
            required_plugin="CorePlugin",
            required_version=">=2.0.0",
            actual_version="1.5.0",
        )
        msg = str(error)
        assert "MyPlugin" in msg
        assert "CorePlugin" in msg
        assert ">=2.0.0" in msg
        assert "1.5.0" in msg
        assert "版本不满足" in msg


class TestPluginUnloadError:
    """Tests for PluginUnloadError."""

    def test_unload_error_str(self):
        """Test string representation."""
        from ncatbot.plugin_system.pluginsys_err import PluginUnloadError

        error = PluginUnloadError(
            plugin_name="RunningPlugin", reason="Has pending tasks"
        )
        msg = str(error)
        assert "RunningPlugin" in msg
        assert "无法卸载" in msg
        assert "pending tasks" in msg


class TestInvalidPluginStateError:
    """Tests for InvalidPluginStateError."""

    def test_invalid_state_str(self):
        """Test string representation."""
        from ncatbot.plugin_system.pluginsys_err import InvalidPluginStateError

        error = InvalidPluginStateError(plugin_name="StatePlugin", state="CORRUPTED")
        msg = str(error)
        assert "StatePlugin" in msg
        assert "无效状态" in msg
        assert "CORRUPTED" in msg


class TestEventHandlerError:
    """Tests for EventHandlerError."""

    def test_event_handler_error_str(self):
        """Test string representation."""
        from ncatbot.plugin_system.pluginsys_err import EventHandlerError

        class MockHandler:
            __module__ = "test_module"

        error = EventHandlerError(
            error_info="Handler raised exception", handler=MockHandler()
        )
        msg = str(error)
        assert "test_module" in msg
        assert "事件处理器错误" in msg


class TestPluginInitError:
    """Tests for PluginInitError."""

    def test_init_error_str(self):
        """Test string representation."""
        from ncatbot.plugin_system.pluginsys_err import PluginInitError

        error = PluginInitError(
            plugin_name="InitPlugin", reason="Failed to connect to database"
        )
        msg = str(error)
        assert "InitPlugin" in msg
        assert "初始化失败" in msg
        assert "database" in msg


class TestPluginDataError:
    """Tests for PluginDataError."""

    def test_data_error_str(self):
        """Test string representation."""
        from ncatbot.plugin_system.pluginsys_err import PluginDataError

        error = PluginDataError(
            plugin_name="DataPlugin", operation="保存", reason="Disk full"
        )
        msg = str(error)
        assert "DataPlugin" in msg
        assert "保存" in msg
        assert "数据" in msg
        assert "Disk full" in msg


class TestPluginValidationError:
    """Tests for PluginValidationError."""

    def test_validation_error_str(self):
        """Test string representation."""
        from ncatbot.plugin_system.pluginsys_err import PluginValidationError

        error = PluginValidationError(
            plugin_name="BadPlugin", missing_attrs=["name", "version"]
        )
        msg = str(error)
        assert "BadPlugin" in msg
        assert "验证失败" in msg
        assert "name" in msg
        assert "version" in msg


class TestPluginWorkspaceError:
    """Tests for PluginWorkspaceError."""

    def test_workspace_error_str(self):
        """Test string representation."""
        from ncatbot.plugin_system.pluginsys_err import PluginWorkspaceError

        error = PluginWorkspaceError(
            plugin_name="WorkspacePlugin",
            path="/data/plugins/workspace",
            reason="Permission denied",
        )
        msg = str(error)
        assert "WorkspacePlugin" in msg
        assert "/data/plugins/workspace" in msg
        assert "Permission denied" in msg


class TestPluginNameConflictError:
    """Tests for PluginNameConflictError."""

    def test_name_conflict_str(self):
        """Test string representation."""
        from ncatbot.plugin_system.pluginsys_err import PluginNameConflictError

        error = PluginNameConflictError(plugin_name="DuplicatePlugin")
        msg = str(error)
        assert "DuplicatePlugin" in msg
        assert "冲突" in msg
        assert "已被使用" in msg


class TestErrorInheritance:
    """Tests for error inheritance hierarchy."""

    def test_all_errors_inherit_from_plugin_system_error(self):
        """Test all plugin errors inherit from PluginSystemError."""
        from ncatbot.plugin_system.pluginsys_err import (
            PluginSystemError,
            PluginCircularDependencyError,
            PluginNotFoundError,
            PluginLoadError,
            PluginDependencyError,
            PluginVersionError,
            PluginUnloadError,
            InvalidPluginStateError,
            PluginInitError,
            PluginDataError,
            PluginValidationError,
            PluginWorkspaceError,
            PluginNameConflictError,
        )

        assert issubclass(PluginCircularDependencyError, PluginSystemError)
        assert issubclass(PluginNotFoundError, PluginSystemError)
        assert issubclass(PluginLoadError, PluginSystemError)
        assert issubclass(PluginDependencyError, PluginSystemError)
        assert issubclass(PluginVersionError, PluginSystemError)
        assert issubclass(PluginUnloadError, PluginSystemError)
        assert issubclass(InvalidPluginStateError, PluginSystemError)
        assert issubclass(PluginInitError, PluginSystemError)
        assert issubclass(PluginDataError, PluginSystemError)
        assert issubclass(PluginValidationError, PluginSystemError)
        assert issubclass(PluginWorkspaceError, PluginSystemError)
        assert issubclass(PluginNameConflictError, PluginSystemError)
