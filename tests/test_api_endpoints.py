"""
Tests for FastAPI endpoints.

Tests the API routes using FastAPI's TestClient.
"""

from unittest.mock import patch, MagicMock
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from imessage_analysis.api import app


@pytest.fixture
def client():
    """Create a TestClient for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_cursor():
    """Create a mock cursor that returns expected data."""
    cursor = MagicMock()
    return cursor


@pytest.fixture
def mock_conn(mock_cursor):
    """Create a mock sqlite3 connection."""
    conn = MagicMock()
    conn.cursor.return_value = mock_cursor
    conn.close = MagicMock()
    return conn


class TestHealthEndpoint:
    """Tests for /health endpoint."""

    def test_health_returns_status(self, client):
        """Health endpoint should return status with db info."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "analysis_db_exists" in data
        assert "analysis_db_path" in data
        # Status should be either 'ok' or 'degraded' based on db existence
        assert data["status"] in ["ok", "degraded"]

    def test_health_is_get_only(self, client):
        """Health endpoint should only accept GET requests."""
        # POST should fail
        response = client.post("/health")
        assert response.status_code == 405


class TestSummaryEndpoint:
    """Tests for /summary endpoint."""

    @patch("imessage_analysis.api._open_analysis_db")
    def test_summary_returns_structure(self, mock_open_db, client, mock_conn, mock_cursor):
        """Summary should return expected JSON structure."""
        mock_open_db.return_value = mock_conn
        # Set up cursor to return expected counts
        mock_cursor.fetchone.side_effect = [
            (1000,),  # total_messages
            (50,),  # total_chats
            (100,),  # total_handles
            (80,),  # total_persons
            (30,),  # contacts_synced
        ]

        response = client.get("/summary")

        assert response.status_code == 200
        data = response.json()
        assert "total_messages" in data
        assert "total_chats" in data
        assert "total_handles" in data
        assert "db_path" in data

    @patch("imessage_analysis.api._open_analysis_db")
    def test_summary_includes_db_path(self, mock_open_db, client, mock_conn, mock_cursor):
        """Summary should include the database path."""
        mock_open_db.return_value = mock_conn
        mock_cursor.fetchone.side_effect = [
            (1000,),
            (50,),
            (100,),
            (80,),
            (30,),
        ]

        response = client.get("/summary")

        assert response.status_code == 200
        data = response.json()
        assert "db_path" in data
        assert data["db_path"] is not None

    @patch("imessage_analysis.api._open_analysis_db")
    def test_summary_closes_connection(self, mock_open_db, client, mock_conn, mock_cursor):
        """Summary should close the database connection."""
        mock_open_db.return_value = mock_conn
        mock_cursor.fetchone.side_effect = [
            (1000,),
            (50,),
            (100,),
            (80,),
            (30,),
        ]

        client.get("/summary")

        mock_conn.close.assert_called_once()


class TestLatestEndpoint:
    """Tests for /latest endpoint."""

    @patch("imessage_analysis.api._open_analysis_db")
    def test_latest_returns_list(self, mock_open_db, client, mock_conn, mock_cursor):
        """Latest should return a list of messages."""
        mock_open_db.return_value = mock_conn
        mock_cursor.fetchall.return_value = [
            ("2024-01-15 10:00:00", "Hello", 0, 1, "+14155551234", "John", "John", "Doe"),
        ]

        response = client.get("/latest")

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @patch("imessage_analysis.api._open_analysis_db")
    def test_latest_with_limit(self, mock_open_db, client, mock_conn, mock_cursor):
        """Latest should respect limit parameter."""
        mock_open_db.return_value = mock_conn
        mock_cursor.fetchall.return_value = []

        response = client.get("/latest?limit=50")

        assert response.status_code == 200
        # Verify execute was called with the limit
        mock_cursor.execute.assert_called_once()
        call_args = mock_cursor.execute.call_args
        assert call_args[0][1] == (50,)  # Second arg is the limit tuple

    def test_latest_limit_validation_min(self, client):
        """Latest should reject limit < 1."""
        response = client.get("/latest?limit=0")
        assert response.status_code == 422  # Validation error

    def test_latest_limit_validation_max(self, client):
        """Latest should reject limit > 500."""
        response = client.get("/latest?limit=501")
        assert response.status_code == 422  # Validation error

    @patch("imessage_analysis.api._open_analysis_db")
    def test_latest_limit_default(self, mock_open_db, client, mock_conn, mock_cursor):
        """Latest should have default limit of 25."""
        mock_open_db.return_value = mock_conn
        mock_cursor.fetchall.return_value = []

        client.get("/latest")

        call_args = mock_cursor.execute.call_args
        assert call_args[0][1] == (25,)  # Default limit is 25

    @patch("imessage_analysis.api._open_analysis_db")
    def test_latest_closes_connection(self, mock_open_db, client, mock_conn, mock_cursor):
        """Latest should close the database connection."""
        mock_open_db.return_value = mock_conn
        mock_cursor.fetchall.return_value = []

        client.get("/latest")

        mock_conn.close.assert_called_once()


