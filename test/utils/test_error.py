"""Tests for ncatbot.utils.error module."""

import pytest
from unittest.mock import patch


class TestNcatBotError:
    """Tests for NcatBotError exception class."""

    def test_ncatbot_error_basic(self):
        """Test basic NcatBotError creation."""
        from ncatbot.utils.error import NcatBotError

        with patch.object(NcatBotError, "logger"):
            with pytest.raises(NcatBotError) as exc_info:
                raise NcatBotError("Test error message", log=False)

            assert str(exc_info.value) == "Test error message"

    def test_ncatbot_error_with_logging(self):
        """Test NcatBotError logs the message."""
        from ncatbot.utils.error import NcatBotError

        with patch.object(NcatBotError, "logger") as mock_logger:
            with patch("ncatbot.utils.error.ncatbot_config") as mock_config:
                mock_config.debug = False

                try:
                    raise NcatBotError("Logged error")
                except NcatBotError:
                    pass

                mock_logger.error.assert_called_once()

    def test_ncatbot_error_no_logging(self):
        """Test NcatBotError with log=False doesn't log."""
        from ncatbot.utils.error import NcatBotError

        with patch.object(NcatBotError, "logger") as mock_logger:
            try:
                raise NcatBotError("No log error", log=False)
            except NcatBotError:
                pass

            mock_logger.error.assert_not_called()

    def test_ncatbot_error_debug_mode_stacktrace(self):
        """Test NcatBotError shows stacktrace in debug mode."""
        from ncatbot.utils.error import NcatBotError

        with patch.object(NcatBotError, "logger") as mock_logger:
            with patch("ncatbot.utils.error.ncatbot_config") as mock_config:
                mock_config.debug = True

                try:
                    raise NcatBotError("Debug error")
                except NcatBotError:
                    pass

                # Both error and info (stacktrace) should be called
                mock_logger.error.assert_called_once()
                mock_logger.info.assert_called_once()


class TestAdapterEventError:
    """Tests for AdapterEventError exception class."""

    def test_adapter_event_error_basic(self):
        """Test basic AdapterEventError creation."""
        from ncatbot.utils.error import AdapterEventError

        with patch.object(AdapterEventError, "logger"):
            with pytest.raises(AdapterEventError) as exc_info:
                raise AdapterEventError("Adapter error", log=False)

            assert str(exc_info.value) == "Adapter error"

    def test_adapter_event_error_with_logging(self):
        """Test AdapterEventError logs the message."""
        from ncatbot.utils.error import AdapterEventError

        with patch.object(AdapterEventError, "logger") as mock_logger:
            with patch("ncatbot.utils.error.ncatbot_config") as mock_config:
                mock_config.debug = False

                try:
                    raise AdapterEventError("Logged adapter error")
                except AdapterEventError:
                    pass

                mock_logger.error.assert_called_once()


class TestNcatBotValueError:
    """Tests for NcatBotValueError exception class."""

    def test_value_error_must_be_false(self):
        """Test NcatBotValueError with must_be=False."""
        from ncatbot.utils.error import NcatBotValueError, NcatBotError

        with patch.object(NcatBotError, "logger"):
            with pytest.raises(NcatBotValueError) as exc_info:
                raise NcatBotValueError("variable", "None", must_be=False)

            assert "variable" in str(exc_info.value)
            assert "不能为" in str(exc_info.value)
            assert "None" in str(exc_info.value)

    def test_value_error_must_be_true(self):
        """Test NcatBotValueError with must_be=True."""
        from ncatbot.utils.error import NcatBotValueError, NcatBotError

        with patch.object(NcatBotError, "logger"):
            with pytest.raises(NcatBotValueError) as exc_info:
                raise NcatBotValueError("config", "valid", must_be=True)

            assert "config" in str(exc_info.value)
            assert "必须" in str(exc_info.value)
            assert "valid" in str(exc_info.value)


class TestNcatBotConnectionError:
    """Tests for NcatBotConnectionError exception class."""

    def test_connection_error_message(self):
        """Test NcatBotConnectionError message format."""
        from ncatbot.utils.error import NcatBotConnectionError

        with pytest.raises(NcatBotConnectionError) as exc_info:
            raise NcatBotConnectionError("Connection refused")

        assert "网络连接错误" in str(exc_info.value)
        assert "Connection refused" in str(exc_info.value)

    def test_connection_error_inheritance(self):
        """Test NcatBotConnectionError inherits from Exception."""
        from ncatbot.utils.error import NcatBotConnectionError

        error = NcatBotConnectionError("test")
        assert isinstance(error, Exception)


class TestErrorInheritance:
    """Tests for error class inheritance."""

    def test_ncatbot_error_is_exception(self):
        """Test NcatBotError inherits from Exception."""
        from ncatbot.utils.error import NcatBotError

        with patch.object(NcatBotError, "logger"):
            error = NcatBotError("test", log=False)
            assert isinstance(error, Exception)

    def test_adapter_event_error_is_exception(self):
        """Test AdapterEventError inherits from Exception."""
        from ncatbot.utils.error import AdapterEventError

        with patch.object(AdapterEventError, "logger"):
            error = AdapterEventError("test", log=False)
            assert isinstance(error, Exception)

    def test_ncatbot_value_error_is_ncatbot_error(self):
        """Test NcatBotValueError inherits from NcatBotError."""
        from ncatbot.utils.error import NcatBotValueError, NcatBotError

        with patch.object(NcatBotError, "logger"):
            error = NcatBotValueError("var", "val")
            assert isinstance(error, NcatBotError)
