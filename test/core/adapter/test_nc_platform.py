"""
NapCat 适配器模块单元测试

测试 ConfigManager、PlatformOps 等核心组件的纯逻辑部分。
"""

import pytest
from pathlib import Path
from unittest.mock import patch

from ncatbot.core.adapter.nc.platform import (
    PlatformOps,
    WindowsOps,
    LinuxOps,
    UnsupportedPlatformError,
)
from ncatbot.core.adapter.nc.auth import LoginStatus


class TestLoginStatus:
    """LoginStatus 枚举测试"""

    def test_enum_values(self):
        """测试枚举值"""
        assert LoginStatus.OK == 0
        assert LoginStatus.NOT_LOGGED_IN == 1
        assert LoginStatus.UIN_MISMATCH == 2
        assert LoginStatus.ABNORMAL == 3

    def test_enum_comparison(self):
        """测试枚举比较"""
        assert LoginStatus.OK < LoginStatus.NOT_LOGGED_IN
        assert LoginStatus.ABNORMAL > LoginStatus.OK

    def test_enum_membership(self):
        """测试枚举成员"""
        assert len(LoginStatus) == 4
        assert LoginStatus.OK in LoginStatus


class TestPlatformOpsFactory:
    """PlatformOps 工厂方法测试"""

    def test_create_windows(self):
        """测试 Windows 平台创建"""
        with patch("platform.system", return_value="Windows"):
            ops = PlatformOps.create()
            assert isinstance(ops, WindowsOps)

    def test_create_linux(self):
        """测试 Linux 平台创建"""
        with patch("platform.system", return_value="Linux"):
            ops = PlatformOps.create()
            assert isinstance(ops, LinuxOps)

    def test_create_unsupported(self):
        """测试不支持的平台"""
        with patch("platform.system", return_value="Darwin"):
            with pytest.raises(UnsupportedPlatformError) as exc_info:
                PlatformOps.create()
            assert "Darwin" in str(exc_info.value)


class TestWindowsOps:
    """WindowsOps 测试"""

    @pytest.fixture
    def ops(self):
        return WindowsOps()

    def test_napcat_dir(self, ops):
        """测试 napcat 目录路径"""
        assert isinstance(ops.napcat_dir, Path)

    def test_config_dir(self, ops):
        """测试配置目录路径"""
        assert ops.config_dir == ops.napcat_dir / "config"

    def test_get_launcher_name_win11(self, ops):
        """测试 Windows 11 启动器名称"""
        with patch("platform.release", return_value="11"):
            with patch("platform.platform", return_value="Windows-11"):
                # 模拟非 Server 版本
                with patch("platform.win32_edition", side_effect=AttributeError):
                    assert ops._get_launcher_name() == "launcher.bat"

    def test_get_launcher_name_win10(self, ops):
        """测试 Windows 10 启动器名称"""
        with patch("platform.release", return_value="10"):
            with patch("platform.platform", return_value="Windows-10"):
                with patch("platform.win32_edition", side_effect=AttributeError):
                    assert ops._get_launcher_name() == "launcher-win10.bat"


class TestLinuxOps:
    """LinuxOps 测试"""

    @pytest.fixture
    def ops(self):
        return LinuxOps()

    def test_napcat_dir_default(self, ops):
        """测试默认 napcat 目录"""
        with patch.object(Path, "exists", return_value=False):
            # 当默认路径不存在时，返回备用路径
            dir_path = ops.napcat_dir
            assert isinstance(dir_path, Path)

    def test_config_dir(self, ops):
        """测试配置目录路径"""
        assert ops.config_dir == ops.napcat_dir / "config"


class TestPlatformOpsCommon:
    """PlatformOps 通用方法测试"""

    @pytest.fixture
    def ops(self):
        """创建一个可测试的平台操作实例"""
        with patch("platform.system", return_value="Windows"):
            return PlatformOps.create()

    def test_is_napcat_installed_true(self, ops):
        """测试 NapCat 已安装"""
        with patch.object(Path, "exists", return_value=True):
            # 需要 mock napcat_dir 属性
            with patch.object(
                type(ops),
                "napcat_dir",
                new_callable=lambda: property(lambda self: Path("/fake/path")),
            ):
                with patch.object(Path, "exists", return_value=True):
                    assert ops.is_napcat_installed() is True

    def test_is_napcat_installed_false(self, ops):
        """测试 NapCat 未安装"""
        with patch.object(
            type(ops),
            "napcat_dir",
            new_callable=lambda: property(lambda self: Path("/nonexistent")),
        ):
            with patch.object(Path, "exists", return_value=False):
                assert ops.is_napcat_installed() is False

    def test_get_installed_version_not_installed(self, ops):
        """测试获取版本 - 未安装"""
        with patch.object(Path, "exists", return_value=False):
            assert ops.get_installed_version() is None

    def test_confirm_action_yes(self, ops):
        """测试用户确认 - 是"""
        with patch("builtins.input", return_value="y"):
            assert ops._confirm_action("Continue?") is True

        with patch("builtins.input", return_value="yes"):
            assert ops._confirm_action("Continue?") is True

        with patch("builtins.input", return_value="Y"):
            assert ops._confirm_action("Continue?") is True

    def test_confirm_action_no(self, ops):
        """测试用户确认 - 否"""
        with patch("builtins.input", return_value="n"):
            assert ops._confirm_action("Continue?") is False

        with patch("builtins.input", return_value=""):
            assert ops._confirm_action("Continue?") is False


class TestUnsupportedPlatformError:
    """UnsupportedPlatformError 异常测试"""

    def test_error_with_system(self):
        """测试带系统名称的错误"""
        error = UnsupportedPlatformError("macOS")
        assert "macOS" in str(error)

    def test_error_default_system(self):
        """测试默认系统名称"""
        with patch("platform.system", return_value="FreeBSD"):
            error = UnsupportedPlatformError()
            assert "FreeBSD" in str(error)
