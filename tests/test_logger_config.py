"""Tests for logger_config module."""

import logging
import os
from pathlib import Path
from unittest import mock

import pytest

from imessage_analysis.logger_config import get_log_level, setup_logging


class TestGetLogLevel:
    """Tests for get_log_level function."""

    def test_default_is_info(self):
        """Test that default log level is INFO when env var not set."""
        with mock.patch.dict(os.environ, {}, clear=True):
            # Remove LOG_LEVEL if it exists
            os.environ.pop("LOG_LEVEL", None)
            assert get_log_level() == logging.INFO

    def test_debug_level(self):
        """Test DEBUG level from environment."""
        with mock.patch.dict(os.environ, {"LOG_LEVEL": "DEBUG"}):
            assert get_log_level() == logging.DEBUG

    def test_info_level(self):
        """Test INFO level from environment."""
        with mock.patch.dict(os.environ, {"LOG_LEVEL": "INFO"}):
            assert get_log_level() == logging.INFO

    def test_warning_level(self):
        """Test WARNING level from environment."""
        with mock.patch.dict(os.environ, {"LOG_LEVEL": "WARNING"}):
            assert get_log_level() == logging.WARNING

    def test_error_level(self):
        """Test ERROR level from environment."""
        with mock.patch.dict(os.environ, {"LOG_LEVEL": "ERROR"}):
            assert get_log_level() == logging.ERROR

    def test_critical_level(self):
        """Test CRITICAL level from environment."""
        with mock.patch.dict(os.environ, {"LOG_LEVEL": "CRITICAL"}):
            assert get_log_level() == logging.CRITICAL

    def test_case_insensitive(self):
        """Test that log level parsing is case-insensitive."""
        with mock.patch.dict(os.environ, {"LOG_LEVEL": "debug"}):
            assert get_log_level() == logging.DEBUG

        with mock.patch.dict(os.environ, {"LOG_LEVEL": "Debug"}):
            assert get_log_level() == logging.DEBUG

    def test_invalid_level_falls_back_to_info(self):
        """Test that invalid log level falls back to INFO."""
        with mock.patch.dict(os.environ, {"LOG_LEVEL": "INVALID"}):
            assert get_log_level() == logging.INFO

        with mock.patch.dict(os.environ, {"LOG_LEVEL": ""}):
            assert get_log_level() == logging.INFO


class TestSetupLogging:
    """Tests for setup_logging function."""

    def test_setup_logging_default(self):
        """Test setup_logging with default parameters doesn't raise."""
        setup_logging()
        root = logging.getLogger()
        assert root is not None

    def test_setup_logging_custom_level(self):
        """Test setup_logging accepts custom level."""
        setup_logging(level=logging.DEBUG)
        root = logging.getLogger()
        assert root.level == logging.DEBUG

    def test_setup_logging_custom_format(self):
        """Test setup_logging with custom format string."""
        custom_format = "%(levelname)s: %(message)s"
        setup_logging(format_string=custom_format)
        root = logging.getLogger()
        assert root is not None

    def test_setup_logging_with_log_file(self, tmp_path: Path):
        """Test setup_logging with log file output."""
        log_file = tmp_path / "test.log"
        setup_logging(log_file=str(log_file))

        # Log something to trigger file creation
        logger = logging.getLogger("test_file_logger")
        logger.info("Test message")

        # File handler should be configured (file may not exist until first write)
        root = logging.getLogger()
        handler_types = [type(h).__name__ for h in root.handlers]
        assert "RotatingFileHandler" in handler_types

    def test_setup_logging_all_parameters(self, tmp_path: Path):
        """Test setup_logging with all parameters specified."""
        log_file = tmp_path / "full_test.log"
        setup_logging(
            level=logging.WARNING,
            format_string="%(message)s",
            log_file=str(log_file),
        )
        root = logging.getLogger()
        assert root.level == logging.WARNING

    def test_setup_logging_respects_env_var(self):
        """Test that setup_logging uses LOG_LEVEL env var when level not specified."""
        with mock.patch.dict(os.environ, {"LOG_LEVEL": "DEBUG"}):
            setup_logging()
            root = logging.getLogger()
            assert root.level == logging.DEBUG

    def test_setup_logging_explicit_level_overrides_env(self):
        """Test that explicit level parameter overrides env var."""
        with mock.patch.dict(os.environ, {"LOG_LEVEL": "DEBUG"}):
            setup_logging(level=logging.ERROR)
            root = logging.getLogger()
            assert root.level == logging.ERROR

    def test_setup_logging_can_be_called_multiple_times(self):
        """Test that setup_logging can be called multiple times safely."""
        # This should not raise - dictConfig handles reconfiguration
        setup_logging(level=logging.INFO)
        setup_logging(level=logging.DEBUG)
        setup_logging(level=logging.WARNING)

        root = logging.getLogger()
        assert root.level == logging.WARNING

    def test_module_loggers_not_disabled(self):
        """Test that existing module loggers are not disabled by setup_logging."""
        # Create a module logger before setup
        module_logger = logging.getLogger("test_module")
        module_logger.setLevel(logging.DEBUG)

        # Call setup_logging
        setup_logging()

        # Module logger should still work (disable_existing_loggers=False)
        assert module_logger.isEnabledFor(logging.DEBUG)
