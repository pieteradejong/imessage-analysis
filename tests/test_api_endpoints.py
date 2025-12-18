"""
Tests for FastAPI endpoints.

Tests the API routes using FastAPI's TestClient.
"""

from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from imessage_analysis.api import app


@pytest.fixture
def client():
    """Create a TestClient for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_db():
    """Create a mock DatabaseConnection."""
    db = MagicMock()
    db.config.db_path_str = "/fake/path/chat.db"
    db.use_memory = False
    db.close = MagicMock()
    return db


class TestHealthEndpoint:
    """Tests for /health endpoint."""

    def test_health_returns_ok(self, client):
        """Health endpoint should return ok status."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_health_is_get_only(self, client):
        """Health endpoint should only accept GET requests."""
        # POST should fail
        response = client.post("/health")
        assert response.status_code == 405


class TestSummaryEndpoint:
    """Tests for /summary endpoint."""

    @patch("imessage_analysis.api._open_db")
    def test_summary_returns_structure(self, mock_open_db, client, mock_db):
        """Summary should return expected JSON structure."""
        mock_db.get_table_names.return_value = ["message", "chat", "handle"]
        mock_db.get_row_counts_by_table.return_value = [
            ("message", 1000),
            ("chat", 50),
            ("handle", 100),
        ]
        mock_open_db.return_value = mock_db

        response = client.get("/summary")

        assert response.status_code == 200
        data = response.json()
        assert "table_count" in data
        assert "tables" in data
        assert "db_path" in data

    @patch("imessage_analysis.api._open_db")
    def test_summary_includes_db_path(self, mock_open_db, client, mock_db):
        """Summary should include the database path."""
        mock_db.get_table_names.return_value = []
        mock_db.get_row_counts_by_table.return_value = []
        mock_open_db.return_value = mock_db

        response = client.get("/summary")

        assert response.status_code == 200
        data = response.json()
        assert data["db_path"] == "/fake/path/chat.db"

    @patch("imessage_analysis.api._open_db")
    def test_summary_closes_connection(self, mock_open_db, client, mock_db):
        """Summary should close the database connection."""
        mock_db.get_table_names.return_value = []
        mock_db.get_row_counts_by_table.return_value = []
        mock_open_db.return_value = mock_db

        client.get("/summary")

        mock_db.close.assert_called_once()


class TestLatestEndpoint:
    """Tests for /latest endpoint."""

    @patch("imessage_analysis.api._open_db")
    @patch("imessage_analysis.api.get_latest_messages_data")
    def test_latest_returns_list(self, mock_get_latest, mock_open_db, client, mock_db):
        """Latest should return a list of messages."""
        mock_open_db.return_value = mock_db
        mock_get_latest.return_value = [
            {"date": "2024-01-15 10:00:00", "text": "Hello", "is_from_me": False},
        ]

        response = client.get("/latest")

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @patch("imessage_analysis.api._open_db")
    @patch("imessage_analysis.api.get_latest_messages_data")
    def test_latest_with_limit(self, mock_get_latest, mock_open_db, client, mock_db):
        """Latest should respect limit parameter."""
        mock_open_db.return_value = mock_db
        mock_get_latest.return_value = []

        client.get("/latest?limit=50")

        mock_get_latest.assert_called_once()
        # Check the limit argument was passed
        call_args = mock_get_latest.call_args
        assert call_args.kwargs.get("limit") == 50 or call_args[1].get("limit") == 50

    def test_latest_limit_validation_min(self, client):
        """Latest should reject limit < 1."""
        response = client.get("/latest?limit=0")
        assert response.status_code == 422  # Validation error

    def test_latest_limit_validation_max(self, client):
        """Latest should reject limit > 500."""
        response = client.get("/latest?limit=501")
        assert response.status_code == 422  # Validation error

    def test_latest_limit_default(self, client):
        """Latest should have default limit of 25."""
        with patch("imessage_analysis.api._open_db") as mock_open_db:
            with patch("imessage_analysis.api.get_latest_messages_data") as mock_get:
                mock_db = MagicMock()
                mock_db.close = MagicMock()
                mock_open_db.return_value = mock_db
                mock_get.return_value = []

                client.get("/latest")

                call_args = mock_get.call_args
                # Default should be 25
                assert call_args.kwargs.get("limit") == 25 or call_args[1].get("limit") == 25

    @patch("imessage_analysis.api._open_db")
    @patch("imessage_analysis.api.get_latest_messages_data")
    def test_latest_closes_connection(self, mock_get_latest, mock_open_db, client, mock_db):
        """Latest should close the database connection."""
        mock_open_db.return_value = mock_db
        mock_get_latest.return_value = []

        client.get("/latest")

        mock_db.close.assert_called_once()


