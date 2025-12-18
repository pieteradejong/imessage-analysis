"""
Tests for visualization.py plotting functions.

Tests that visualization functions handle missing plotly gracefully.
"""

from unittest.mock import patch, MagicMock

import pytest


class TestPlotlyAvailability:
    """Tests for PLOTLY_AVAILABLE flag handling."""

    def test_plotly_available_flag_exists(self):
        """PLOTLY_AVAILABLE flag should exist."""
        from imessage_analysis import visualization

        assert hasattr(visualization, "PLOTLY_AVAILABLE")

    def test_plotly_available_is_boolean(self):
        """PLOTLY_AVAILABLE should be a boolean."""
        from imessage_analysis import visualization

        assert isinstance(visualization.PLOTLY_AVAILABLE, bool)


class TestPlotMessagesOverTime:
    """Tests for plot_messages_over_time function."""

    def test_handles_empty_messages(self):
        """Should handle empty messages list."""
        from imessage_analysis.visualization import plot_messages_over_time

        # Should not raise
        plot_messages_over_time([])

    def test_handles_messages_list(self):
        """Should handle list of messages."""
        from imessage_analysis.visualization import plot_messages_over_time

        messages = [
            {"date": "2024-01-15 10:00:00", "text": "Hello"},
            {"date": "2024-01-15 11:00:00", "text": "World"},
        ]
        # Should not raise
        plot_messages_over_time(messages)

    def test_handles_output_file_parameter(self):
        """Should accept output_file parameter."""
        from imessage_analysis.visualization import plot_messages_over_time

        # Should not raise
        plot_messages_over_time([], output_file="/tmp/test.html")

    @patch("imessage_analysis.visualization.PLOTLY_AVAILABLE", False)
    def test_handles_missing_plotly(self):
        """Should handle case when plotly is not available."""
        # Re-import after patching
        from imessage_analysis.visualization import plot_messages_over_time

        # Should not raise even without plotly
        plot_messages_over_time([])


class TestPlotMessageDistributionByChat:
    """Tests for plot_message_distribution_by_chat function."""

    def test_handles_empty_stats(self):
        """Should handle empty stats list."""
        from imessage_analysis.visualization import plot_message_distribution_by_chat

        # Should not raise
        plot_message_distribution_by_chat([])

    def test_handles_stats_list(self):
        """Should handle list of chat statistics."""
        from imessage_analysis.visualization import plot_message_distribution_by_chat

        stats = [
            {"chat_identifier": "+14155551234", "message_count": 100},
            {"chat_identifier": "+14155555678", "message_count": 200},
        ]
        # Should not raise
        plot_message_distribution_by_chat(stats)

    def test_handles_output_file_parameter(self):
        """Should accept output_file parameter."""
        from imessage_analysis.visualization import plot_message_distribution_by_chat

        # Should not raise
        plot_message_distribution_by_chat([], output_file="/tmp/test.html")

    @patch("imessage_analysis.visualization.PLOTLY_AVAILABLE", False)
    def test_handles_missing_plotly(self):
        """Should handle case when plotly is not available."""
        from imessage_analysis.visualization import plot_message_distribution_by_chat

        # Should not raise even without plotly
        plot_message_distribution_by_chat([])