class TestTopChatsEndpoint:
    """Tests for /top-chats endpoint."""

    @patch("imessage_analysis.api._open_analysis_db")
    def test_top_chats_returns_list(self, mock_open_db, client, mock_conn, mock_cursor):
        """Top chats should return a list."""
        mock_open_db.return_value = mock_conn
        mock_cursor.fetchall.return_value = [
            (1, 100),  # chat_id, message_count
        ]

        response = client.get("/top-chats")

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @patch("imessage_analysis.api._open_analysis_db")
    def test_top_chats_respects_limit(self, mock_open_db, client, mock_conn, mock_cursor):
        """Top chats should limit results."""
        mock_open_db.return_value = mock_conn
        mock_cursor.fetchall.return_value = [(i, 100 - i) for i in range(5)]

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

    @patch("imessage_analysis.api._open_analysis_db")
    def test_top_chats_closes_connection(self, mock_open_db, client, mock_conn, mock_cursor):
        """Top chats should close the database connection."""
        mock_open_db.return_value = mock_conn
        mock_cursor.fetchall.return_value = []

        client.get("/top-chats")

        mock_conn.close.assert_called_once()


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

    @patch("imessage_analysis.api._open_analysis_db")
    def test_database_error_returns_503(self, mock_open_db, client):
        """Database errors should return 503 status."""
        from fastapi import HTTPException

        mock_open_db.side_effect = HTTPException(status_code=503, detail="Database not found")

        # HTTPException is handled by FastAPI and returns a proper response
        response = client.get("/summary")
        assert response.status_code == 503

    @patch("imessage_analysis.api._open_analysis_db")
    def test_database_error_returns_503_when_handled(self, mock_open_db):
        """Database errors return 503 when raise_server_exceptions=False."""
        from fastapi import HTTPException

        mock_open_db.side_effect = HTTPException(status_code=503, detail="Database not found")

        # Create client that doesn't raise exceptions
        test_client = TestClient(app, raise_server_exceptions=False)
        response = test_client.get("/summary")

        assert response.status_code == 503

    def test_invalid_endpoint_returns_404(self, client):
        """Invalid endpoints should return 404."""
        response = client.get("/nonexistent")
        assert response.status_code == 404


class TestContactsEndpoint:
    """Tests for /contacts endpoint."""

    @patch("imessage_analysis.api._open_analysis_db")
    def test_contacts_returns_list(self, mock_open_db, client, mock_conn, mock_cursor):
        """Contacts should return a list."""
        mock_open_db.return_value = mock_conn
        mock_cursor.fetchall.return_value = [
            # handle_id, value_raw, value_normalized, handle_type, person_id,
            # first_name, last_name, display_name, person_source,
            # message_count, sent_count, received_count, first_message, last_message
            (
                1,
                "+14155551234",
                "+14155551234",
                "phone",
                1,
                "John",
                "Doe",
                "John Doe",
                "contacts",
                100,
                50,
                50,
                "2024-01-01",
                "2024-01-15",
            ),
        ]

        response = client.get("/contacts")

        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) == 1

    @patch("imessage_analysis.api._open_analysis_db")
    def test_contacts_structure(self, mock_open_db, client, mock_conn, mock_cursor):
        """Contacts should have expected fields."""
        mock_open_db.return_value = mock_conn
        mock_cursor.fetchall.return_value = [
            (
                1,
                "+14155551234",
                "+14155551234",
                "phone",
                1,
                "John",
                "Doe",
                "John Doe",
                "contacts",
                100,
                50,
                50,
                "2024-01-01",
                "2024-01-15",
            ),
        ]

        response = client.get("/contacts")
        data = response.json()

        assert len(data) == 1
        contact = data[0]
        assert "handle_id" in contact
        assert "id" in contact
        assert "display_name" in contact
        assert "message_count" in contact
        assert "sent_count" in contact
        assert "received_count" in contact

    @patch("imessage_analysis.api._open_analysis_db")
    def test_contacts_display_name_fallback(self, mock_open_db, client, mock_conn, mock_cursor):
        """Contacts should build display_name from first/last name if not set."""
        mock_open_db.return_value = mock_conn
        # display_name (row[7]) is None, but first_name and last_name are set
        mock_cursor.fetchall.return_value = [
            (
                1,
                "+14155551234",
                "+14155551234",
                "phone",
                1,
                "John",
                "Doe",
                None,
                "inferred",
                100,
                50,
                50,
                "2024-01-01",
                "2024-01-15",
            ),
        ]

        response = client.get("/contacts")
        data = response.json()

        assert data[0]["display_name"] == "John Doe"

    @patch("imessage_analysis.api._open_analysis_db")
    def test_contacts_empty_list(self, mock_open_db, client, mock_conn, mock_cursor):
        """Contacts should handle empty result."""
        mock_open_db.return_value = mock_conn
        mock_cursor.fetchall.return_value = []

        response = client.get("/contacts")

        assert response.status_code == 200
        assert response.json() == []

    @patch("imessage_analysis.api._open_analysis_db")
    def test_contacts_closes_connection(self, mock_open_db, client, mock_conn, mock_cursor):
        """Contacts should close the database connection."""
        mock_open_db.return_value = mock_conn
        mock_cursor.fetchall.return_value = []

        client.get("/contacts")

        mock_conn.close.assert_called_once()


