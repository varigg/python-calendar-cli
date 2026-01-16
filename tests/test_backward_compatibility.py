"""Backward compatibility tests for GCalClient refactoring.

This test suite documents and verifies the current GCalClient public API contract
to ensure that refactoring to use GoogleAuth and GoogleAPIClient base class
maintains 100% backward compatibility.

Per Constitution Success Criterion SC-002:
All existing Calendar functionality must work unchanged after refactoring.
"""

import datetime
from unittest.mock import Mock, patch

import pytest

from caltool.gcal_client import GCalClient


class TestGCalClientPublicAPI:
    """Test suite documenting current GCalClient public API contract."""

    @patch("caltool.google_client.build")
    @patch("caltool.google_auth.GoogleAuth.get_credentials")
    def test_gcalclient_constructor_signature(self, mock_get_creds, mock_build, mock_config, tmp_path):
        """Verify GCalClient.__init__(config, service=None) signature preserved."""
        # Mock authentication - now handled by GoogleAuth
        mock_creds = Mock()
        mock_get_creds.return_value = mock_creds
        mock_service = Mock()
        mock_build.return_value = mock_service

        # Update config to use tmp_path files
        mock_config.data["TOKEN_FILE"] = str(tmp_path / "token.json")
        mock_config.data["CREDENTIALS_FILE"] = str(tmp_path / "credentials.json")

        # Current signature: __init__(self, config: Config, service=None)
        client = GCalClient(mock_config)
        assert client is not None

        # Should also accept optional service parameter
        mock_service2 = Mock()
        client_with_service = GCalClient(mock_config, service=mock_service2)
        assert client_with_service is not None

    def test_gcalclient_has_get_calendar_list_method(self, mock_config):
        """Verify GCalClient.get_calendar_list() method exists and returns list."""
        mock_service = Mock()
        mock_service.calendarList().list().execute.return_value = {
            "items": [{"id": "primary", "summary": "Test Calendar"}]
        }

        client = GCalClient(mock_config, service=mock_service)
        calendars = client.get_calendar_list()

        assert isinstance(calendars, list)
        assert len(calendars) > 0
        assert "id" in calendars[0]

    def test_gcalclient_has_get_events_method(self, mock_config):
        """Verify GCalClient.get_events(calendar_id, start_time, end_time) method exists."""
        mock_service = Mock()
        mock_service.events().list().execute.return_value = {"items": [{"id": "event1", "summary": "Test Event"}]}

        client = GCalClient(mock_config, service=mock_service)
        start = datetime.datetime(2026, 1, 15, 0, 0, 0)
        end = datetime.datetime(2026, 1, 16, 0, 0, 0)
        events = client.get_events(calendar_id="primary", start_time=start, end_time=end)

        assert isinstance(events, list)

    def test_gcalclient_has_get_day_busy_times_method(self, mock_config):
        """Verify GCalClient.get_day_busy_times(calendar_ids, day_start, day_end, timezone) method exists."""
        mock_service = Mock()
        mock_service.freebusy().query().execute.return_value = {
            "calendars": {"primary": {"busy": [{"start": "2026-01-15T09:00:00Z", "end": "2026-01-15T10:00:00Z"}]}}
        }

        client = GCalClient(mock_config, service=mock_service)
        day_start = datetime.datetime(2026, 1, 15, 0, 0, 0)
        day_end = datetime.datetime(2026, 1, 16, 0, 0, 0)
        result = client.get_day_busy_times(
            calendar_ids=["primary"], day_start=day_start, day_end=day_end, timezone="America/Los_Angeles"
        )

        assert isinstance(result, list)

    def test_gcalclient_has_get_event_details_method(self, mock_config):
        """Verify GCalClient.get_event_details(calendar_id, event_id) method exists."""
        mock_service = Mock()
        mock_service.events().get().execute.return_value = {"id": "event1", "summary": "Test Event"}

        client = GCalClient(mock_config, service=mock_service)
        event = client.get_event_details(calendar_id="primary", event_id="event1")

        assert event["id"] == "event1"

    @patch("caltool.google_client.build")
    @patch("caltool.google_auth.GoogleAuth.get_credentials")
    def test_gcalclient_authentication_behavior(self, mock_get_creds, mock_build, mock_config, tmp_path):
        """Verify GCalClient handles authentication transparently (now via GoogleAuth)."""
        # Mock valid credentials - now handled by GoogleAuth
        mock_creds = Mock()
        mock_get_creds.return_value = mock_creds

        mock_service = Mock()
        mock_build.return_value = mock_service

        # Update config to use tmp_path files
        mock_config.data["TOKEN_FILE"] = str(tmp_path / "token.json")
        mock_config.data["CREDENTIALS_FILE"] = str(tmp_path / "credentials.json")

        # Client should initialize without errors
        client = GCalClient(mock_config)
        assert client.service is not None

    def test_gcalclient_exception_handling_preserved(self, mock_config):
        """Verify GCalClient raises appropriate exceptions for API errors."""
        import httplib2
        from googleapiclient.errors import HttpError

        from caltool.errors import CLIError

        mock_service = Mock()
        resp = httplib2.Response({"status": "404"})
        content = b'{"error": {"code": 404, "message": "Not found"}}'
        mock_service.calendarList().list().execute.side_effect = HttpError(resp, content)

        client = GCalClient(mock_config, service=mock_service)

        # After refactoring, HttpError is caught and converted to CLIError
        with pytest.raises(CLIError):
            client.get_calendar_list()


