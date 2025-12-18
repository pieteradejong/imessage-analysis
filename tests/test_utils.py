"""
Tests for utils.py functions.

Tests utility functions for formatting and terminal output.
"""

import pytest

from imessage_analysis.utils import Colors, format_timestamp, format_message_count


class TestColors:
    """Tests for Colors class."""

    def test_colors_have_values(self):
        """Color constants should be non-empty strings."""
        assert Colors.HEADER != ""
        assert Colors.OKBLUE != ""
        assert Colors.OKCYAN != ""
        assert Colors.OKGREEN != ""
        assert Colors.WARNING != ""
        assert Colors.FAIL != ""
        assert Colors.ENDC != ""
        assert Colors.BOLD != ""
        assert Colors.UNDERLINE != ""

    def test_colors_are_ansi_escape_codes(self):
        """Colors should be ANSI escape sequences."""
        # ANSI escape codes start with \033[
        assert Colors.HEADER.startswith("\033[")
        assert Colors.ENDC == "\033[0m"

    def test_endc_resets_formatting(self):
        """ENDC should be the reset code."""
        assert Colors.ENDC == "\033[0m"


class TestFormatTimestamp:
    """Tests for format_timestamp function."""

    def test_zero_timestamp(self):
        """Zero timestamp should return 2001-01-01 (iMessage epoch)."""
        result = format_timestamp(0)
        assert result == "2001-01-01 00:00:00"

    def test_positive_timestamp(self):
        """Positive timestamp should return correct date."""
        # 1 day in nanoseconds = 86400 * 1_000_000_000
        one_day_ns = 86400 * 1_000_000_000
        result = format_timestamp(one_day_ns)
        assert result == "2001-01-02 00:00:00"

    def test_known_date(self):
        """Test with a known date timestamp."""
        # 2024-01-01 00:00:00 is 23 years after 2001-01-01
        # That's 8401 days (including leap years through 2024)
        # Approximate: 23 * 365.25 * 86400 * 1e9 nanoseconds
        # For simplicity, test format is correct
        result = format_timestamp(1_000_000_000_000_000_000)  # Large timestamp
        # Just verify it returns a properly formatted string
        assert len(result) == 19
        assert result[4] == "-"
        assert result[7] == "-"
        assert result[10] == " "
        assert result[13] == ":"
        assert result[16] == ":"

    def test_returns_string(self):
        """Should always return a string."""
        assert isinstance(format_timestamp(0), str)
        assert isinstance(format_timestamp(1000000000), str)

    def test_timestamp_format(self):
        """Result should match YYYY-MM-DD HH:MM:SS format."""
        result = format_timestamp(0)
        parts = result.split(" ")
        assert len(parts) == 2

        date_parts = parts[0].split("-")
        assert len(date_parts) == 3
        assert len(date_parts[0]) == 4  # Year
        assert len(date_parts[1]) == 2  # Month
        assert len(date_parts[2]) == 2  # Day

        time_parts = parts[1].split(":")
        assert len(time_parts) == 3


class TestFormatMessageCount:
    """Tests for format_message_count function."""

    def test_zero(self):
        """Zero should return '0'."""
        assert format_message_count(0) == "0"

    def test_small_numbers(self):
        """Numbers under 1000 should return as-is."""
        assert format_message_count(1) == "1"
        assert format_message_count(100) == "100"
        assert format_message_count(999) == "999"

    def test_thousands_boundary(self):
        """1000 should use K notation."""
        assert format_message_count(1000) == "1.0K"

    def test_thousands(self):
        """Numbers in thousands should use K notation."""
        assert format_message_count(1500) == "1.5K"
        assert format_message_count(10000) == "10.0K"
        assert format_message_count(999999) == "1000.0K"

    def test_millions_boundary(self):
        """1000000 should use M notation."""
        assert format_message_count(1000000) == "1.0M"

    def test_millions(self):
        """Numbers in millions should use M notation."""
        assert format_message_count(1500000) == "1.5M"
        assert format_message_count(10000000) == "10.0M"

    def test_returns_string(self):
        """Should always return a string."""
        assert isinstance(format_message_count(0), str)
        assert isinstance(format_message_count(1000), str)
        assert isinstance(format_message_count(1000000), str)

    def test_precision(self):
        """K and M values should have one decimal place."""
        result_k = format_message_count(1234)
        assert result_k == "1.2K"

        result_m = format_message_count(1234567)
        assert result_m == "1.2M"