class TestTopChatsEndpoint:
    """Tests for /top-chats endpoint."""

    @patch("imessage_analysis.api._open_db")
    @patch("imessage_analysis.api.get_message_statistics_by_chat")
    def test_top_chats_returns_list(self, mock_get_stats, mock_open_db, client, mock_db):
        """Top chats should return a list."""
        mock_open_db.return_value = mock_db
        mock_get_stats.return_value = [
            {"chat_identifier": "+14155551234", "display_name": "John", "message_count": 100},
        ]

        response = client.get("/top-chats")

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @patch("imessage_analysis.api._open_db")
    @patch("imessage_analysis.api.get_message_statistics_by_chat")
    def test_top_chats_respects_limit(self, mock_get_stats, mock_open_db, client, mock_db):
        """Top chats should limit results."""
        mock_open_db.return_value = mock_db
        mock_get_stats.return_value = [
            {"chat_identifier": f"+1415555{i:04d}", "message_count": i} for i in range(100)
        ]

        response = client.get("/top-chats?limit=5")

        assert response.status_code == 200
        assert len(response.json()) == 5

    def test_top_chats_limit_validation_min(self, client):
        """Top chats should reject limit < 1."""
        response = client.get("/top-chats?limit=0")
        assert response.status_code == 422

    def test_top_chats_limit_validation_max(self, client):
        """Top chats should reject limit > 500."""
        response = client.get("/top-chats?limit=501")
        assert response.status_code == 422

    @patch("imessage_analysis.api._open_db")
    @patch("imessage_analysis.api.get_message_statistics_by_chat")
    def test_top_chats_closes_connection(self, mock_get_stats, mock_open_db, client, mock_db):
        """Top chats should close the database connection."""
        mock_open_db.return_value = mock_db
        mock_get_stats.return_value = []

        client.get("/top-chats")

        mock_db.close.assert_called_once()


class TestCORSMiddleware:
    """Tests for CORS configuration."""

    def test_cors_allows_localhost(self, client):
        """CORS should allow localhost origin."""
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            },
        )
        # FastAPI returns 200 for OPTIONS
        assert response.status_code == 200

    def test_cors_headers_present(self, client):
        """CORS headers should be present in response."""
        response = client.get("/health", headers={"Origin": "http://localhost:5173"})
        # Should have CORS headers
        assert "access-control-allow-origin" in response.headers


class TestErrorHandling:
    """Tests for error handling."""

    @patch("imessage_analysis.api._open_db")
    def test_database_error_raises_exception(self, mock_open_db, client):
        """Database errors should propagate as exceptions."""
        mock_open_db.side_effect = Exception("Database not found")

        # FastAPI TestClient re-raises exceptions by default
        with pytest.raises(Exception) as exc_info:
            client.get("/summary")
        assert "Database not found" in str(exc_info.value)

    @patch("imessage_analysis.api._open_db")
    def test_database_error_returns_500_when_handled(self, mock_open_db):
        """Database errors return 500 when raise_server_exceptions=False."""
        mock_open_db.side_effect = Exception("Database not found")

        # Create client that doesn't raise exceptions
        test_client = TestClient(app, raise_server_exceptions=False)
        response = test_client.get("/summary")

        assert response.status_code == 500

    def test_invalid_endpoint_returns_404(self, client):
        """Invalid endpoints should return 404."""
        response = client.get("/nonexistent")
        assert response.status_code == 404