class TestContactDetailEndpoint:
    """Tests for /contacts/{handle_id} endpoint."""

    @patch("imessage_analysis.api._open_analysis_db")
    def test_contact_detail_found(self, mock_open_db, client, mock_conn, mock_cursor):
        """Should return contact details when found."""
        mock_open_db.return_value = mock_conn
        # First query returns contact info, second returns stats
        mock_cursor.fetchone.side_effect = [
            # handle_id, value_raw, value_normalized, handle_type, person_id,
            # first_name, last_name, display_name, person_source
            (1, "+14155551234", "+14155551234", "phone", 1, "John", "Doe", "John Doe", "contacts"),
            # total, from_me, from_them, chars_from_me, chars_from_them, first_message, last_message
            (100, 50, 50, 2500, 2500, "2024-01-01", "2024-01-15"),
        ]

        response = client.get("/contacts/+14155551234")

        assert response.status_code == 200
        data = response.json()
        assert "contact" in data
        assert "statistics" in data
        assert data["contact"]["id"] == "+14155551234"

    @patch("imessage_analysis.api._open_analysis_db")
    def test_contact_detail_not_found(self, mock_open_db, client, mock_conn, mock_cursor):
        """Should return 404 when contact not found."""
        mock_open_db.return_value = mock_conn
        mock_cursor.fetchone.return_value = None

        response = client.get("/contacts/unknown")

        assert response.status_code == 404

    @patch("imessage_analysis.api._open_analysis_db")
    def test_contact_detail_statistics_structure(
        self, mock_open_db, client, mock_conn, mock_cursor
    ):
        """Should return proper statistics structure."""
        mock_open_db.return_value = mock_conn
        mock_cursor.fetchone.side_effect = [
            (1, "+14155551234", "+14155551234", "phone", 1, "John", "Doe", "John Doe", "contacts"),
            (100, 60, 40, 3000, 2000, "2024-01-01", "2024-01-15"),
        ]

        response = client.get("/contacts/+14155551234")
        stats = response.json()["statistics"]

        assert "total_messages" in stats
        assert "from_me" in stats
        assert "from_them" in stats
        assert stats["total_messages"] == 100
        assert stats["from_me"]["message_count"] == 60
        assert stats["from_them"]["message_count"] == 40

    @patch("imessage_analysis.api._open_analysis_db")
    def test_contact_detail_display_name_fallback(
        self, mock_open_db, client, mock_conn, mock_cursor
    ):
        """Should build display_name from first/last if not set."""
        mock_open_db.return_value = mock_conn
        # display_name (row[7]) is None
        mock_cursor.fetchone.side_effect = [
            (1, "+14155551234", "+14155551234", "phone", 1, "Jane", "Smith", None, "inferred"),
            (50, 25, 25, 1000, 1000, "2024-01-01", "2024-01-15"),
        ]

        response = client.get("/contacts/+14155551234")
        contact = response.json()["contact"]

        assert contact["display_name"] == "Jane Smith"

    @patch("imessage_analysis.api._open_analysis_db")
    def test_contact_detail_closes_connection(self, mock_open_db, client, mock_conn, mock_cursor):
        """Should close the database connection."""
        mock_open_db.return_value = mock_conn
        mock_cursor.fetchone.side_effect = [
            (1, "+14155551234", "+14155551234", "phone", 1, "John", "Doe", "John Doe", "contacts"),
            (100, 50, 50, 2500, 2500, "2024-01-01", "2024-01-15"),
        ]

        client.get("/contacts/+14155551234")

        mock_conn.close.assert_called_once()


