"""Shared test fixtures for the calendarcli test suite."""

import datetime
from unittest.mock import Mock

import pytest

from caltool.config import Config
from caltool.scheduler import Scheduler, SearchParameters


@pytest.fixture
def mock_config(tmp_path):
    """Create a mock config with temporary file paths for testing."""
    config_data = {
        "CREDENTIALS_FILE": str(tmp_path / "credentials.json"),
        "TOKEN_FILE": str(tmp_path / "token.json"),
        "SCOPES": ["scope"],
        "CALENDAR_IDS": ["primary"],
        "AVAILABILITY_START": "08:00",
        "AVAILABILITY_END": "18:00",
        "TIME_ZONE": "America/Los_Angeles",
    }
    config = Config()
    config.data = config_data
    return config


@pytest.fixture
def calendar_data():
    """Sample calendar list data for testing."""
    return [
        {"id": "primary", "summary": "My Calendar", "accessRole": "owner"},
        {"id": "secondary@group.calendar.google.com", "summary": "Team Calendar", "accessRole": "reader"},
    ]


@pytest.fixture
def busy_times():
    """Sample busy time data for testing."""
    return [
        {"start": "2025-05-02T09:00:00-07:00", "end": "2025-05-02T10:00:00-07:00"},
        {"start": "2025-05-02T14:00:00-07:00", "end": "2025-05-02T15:00:00-07:00"},
    ]


@pytest.fixture
def scheduler():
    """Create a configured scheduler instance for testing."""
    availability_start = datetime.time(8, 0)
    availability_end = datetime.time(18, 0)
    duration_minutes = 30
    time_zone = "America/Los_Angeles"
    start_date = datetime.date(2025, 5, 2)
    end_date = datetime.date(2025, 5, 3)
    search_params = SearchParameters(
        start_date=start_date,
        end_date=end_date,
        start_time=availability_start,
        end_time=availability_end,
        duration=duration_minutes,
        timezone=time_zone,
    )
    return Scheduler(
        client=Mock(),
        search_params=search_params,
        calendar_ids=["primary"],
    )


# ============================================================================
# Gmail Mock Fixtures (Phase 2: Foundation)
# ============================================================================


@pytest.fixture
def mock_gmail_messages():
    """Sample Gmail messages list response for testing."""
    return {
        "messages": [
            {"id": "msg001", "threadId": "thread001"},
            {"id": "msg002", "threadId": "thread001"},
            {"id": "msg003", "threadId": "thread002"},
        ],
        "resultSizeEstimate": 3,
    }


@pytest.fixture
def mock_gmail_message_detail():
    """Sample Gmail message detail response for testing."""
    return {
        "id": "msg001",
        "threadId": "thread001",
        "labelIds": ["INBOX", "UNREAD"],
        "snippet": "This is a test email snippet...",
        "payload": {
            "headers": [
                {"name": "From", "value": "sender@example.com"},
                {"name": "To", "value": "recipient@example.com"},
                {"name": "Subject", "value": "Test Subject"},
                {"name": "Date", "value": "Mon, 15 Jan 2026 10:00:00 -0800"},
            ],
            "body": {
                "size": 42,
                "data": "VGhpcyBpcyBhIHRlc3QgbWVzc2FnZQ==",  # base64: "This is a test message"
            },
        },
        "internalDate": "1736960400000",
        "sizeEstimate": 1234,
    }


@pytest.fixture
def mock_google_auth_response():
    """Mock Google OAuth2 authentication response for testing."""
    mock_creds = Mock()
    mock_creds.valid = True
    mock_creds.expired = False
    mock_creds.token = "mock_access_token"
    mock_creds.refresh_token = "mock_refresh_token"
    mock_creds.scopes = ["https://www.googleapis.com/auth/calendar.readonly"]
    return mock_creds


@pytest.fixture
def mock_http_error_429():
    """Mock HttpError for rate limit (429) testing."""
    from googleapiclient.errors import HttpError
    import httplib2

    resp = httplib2.Response({"status": "429"})
    content = b'{"error": {"code": 429, "message": "Rate limit exceeded"}}'
    return HttpError(resp, content)


@pytest.fixture
def mock_http_error_403():
    """Mock HttpError for quota exceeded (403) testing."""
    from googleapiclient.errors import HttpError
    import httplib2

    resp = httplib2.Response({"status": "403"})
    content = b'{"error": {"code": 403, "message": "Quota exceeded"}}'
    return HttpError(resp, content)


@pytest.fixture
def mock_http_error_401():
    """Mock HttpError for authentication failure (401) testing."""
    from googleapiclient.errors import HttpError
    import httplib2

    resp = httplib2.Response({"status": "401"})
    content = b'{"error": {"code": 401, "message": "Invalid credentials"}}'
    return HttpError(resp, content)