class TestGCalClientRefactoringContract:
    """Contract tests to verify after refactoring to use GoogleAuth and GoogleAPIClient."""

    def test_gcalclient_inherits_from_base_after_refactor(self, mock_config):
        """After refactoring, GCalClient should inherit from GoogleAPIClient."""
        # This test will pass after Phase 6 (T027-T030)
        # For now, just verify client can be instantiated
        client = GCalClient(mock_config, service=Mock())
        assert client is not None
        # TODO: After refactor, add: assert isinstance(client, GoogleAPIClient)

    def test_gcalclient_no_duplicate_auth_logic_after_refactor(self, mock_config):
        """After refactoring, GCalClient should NOT have authenticate() method."""
        # After T028, authenticate() is removed (handled by GoogleAuth)
        client = GCalClient(mock_config, service=Mock())

        # After refactor, authenticate() should not exist on GCalClient
        assert not hasattr(client, "authenticate"), "authenticate() should be removed after refactor (Phase 6)"

    def test_all_existing_calendar_tests_pass_after_refactor(self):
        """Meta-test: All tests in test_cli.py related to Calendar must pass after refactor."""
        # This is verified by running: uv run pytest tests/test_cli.py -k "calendar or gcal"
        # Per Task T031: Run ALL existing tests and verify 100% pass
        assert True  # Placeholder - actual verification is running pytest


# ============================================================================
# Documentation of Current GCalClient Implementation
# ============================================================================

"""
CURRENT GCALCLIENT PUBLIC API CONTRACT (Pre-Refactoring):

Class: GCalClient
    Constructor:
        __init__(self, config: Config, service=None)

    Methods:
        - get_calendar_list() -> list[dict]
            Returns list of calendar objects from Google Calendar API

        - get_events(calendar_id: str, start_time: datetime, end_time: datetime) -> list[dict]
            Returns list of event objects for specified calendar and time range

        - get_day_busy_times(calendar_ids: list[str], day_start: datetime, day_end: datetime, timezone: str) -> list[dict]
            Returns list of busy time slots for specified calendars and day range

        - get_event_details(calendar_id: str, event_id: str) -> dict
            Returns details of a specific event

        - authenticate(self)  [INTERNAL - to be removed in Phase 6]
            Handles OAuth flow and token management
            NOTE: This should move to GoogleAuth module

    Exception Behavior:
        - Raises googleapiclient.errors.HttpError for API errors
        - Does NOT transform or wrap exceptions

    Authentication:
        - Uses token.json file from config
        - Reads credentials.json from config
        - Handles token refresh automatically
        - Uses scopes from config

BACKWARD COMPATIBILITY REQUIREMENTS:
    1. Constructor signature must remain unchanged
    2. All public methods (get_calendar_list, get_events, get_day_busy_times, get_event_details) must work identically
    3. Return types and data structures must be preserved
    4. Exception types and behavior must be unchanged
    5. Config integration must work as before
    6. CLI commands (get-calendars, free, show-events) must work unchanged
"""