class TestDiagnosticsEndpoint:
    """Tests for /diagnostics endpoint."""

    def test_diagnostics_no_db(self, client):
        """Should return not_initialized when db doesn't exist."""
        with patch("imessage_analysis.api._get_analysis_db_path") as mock_path:
            mock_path.return_value = Path("/nonexistent/path/analysis.db")
            response = client.get("/diagnostics")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "not_initialized"
            assert data["analysis_db_exists"] is False

    @patch("imessage_analysis.api.sqlite3.connect")
    @patch("imessage_analysis.api._get_analysis_db_path")
    def test_diagnostics_with_db(self, mock_path, mock_connect, client, tmp_path):
        """Should return diagnostics when db exists."""
        # Create a real file so path.exists() returns True
        db_file = tmp_path / "analysis.db"
        db_file.touch()
        mock_path.return_value = db_file

        # Set up mock connection and cursor
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # Mock the various queries
        mock_cursor.fetchone.side_effect = [
            (100,),  # total_handles
            (80,),  # total_persons
            (1000,),  # total_messages
            (50,),  # total_contact_methods
            (60,),  # handles_with_names
            (40,),  # handles_from_contacts
            (10,),  # handles_unlinked
            ("2020-01-01", "2024-01-15"),  # date_range
        ]
        mock_cursor.fetchall.side_effect = [
            [("contacts", 40), ("inferred", 40)],  # person_sources
            [("phone", 70), ("email", 30)],  # handle_types
            [],  # etl_state
            [],  # top_contacts
        ]

        response = client.get("/diagnostics")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["analysis_db_exists"] is True
        assert "counts" in data
        assert "enrichment" in data

    @patch("imessage_analysis.api.sqlite3.connect")
    @patch("imessage_analysis.api._get_analysis_db_path")
    def test_diagnostics_counts_structure(self, mock_path, mock_connect, client, tmp_path):
        """Should return proper counts structure."""
        db_file = tmp_path / "analysis.db"
        db_file.touch()
        mock_path.return_value = db_file

        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        mock_cursor.fetchone.side_effect = [
            (100,),
            (80,),
            (1000,),
            (50,),
            (60,),
            (40,),
            (10,),
            ("2020-01-01", "2024-01-15"),
        ]
        mock_cursor.fetchall.side_effect = [
            [("contacts", 40)],
            [("phone", 70)],
            [],
            [],
        ]

        response = client.get("/diagnostics")
        counts = response.json()["counts"]

        assert "handles" in counts
        assert "persons" in counts
        assert "messages" in counts
        assert counts["handles"] == 100
        assert counts["messages"] == 1000

    @patch("imessage_analysis.api.sqlite3.connect")
    @patch("imessage_analysis.api._get_analysis_db_path")
    def test_diagnostics_enrichment_structure(self, mock_path, mock_connect, client, tmp_path):
        """Should return proper enrichment structure."""
        db_file = tmp_path / "analysis.db"
        db_file.touch()
        mock_path.return_value = db_file

        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        mock_cursor.fetchone.side_effect = [
            (100,),
            (80,),
            (1000,),
            (50,),
            (60,),
            (40,),
            (10,),
            ("2020-01-01", "2024-01-15"),
        ]
        mock_cursor.fetchall.side_effect = [
            [],
            [],
            [],
            [],
        ]

        response = client.get("/diagnostics")
        enrichment = response.json()["enrichment"]

        assert "handles_total" in enrichment
        assert "handles_with_names" in enrichment
        assert "handles_from_contacts" in enrichment
        assert "name_coverage_percent" in enrichment

    @patch("imessage_analysis.api.sqlite3.connect")
    @patch("imessage_analysis.api._get_analysis_db_path")
    def test_diagnostics_closes_connection(self, mock_path, mock_connect, client, tmp_path):
        """Should close the database connection."""
        db_file = tmp_path / "analysis.db"
        db_file.touch()
        mock_path.return_value = db_file

        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        mock_cursor.fetchone.side_effect = [
            (100,),
            (80,),
            (1000,),
            (50,),
            (60,),
            (40,),
            (10,),
            ("2020-01-01", "2024-01-15"),
        ]
        mock_cursor.fetchall.side_effect = [[], [], [], []]

        client.get("/diagnostics")

        mock_conn.close.assert_called_once()
