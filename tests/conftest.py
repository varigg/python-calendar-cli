"""Shared test fixtures for the calendarcli test suite."""

import datetime
from unittest.mock import Mock

import pytest

from gtool.config.settings import Config
from gtool.core.models import SearchParameters
from gtool.core.scheduler import Scheduler


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
def make_http_error():
    """Factory fixture to create HttpError for any status code."""
    import httplib2
    from googleapiclient.errors import HttpError

    def _make_error(status: int, message: str = "Error"):
        resp = httplib2.Response({"status": str(status)})
        content = f'{{"error": {{"code": {status}, "message": "{message}"}}}}'.encode()
        return HttpError(resp, content)

    return _make_error


@pytest.fixture
def mock_http_error_401(make_http_error):
    """Mock HttpError for authentication failure (401)."""
    return make_http_error(401, "Invalid credentials")


@pytest.fixture
def mock_http_error_403(make_http_error):
    """Mock HttpError for quota exceeded (403)."""
    return make_http_error(403, "Quota exceeded")


@pytest.fixture
def mock_http_error_429(make_http_error):
    """Mock HttpError for rate limit (429)."""
    return make_http_error(429, "Rate limit exceeded")


@pytest.fixture
def mock_http_error_500(make_http_error):
    """Mock HttpError for server error (500)."""
    return make_http_error(500, "Internal server error")


@pytest.fixture
def mock_http_error_400(make_http_error):
    """Mock HttpError for client error (400)."""
    return make_http_error(400, "Bad request")


@pytest.fixture
def mock_google_auth():
    """Mock GoogleAuth instance for composition testing."""
    mock_auth = Mock()
    mock_auth.get_credentials.return_value = Mock()
    return mock_auth


@pytest.fixture
def mock_google_service():
    """Mock Google API service for composition testing."""
    mock_service = Mock()
    return mock_service


@pytest.fixture
def mock_error_categorizer():
    """Mock ErrorCategorizer for composition testing."""
    mock_categorizer = Mock()
    mock_categorizer.categorize.side_effect = lambda err: (
        "AUTH"
        if "401" in str(err)
        else "QUOTA"
        if "429" in str(err) or "403" in str(err)
        else "TRANSIENT"
        if "500" in str(err)
        else "CLIENT"
    )
    return mock_categorizer


@pytest.fixture
def mock_retry_policy():
    """Mock RetryPolicy for composition testing."""
    mock_policy = Mock()
    mock_policy.execute.side_effect = lambda func, *args, **kwargs: func(*args, **kwargs)
    mock_policy.should_retry.return_value = True
    return mock_policy


@pytest.fixture
def mock_service_factory():
    """Mock ServiceFactory for composition testing."""
    mock_factory = Mock()
    mock_factory.build_service.return_value = Mock()
    return mock_factory
