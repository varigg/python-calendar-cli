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
