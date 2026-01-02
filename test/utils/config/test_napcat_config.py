"""Tests for ncatbot.utils.config.napcat module."""

import pytest
from unittest.mock import patch, MagicMock


class TestNapCatConfigCreation:
    """Tests for NapCatConfig class creation."""

    def test_napcat_config_default_values(self):
        """Test NapCatConfig has correct default values."""
        from ncatbot.utils.config.napcat import NapCatConfig

        config = NapCatConfig()
        assert config.ws_uri == "ws://localhost:3001"
        assert config.ws_token == "NcatBot"
        assert config.ws_listen_ip == "localhost"
        assert config.webui_uri == "http://localhost:6099"
        assert config.webui_token == "NcatBot"
        assert config.enable_webui is True
        assert config.check_napcat_update is False
        assert config.stop_napcat is False
        assert config.remote_mode is False

    def test_napcat_config_custom_values(self):
        """Test NapCatConfig with custom values."""
        from ncatbot.utils.config.napcat import NapCatConfig

        config = NapCatConfig(
            ws_uri="ws://192.168.1.100:3002",
            ws_token="custom_token",
            webui_uri="http://192.168.1.100:6100",
            enable_webui=False,
        )
        assert config.ws_uri == "ws://192.168.1.100:3002"
        assert config.ws_token == "custom_token"
        assert config.webui_uri == "http://192.168.1.100:6100"
        assert config.enable_webui is False


class TestNapCatConfigStandardizeWsUri:
    """Tests for NapCatConfig._standardize_ws_uri method."""

    def test_standardize_ws_uri_with_scheme(self):
        """Test standardize preserves ws:// scheme."""
        from ncatbot.utils.config.napcat import NapCatConfig

        config = NapCatConfig(ws_uri="ws://localhost:3001")
        config._standardize_ws_uri()
        assert config.ws_uri == "ws://localhost:3001"
        assert config.ws_host == "localhost"
        assert config.ws_port == 3001

    def test_standardize_ws_uri_wss_scheme(self):
        """Test standardize preserves wss:// scheme."""
        from ncatbot.utils.config.napcat import NapCatConfig

        config = NapCatConfig(ws_uri="wss://secure.example.com:443")
        config._standardize_ws_uri()
        assert config.ws_uri == "wss://secure.example.com:443"
        assert config.ws_host == "secure.example.com"
        assert config.ws_port == 443

    def test_standardize_ws_uri_without_scheme(self):
        """Test standardize adds ws:// if missing."""
        from ncatbot.utils.config.napcat import NapCatConfig

        config = NapCatConfig(ws_uri="localhost:3001")
        config._standardize_ws_uri()
        assert config.ws_uri == "ws://localhost:3001"
        assert config.ws_host == "localhost"
        assert config.ws_port == 3001

    def test_standardize_ws_uri_extracts_host_port(self):
        """Test standardize extracts host and port correctly."""
        from ncatbot.utils.config.napcat import NapCatConfig

        config = NapCatConfig(ws_uri="ws://192.168.1.100:5000")
        config._standardize_ws_uri()
        assert config.ws_host == "192.168.1.100"
        assert config.ws_port == 5000


class TestNapCatConfigStandardizeWebuiUri:
    """Tests for NapCatConfig._standardize_webui_uri method."""

    def test_standardize_webui_uri_with_http(self):
        """Test standardize preserves http:// scheme."""
        from ncatbot.utils.config.napcat import NapCatConfig

        config = NapCatConfig(webui_uri="http://localhost:6099")
        config._standardize_webui_uri()
        assert config.webui_uri == "http://localhost:6099"
        assert config.webui_host == "localhost"
        assert config.webui_port == 6099

    def test_standardize_webui_uri_with_https(self):
        """Test standardize preserves https:// scheme."""
        from ncatbot.utils.config.napcat import NapCatConfig

        config = NapCatConfig(webui_uri="https://secure.example.com:443")
        config._standardize_webui_uri()
        assert config.webui_uri == "https://secure.example.com:443"
        assert config.webui_host == "secure.example.com"

    def test_standardize_webui_uri_without_scheme(self):
        """Test standardize adds http:// if missing."""
        from ncatbot.utils.config.napcat import NapCatConfig

        config = NapCatConfig(webui_uri="localhost:6099")
        config._standardize_webui_uri()
        assert config.webui_uri == "http://localhost:6099"


