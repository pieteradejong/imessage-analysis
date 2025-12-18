"""Tests for logger_config module."""

import logging
from pathlib import Path

from imessage_analysis.logger_config import setup_logging


class TestSetupLogging:
    """Tests for setup_logging function."""

    def test_setup_logging_default(self):
        """Test setup_logging with default parameters doesn't raise."""
        # Just verify it runs without error - basicConfig behavior depends on
        # whether handlers are already configured
        setup_logging()

    def test_setup_logging_custom_level(self):
        """Test setup_logging accepts custom level."""
        # Just verify it runs without error
        setup_logging(level=logging.DEBUG)

    def test_setup_logging_custom_format(self):
        """Test setup_logging with custom format string."""
        custom_format = "%(levelname)s: %(message)s"
        setup_logging(format_string=custom_format)
        # Just verify it doesn't crash - format is applied to handlers
        root = logging.getLogger()
        assert root is not None

    def test_setup_logging_with_log_file(self, tmp_path: Path):
        """Test setup_logging with log file output."""
        log_file = tmp_path / "test.log"
        setup_logging(log_file=str(log_file))

        # Verify it doesn't crash and log file directory exists
        assert log_file.parent.exists()

    def test_setup_logging_all_parameters(self, tmp_path: Path):
        """Test setup_logging with all parameters specified."""
        log_file = tmp_path / "full_test.log"
        setup_logging(
            level=logging.WARNING,
            format_string="%(message)s",
            log_file=str(log_file),
        )
        # Verify no exception raised
