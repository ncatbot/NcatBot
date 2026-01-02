"""Tests for ncatbot.utils.config.config module."""

import pytest
import tempfile
import os
import yaml
from unittest.mock import patch, MagicMock


class TestConfigCreation:
    """Tests for Config class creation."""

    def test_config_default_values(self):
        """Test Config has correct default values."""
        from ncatbot.utils.config.config import Config

        config = Config()
        assert config.bt_uin == "123456"
        assert config.root == "123456"
        assert config.debug is False
        assert config.websocket_timeout == 15

    def test_config_with_custom_values(self):
        """Test Config with custom values."""
        from ncatbot.utils.config.config import Config
        from ncatbot.utils.config.napcat import NapCatConfig
        from ncatbot.utils.config.plugin import PluginConfig

        config = Config(
            bt_uin="999888777",
            root="111222333",
            debug=True,
            napcat=NapCatConfig(ws_uri="ws://example.com:3001"),
            plugin=PluginConfig(plugins_dir="custom_plugins"),
        )
        assert config.bt_uin == "999888777"
        assert config.root == "111222333"
        assert config.debug is True
        assert config.napcat.ws_uri == "ws://example.com:3001"
        assert config.plugin.plugins_dir == "custom_plugins"


class TestConfigCreateFromFile:
    """Tests for Config.create_from_file method."""

    def test_create_from_valid_file(self):
        """Test creating config from valid YAML file."""
        from ncatbot.utils.config.config import Config

        config_data = {
            "bt_uin": "123456789",
            "root": "987654321",
            "debug": True,
            "napcat": {
                "ws_uri": "ws://localhost:3001",
                "ws_token": "test_token",
            },
            "plugin": {
                "plugins_dir": "test_plugins",
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            f.flush()
            temp_path = f.name

        try:
            config = Config.create_from_file(temp_path)
            assert config.bt_uin == "123456789"
            assert config.root == "987654321"
            assert config.debug is True
            assert config.napcat.ws_token == "test_token"
        finally:
            os.unlink(temp_path)

    def test_create_from_empty_file(self):
        """Test creating config from empty file."""
        from ncatbot.utils.config.config import Config

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("")
            f.flush()
            temp_path = f.name

        try:
            config = Config.create_from_file(temp_path)
            # 应该返回默认配置
            assert config.bt_uin == "123456"
        finally:
            os.unlink(temp_path)

    def test_create_from_nonexistent_file(self):
        """Test creating config from nonexistent file raises error."""
        from ncatbot.utils.config.config import Config

        with pytest.raises(ValueError, match="配置文件不存在"):
            Config.create_from_file("/nonexistent/path/config.yaml")

    def test_create_from_invalid_yaml(self):
        """Test creating config from invalid YAML raises error."""
        from ncatbot.utils.config.config import Config

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: yaml: content: [")
            f.flush()
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="配置文件格式无效"):
                Config.create_from_file(temp_path)
        finally:
            os.unlink(temp_path)

    def test_create_from_file_warns_unknown_keys(self):
        """Test create_from_file warns on unknown keys."""
        from ncatbot.utils.config.config import Config

        config_data = {
            "bt_uin": "123456789",
            "unknown_key": "unknown_value",
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            f.flush()
            temp_path = f.name

        try:
            with patch("ncatbot.utils.config.config.logger") as mock_logger:
                Config.create_from_file(temp_path)
                # 应该警告未知配置项
                mock_logger.warning.assert_called()
        finally:
            os.unlink(temp_path)


class TestConfigAsDict:
    """Tests for Config.asdict method."""

    def test_asdict_includes_nested_configs(self):
        """Test asdict includes nested napcat and plugin configs."""
        from ncatbot.utils.config.config import Config

        config = Config()
        data = config.asdict()

        assert "napcat" in data
        assert "plugin" in data
        assert isinstance(data["napcat"], dict)
        assert isinstance(data["plugin"], dict)

    def test_asdict_excludes_private_fields(self):
        """Test asdict excludes private fields."""
        from ncatbot.utils.config.config import Config

        config = Config()
        data = config.asdict()

        assert "_default_bt_uin" not in data
        assert "_default_root" not in data


class TestConfigGetUriWithToken:
    """Tests for Config.get_uri_with_token method."""

    def test_get_uri_with_simple_token(self):
        """Test get_uri_with_token with simple token."""
        from ncatbot.utils.config.config import Config
        from ncatbot.utils.config.napcat import NapCatConfig

        config = Config(
            napcat=NapCatConfig(
                ws_uri="ws://localhost:3001",
                ws_token="simple_token",
            )
        )

        uri = config.get_uri_with_token()
        assert uri == "ws://localhost:3001/?access_token=simple_token"

    def test_get_uri_with_special_chars_token(self):
        """Test get_uri_with_token with special characters in token."""
        from ncatbot.utils.config.config import Config
        from ncatbot.utils.config.napcat import NapCatConfig

        config = Config(
            napcat=NapCatConfig(
                ws_uri="ws://localhost:3001",
                ws_token="token+with/special=chars",
            )
        )

        uri = config.get_uri_with_token()
        assert "access_token=" in uri
        assert "+" not in uri.split("access_token=")[1] or "%2B" in uri

    def test_get_uri_strips_trailing_slash(self):
        """Test get_uri_with_token strips trailing slash."""
        from ncatbot.utils.config.config import Config
        from ncatbot.utils.config.napcat import NapCatConfig

        config = Config(
            napcat=NapCatConfig(
                ws_uri="ws://localhost:3001/",
                ws_token="token",
            )
        )

        uri = config.get_uri_with_token()
        assert "3001//" not in uri


class TestConfigLoad:
    """Tests for Config.load method."""

    def test_load_returns_config_instance(self):
        """Test load returns Config instance."""
        from ncatbot.utils.config.config import Config

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump({"bt_uin": "test123"}, f)
            f.flush()
            temp_path = f.name

        try:
            with patch("ncatbot.utils.config.config.CONFIG_PATH", temp_path):
                # 重新加载模块以使用新的 CONFIG_PATH
                config = Config.load()
                assert isinstance(config, Config)
        finally:
            os.unlink(temp_path)

    def test_load_handles_missing_file(self):
        """Test load handles missing file gracefully."""
        from ncatbot.utils.config.config import Config

        with patch("ncatbot.utils.config.config.CONFIG_PATH", "/nonexistent/config.yaml"):
            config = Config.load()
            # 应该返回默认配置
            assert isinstance(config, Config)
            assert config.bt_uin == "123456"


class TestConfigIsNapcatLocal:
    """Tests for Config.is_napcat_local method."""

    def test_is_napcat_local_localhost(self):
        """Test is_napcat_local returns True for localhost."""
        from ncatbot.utils.config.config import Config
        from ncatbot.utils.config.napcat import NapCatConfig

        napcat = NapCatConfig(ws_uri="ws://localhost:3001")
        napcat._standardize_ws_uri()
        config = Config(napcat=napcat)
        assert config.is_napcat_local() is True

    def test_is_napcat_local_127(self):
        """Test is_napcat_local returns True for 127.0.0.1."""
        from ncatbot.utils.config.config import Config
        from ncatbot.utils.config.napcat import NapCatConfig

        napcat = NapCatConfig(ws_uri="ws://127.0.0.1:3001")
        napcat._standardize_ws_uri()
        config = Config(napcat=napcat)
        assert config.is_napcat_local() is True

    def test_is_napcat_local_remote(self):
        """Test is_napcat_local returns False for remote host."""
        from ncatbot.utils.config.config import Config
        from ncatbot.utils.config.napcat import NapCatConfig

        napcat = NapCatConfig(ws_uri="ws://192.168.1.100:3001")
        napcat._standardize_ws_uri()
        config = Config(napcat=napcat)
        assert config.is_napcat_local() is False


class TestConfigSetters:
    """Tests for Config setter methods."""

    def test_set_bot_uin(self):
        """Test set_bot_uin method."""
        from ncatbot.utils.config.config import Config

        config = Config()
        config.set_bot_uin(999888777)
        assert config.bt_uin == "999888777"

    def test_set_root(self):
        """Test set_root method."""
        from ncatbot.utils.config.config import Config

        config = Config()
        config.set_root(111222333)
        assert config.root == "111222333"

    def test_set_ws_uri(self):
        """Test set_ws_uri method."""
        from ncatbot.utils.config.config import Config

        config = Config()
        config.set_ws_uri("ws://newhost:3002")
        assert config.napcat.ws_uri == "ws://newhost:3002"

    def test_set_webui_uri(self):
        """Test set_webui_uri method."""
        from ncatbot.utils.config.config import Config

        config = Config()
        config.set_webui_uri("http://newhost:6100")
        assert config.napcat.webui_uri == "http://newhost:6100"

    def test_set_ws_token(self):
        """Test set_ws_token method."""
        from ncatbot.utils.config.config import Config

        config = Config()
        config.set_ws_token("new_token")
        assert config.napcat.ws_token == "new_token"

    def test_set_webui_token(self):
        """Test set_webui_token method."""
        from ncatbot.utils.config.config import Config

        config = Config()
        config.set_webui_token("new_webui_token")
        assert config.napcat.webui_token == "new_webui_token"

    def test_set_ws_listen_ip(self):
        """Test set_ws_listen_ip method."""
        from ncatbot.utils.config.config import Config

        config = Config()
        config.set_ws_listen_ip("0.0.0.0")
        assert config.napcat.ws_listen_ip == "0.0.0.0"


class TestConfigUpdateFromFile:
    """Tests for Config.update_from_file method."""

    def test_update_from_file(self):
        """Test update_from_file updates config."""
        from ncatbot.utils.config.config import Config

        config = Config(bt_uin="original")

        config_data = {"bt_uin": "updated", "debug": True}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            f.flush()
            temp_path = f.name

        try:
            config.update_from_file(temp_path)
            assert config.bt_uin == "updated"
            assert config.debug is True
        finally:
            os.unlink(temp_path)


class TestConfigStr:
    """Tests for Config.__str__ method."""

    def test_str_contains_key_info(self):
        """Test __str__ contains key configuration info."""
        from ncatbot.utils.config.config import Config

        config = Config(bt_uin="123456789", root="987654321")
        result = str(config)
        assert "123456789" in result
        assert "987654321" in result
        assert "BOTQQ" in result
        assert "ROOT" in result