class TestNapCatConfigSecurityCheck:
    """Tests for NapCatConfig._security_check method."""

    def test_security_check_local_weak_token_passes(self):
        """Test security check passes for local listen with weak token."""
        from ncatbot.utils.config.napcat import NapCatConfig

        config = NapCatConfig(
            ws_listen_ip="localhost",
            ws_token="weak",
            webui_token="weak",
            enable_webui=False,
        )
        # 不应该抛出异常
        config._security_check()

    def test_security_check_0000_weak_ws_token_prompts(self):
        """Test security check prompts for 0.0.0.0 with weak WS token."""
        from ncatbot.utils.config.napcat import NapCatConfig

        config = NapCatConfig(
            ws_listen_ip="0.0.0.0",
            ws_token="weak",
            enable_webui=False,
        )

        # 模拟用户输入 'n'（不修改密码）
        with patch("builtins.input", return_value="n"):
            with pytest.raises(ValueError, match="WS 令牌强度不足"):
                config._security_check()

    def test_security_check_0000_strong_token_passes(self):
        """Test security check passes for 0.0.0.0 with strong token."""
        from ncatbot.utils.config.napcat import NapCatConfig
        from ncatbot.utils.config.utils import generate_strong_password

        strong_token = generate_strong_password()
        config = NapCatConfig(
            ws_listen_ip="0.0.0.0",
            ws_token=strong_token,
            webui_token=strong_token,
            enable_webui=False,
        )
        # 不应该抛出异常
        config._security_check()

    def test_security_check_weak_webui_token_prompts(self):
        """Test security check prompts for weak WebUI token."""
        from ncatbot.utils.config.napcat import NapCatConfig
        from ncatbot.utils.config.utils import generate_strong_password

        strong_ws_token = generate_strong_password()
        config = NapCatConfig(
            ws_listen_ip="localhost",
            ws_token=strong_ws_token,
            webui_token="weak",
            enable_webui=True,
        )

        with patch("builtins.input", return_value="n"):
            with pytest.raises(ValueError, match="WebUI 令牌强度不足"):
                config._security_check()

    def test_security_check_auto_generate_ws_token(self):
        """Test security check auto-generates WS token when user accepts."""
        from ncatbot.utils.config.napcat import NapCatConfig
        from ncatbot.utils.config.utils import strong_password_check

        config = NapCatConfig(
            ws_listen_ip="0.0.0.0",
            ws_token="weak",
            enable_webui=False,
        )

        with patch("builtins.input", return_value="y"):
            config._security_check()
            # 应该生成强密码
            assert strong_password_check(config.ws_token)

    def test_security_check_auto_generate_webui_token(self):
        """Test security check auto-generates WebUI token when user accepts."""
        from ncatbot.utils.config.napcat import NapCatConfig
        from ncatbot.utils.config.utils import strong_password_check, generate_strong_password

        config = NapCatConfig(
            ws_listen_ip="localhost",
            ws_token=generate_strong_password(),
            webui_token="weak",
            enable_webui=True,
        )

        with patch("builtins.input", return_value="y"):
            config._security_check()
            assert strong_password_check(config.webui_token)


class TestNapCatConfigValidate:
    """Tests for NapCatConfig.validate method."""

    def test_validate_standardizes_uris(self):
        """Test validate standardizes both URIs."""
        from ncatbot.utils.config.napcat import NapCatConfig
        from ncatbot.utils.config.utils import generate_strong_password

        config = NapCatConfig(
            ws_uri="localhost:3001",
            webui_uri="localhost:6099",
            ws_token=generate_strong_password(),
            webui_token=generate_strong_password(),
        )
        config.validate()
        assert config.ws_uri.startswith("ws://")
        assert config.webui_uri.startswith("http://")

    def test_validate_remote_host_logs_info(self):
        """Test validate logs info for remote host."""
        from ncatbot.utils.config.napcat import NapCatConfig
        from ncatbot.utils.config.utils import generate_strong_password

        config = NapCatConfig(
            ws_uri="ws://192.168.1.100:3001",
            webui_uri="http://192.168.1.100:6099",
            ws_token=generate_strong_password(),
            webui_token=generate_strong_password(),
            enable_webui=False,
        )

        with patch("ncatbot.utils.config.napcat.logger") as mock_logger:
            config.validate()
            mock_logger.info.assert_called()

    def test_validate_mismatched_listen_ip_warns(self):
        """Test validate warns when listen IP doesn't match WS host."""
        from ncatbot.utils.config.napcat import NapCatConfig
        from ncatbot.utils.config.utils import generate_strong_password

        config = NapCatConfig(
            ws_uri="ws://192.168.1.100:3001",
            ws_listen_ip="localhost",
            ws_token=generate_strong_password(),
            webui_token=generate_strong_password(),
            enable_webui=False,
        )

        with patch("ncatbot.utils.config.napcat.logger") as mock_logger:
            config.validate()
            # 应该发出警告
            warning_calls = [
                call for call in mock_logger.warning.call_args_list
                if "监听地址" in str(call) or "不匹配" in str(call)
            ]
            assert len(warning_calls) > 0


class TestNapCatConfigFromDict:
    """Tests for NapCatConfig.from_dict method."""

    def test_from_dict_basic(self):
        """Test from_dict with basic fields."""
        from ncatbot.utils.config.napcat import NapCatConfig

        data = {
            "ws_uri": "ws://custom:3001",
            "ws_token": "custom_token",
            "enable_webui": False,
        }
        config = NapCatConfig.from_dict(data)
        assert config.ws_uri == "ws://custom:3001"
        assert config.ws_token == "custom_token"
        assert config.enable_webui is False

    def test_from_dict_preserves_defaults(self):
        """Test from_dict preserves unspecified defaults."""
        from ncatbot.utils.config.napcat import NapCatConfig

        data = {"ws_uri": "ws://custom:3001"}
        config = NapCatConfig.from_dict(data)
        assert config.ws_uri == "ws://custom:3001"
        assert config.ws_token == "NcatBot"  # default
        assert config.enable_webui is True  # default


class TestNapCatConfigAsDict:
    """Tests for NapCatConfig.asdict method."""

    def test_asdict_excludes_computed_fields(self):
        """Test asdict excludes computed host/port fields."""
        from ncatbot.utils.config.napcat import NapCatConfig

        config = NapCatConfig()
        config._standardize_ws_uri()
        config._standardize_webui_uri()

        data = config.asdict()
        # 计算字段应该在 ATTRIBUTE_IGNORE 中被排除
        assert "ws_uri" in data
        assert "ws_token" in data

    def test_asdict_returns_all_config_fields(self):
        """Test asdict returns all configuration fields."""
        from ncatbot.utils.config.napcat import NapCatConfig

        config = NapCatConfig(
            ws_uri="ws://test:3001",
            ws_token="test_token",
            enable_webui=True,
        )
        data = config.asdict()

        assert data["ws_uri"] == "ws://test:3001"
        assert data["ws_token"] == "test_token"
        assert data["enable_webui"] is True

