"""Tests for ncatbot.utils.status module."""

import logging
import threading
import pytest
from unittest.mock import patch


class TestStatus:
    """Tests for Status class."""

    @pytest.fixture
    def fresh_status(self):
        """Create a fresh Status instance for each test."""
        from ncatbot.utils.status import Status

        return Status()

    def test_init_default_values(self, fresh_status):
        """Test that Status initializes with correct default values."""
        assert fresh_status.exit is False
        assert fresh_status.current_github_proxy is None
        assert fresh_status.global_access_manager is None
        assert len(fresh_status._registered_loggers) == 0

    def test_set_attribute(self, fresh_status):
        """Test setting an attribute via set method."""
        fresh_status.set("exit", True)
        assert fresh_status.exit is True

        fresh_status.set("current_github_proxy", "https://proxy.example.com")
        assert fresh_status.current_github_proxy == "https://proxy.example.com"

    def test_set_custom_attribute(self, fresh_status):
        """Test setting a custom attribute."""
        fresh_status.set("custom_key", "custom_value")
        assert fresh_status.custom_key == "custom_value"

    def test_register_logger(self, fresh_status):
        """Test registering a logger."""
        fresh_status.register_logger("test_logger")
        assert fresh_status.is_registered_logger("test_logger") is True
        assert fresh_status.is_registered_logger("non_existent") is False

    def test_register_multiple_loggers(self, fresh_status):
        """Test registering multiple loggers."""
        fresh_status.register_logger("logger1")
        fresh_status.register_logger("logger2")
        fresh_status.register_logger("logger3")

        assert fresh_status.is_registered_logger("logger1") is True
        assert fresh_status.is_registered_logger("logger2") is True
        assert fresh_status.is_registered_logger("logger3") is True

    def test_register_logger_duplicate(self, fresh_status):
        """Test registering the same logger twice doesn't cause issues."""
        fresh_status.register_logger("dup_logger")
        fresh_status.register_logger("dup_logger")

        loggers = fresh_status.get_registered_loggers()
        assert (
            loggers.count("dup_logger")
            if isinstance(loggers, list)
            else "dup_logger" in loggers
        )

    def test_get_registered_loggers_returns_copy(self, fresh_status):
        """Test that get_registered_loggers returns a copy."""
        fresh_status.register_logger("test_logger")

        loggers = fresh_status.get_registered_loggers()
        loggers.add("should_not_affect_original")

        assert "should_not_affect_original" not in fresh_status.get_registered_loggers()

    def test_update_logger_level_debug_mode(self, fresh_status):
        """Test updating logger levels in debug mode."""
        with patch("ncatbot.utils.config.ncatbot_config") as mock_config:
            mock_config.debug = True

            # Register a logger first
            fresh_status.register_logger("test_update_logger")

            # Create the actual logger
            logger = logging.getLogger("test_update_logger")
            logger.setLevel(logging.WARNING)  # Set to non-debug level

            fresh_status.update_logger_level()

            assert logger.level == logging.DEBUG

    def test_update_logger_level_normal_mode(self, fresh_status):
        """Test updating logger levels in normal mode."""
        with patch("ncatbot.utils.config.ncatbot_config") as mock_config:
            mock_config.debug = False

            # Register a logger first
            fresh_status.register_logger("test_normal_logger")

            # Create the actual logger
            logger = logging.getLogger("test_normal_logger")
            logger.setLevel(logging.DEBUG)  # Set to debug level

            fresh_status.update_logger_level()

            assert logger.level == logging.INFO

    def test_thread_safety_set(self, fresh_status):
        """Test thread safety of set method."""
        results = []

        def set_value(i):
            fresh_status.set(f"key_{i}", i)
            results.append(i)

        threads = [threading.Thread(target=set_value, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(results) == 10

    def test_thread_safety_register_logger(self, fresh_status):
        """Test thread safety of register_logger."""

        def register(name):
            fresh_status.register_logger(name)

        threads = [
            threading.Thread(target=register, args=(f"logger_{i}",)) for i in range(10)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        loggers = fresh_status.get_registered_loggers()
        assert len(loggers) == 10


class TestGlobalStatus:
    """Tests for the global status singleton."""

    def test_global_status_exists(self):
        """Test that global status singleton is accessible."""
        from ncatbot.utils.status import status

        assert status is not None

    def test_global_status_is_status_instance(self):
        """Test that global status is a Status instance."""
        from ncatbot.utils.status import status, Status

        assert isinstance(status, Status)
