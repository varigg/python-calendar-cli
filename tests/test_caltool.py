import datetime
import re
from unittest.mock import Mock, patch
from zoneinfo import ZoneInfo

import pytest
from click.testing import CliRunner

from caltool.cli import cli
from caltool.gcal_client import GCalClient
from caltool.scheduler import Scheduler, SearchParameters
from src.caltool.config import Config


def test_get_calendars_missing_credentials(tmp_path):
    from src.caltool.cli import get_calendars

    config = {
        "CREDENTIALS_FILE": str(tmp_path / "missing_credentials.json"),
        "TOKEN_FILE": str(tmp_path / "token.json"),
        "SCOPES": ["https://www.googleapis.com/auth/calendar"],
    }
    with pytest.raises(SystemExit):
        get_calendars(config)


def test_get_calendars_missing_token(tmp_path):
    from src.caltool.cli import get_calendars

    cred_file = tmp_path / "credentials.json"
    cred_file.write_text("{}")
    config = {
        "CREDENTIALS_FILE": str(cred_file),
        "TOKEN_FILE": str(tmp_path / "missing_token.json"),
        "SCOPES": ["https://www.googleapis.com/auth/calendar"],
    }
    with pytest.raises(SystemExit):
        get_calendars(config)


def test_get_calendars_invalid_scopes(tmp_path):
    from src.caltool.cli import get_calendars

    cred_file = tmp_path / "credentials.json"
    token_file = tmp_path / "token.json"
    cred_file.write_text("{}")
    token_file.write_text("{}")
    config = {
        "CREDENTIALS_FILE": str(cred_file),
        "TOKEN_FILE": str(token_file),
        "SCOPES": "notalist",
    }
    with pytest.raises(SystemExit):
        get_calendars(config)


def test_get_calendars_auth_error(tmp_path):
    from src.caltool.cli import get_calendars

    cred_file = tmp_path / "credentials.json"
    token_file = tmp_path / "token.json"
    cred_file.write_text("{}")
    token_file.write_text("{}")
    config = {
        "CREDENTIALS_FILE": str(cred_file),
        "TOKEN_FILE": str(token_file),
        "SCOPES": ["https://www.googleapis.com/auth/calendar"],
    }
    with patch("src.caltool.cli.GCalClient") as mock_client:
        instance = mock_client.return_value
        instance.get_calendar_list.side_effect = Exception("invalid_scope")
        with pytest.raises(SystemExit):
            get_calendars(config)

def clean_cli_output(output):
    """Helper to strip ANSI codes, config messages, and empty lines from CLI output."""
    output = re.sub(r"\x1b\[[0-9;]*m", "", output)  # Remove ANSI
    output = "\n".join([line for line in output.splitlines() if not line.startswith("Using configuration file:")])
    output = "\n".join([line for line in output.splitlines() if line.strip()])
    return output


@pytest.fixture
def calendar_data():
    return [
        {"id": "primary", "summary": "My Calendar", "accessRole": "owner"},
        {"id": "secondary@group.calendar.google.com", "summary": "Team Calendar", "accessRole": "reader"},
    ]


@pytest.fixture
def busy_times():
    return [
        {"start": "2025-05-02T09:00:00-07:00", "end": "2025-05-02T10:00:00-07:00"},
        {"start": "2025-05-02T14:00:00-07:00", "end": "2025-05-02T15:00:00-07:00"},
    ]


@pytest.fixture
def scheduler():
    availability_start = datetime.time(8, 0)
    availability_end = datetime.time(18, 0)
    duration_minutes = 30
    time_zone = "America/Los_Angeles"
    start_date = datetime.date(2025, 5, 2)
    end_date = datetime.date(2025, 5, 3)
    search_params = SearchParameters(
        start_date=str(start_date),
        end_date=str(end_date),
        start_time=availability_start.strftime("%H:%M"),
        end_time=availability_end.strftime("%H:%M"),
        duration=duration_minutes,
        timezone=time_zone,
    )
    return Scheduler(
        client=Mock(),
        search_params=search_params,
        calendar_ids=["primary"],
    )


@pytest.mark.parametrize(
    "start,end,duration,expected",
    [
        (datetime.datetime(2025, 5, 2, 8, 0), datetime.datetime(2025, 5, 2, 8, 30), 30, True),
        (datetime.datetime(2025, 5, 2, 8, 0), datetime.datetime(2025, 5, 2, 8, 15), 30, False),
        (datetime.datetime(2025, 5, 2, 8, 0), datetime.datetime(2025, 5, 2, 9, 0), 30, True),
        (datetime.datetime(2025, 5, 2, 8, 0), datetime.datetime(2025, 5, 3, 8, 0), 30, True),
    ],
)
def test_is_slot_long_enough(scheduler, start, end, duration, expected):
    assert scheduler.is_slot_long_enough(start, end, duration) == expected


@pytest.mark.parametrize(
    "busy,expected_count",
    [
        ([], 1),
        ([{"start": "2025-05-02T09:00:00-07:00", "end": "2025-05-02T10:00:00-07:00"}], 2),
        ([{"start": "2025-05-02T08:00:00-07:00", "end": "2025-05-02T18:00:00-07:00"}], 0),
        (
            [
                {"start": "2025-05-02T08:00:00-07:00", "end": "2025-05-02T09:00:00-07:00"},
                {"start": "2025-05-02T17:00:00-07:00", "end": "2025-05-02T18:00:00-07:00"},
            ],
            1,
        ),
    ],
)
def test_get_free_slots_for_day(scheduler, busy, expected_count):
    tz = ZoneInfo("America/Los_Angeles")
    day_start = datetime.datetime(2025, 5, 2, 8, 0, tzinfo=tz)
    day_end = datetime.datetime(2025, 5, 2, 18, 0, tzinfo=tz)
    slots = scheduler.get_free_slots_for_day(busy, day_start, day_end, 30)
    assert len(slots) == expected_count


@patch("caltool.cli.GCalClient")
def test_free_command(mock_gcal, busy_times):
    mock_client = Mock()
    mock_client.get_day_busy_times.return_value = busy_times
    mock_gcal.return_value = mock_client
    runner = CliRunner()
    # Create a mock config object
    config_data = {
        "CREDENTIALS_FILE": "creds.json",
        "TOKEN_FILE": "token.json",
        "SCOPES": ["scope"],
        "CALENDAR_IDS": ["primary"],
        "AVAILABILITY_START": "08:00",
        "AVAILABILITY_END": "18:00",
        "TIME_ZONE": "America/Los_Angeles",
    }
    mock_config = Config()
    mock_config.data = config_data
    result = runner.invoke(
        cli,
        [
            "free",
            "today+1",
            "--duration",
            "30",
            "--availability-start",
            "08:00",
            "--availability-end",
            "18:00",
            "--timezone",
            "America/Los_Angeles",
        ],
        obj=mock_config,
    )
    assert result.exit_code == 0
    output = clean_cli_output(result.output)
    assert "Wed 08/20" in output
    assert "Thu 08/21" in output
    assert "PM" in output
    assert re.search(r"\d{2}:\d{2} [AP]M - \d{2}:\d{2} [AP]M", output)


@patch("caltool.cli.GCalClient")
def test_get_calendars_command(mock_gcal, calendar_data):
    mock_client = Mock()
    mock_client.get_calendar_list.return_value = calendar_data
    mock_gcal.return_value = mock_client
    runner = CliRunner()
    config_data = {
        "CREDENTIALS_FILE": "creds.json",
        "TOKEN_FILE": "token.json",
        "SCOPES": ["scope"],
        "CALENDAR_IDS": ["primary"],
        "AVAILABILITY_START": "08:00",
        "AVAILABILITY_END": "18:00",
        "TIME_ZONE": "America/Los_Angeles",
    }
    mock_config = Config()
    mock_config.data = config_data
    result = runner.invoke(cli, ["get-calendars"], obj=mock_config)
    assert result.exit_code == 0
    output = clean_cli_output(result.output)
    assert "My Calendar" in output
    assert "Team Calendar" in output


def test_gcalclient_injection():
    # Test that dependency injection works for GCalClient
    mock_service = Mock()
    config_data = {
        "CREDENTIALS_FILE": "/fake/creds.json",
        "TOKEN_FILE": "/fake/token.json",
        "SCOPES": ["scope"],
        "CALENDAR_IDS": ["primary"],
        "AVAILABILITY_START": "08:00",
        "AVAILABILITY_END": "18:00",
        "TIME_ZONE": "America/Los_Angeles",
    }
    mock_config = Config()
    mock_config.data = config_data
    client = GCalClient(mock_config, service=mock_service)
    assert client.service is mock_service
    # Test that API methods use the injected service
    client.service.calendarList().list().execute.return_value = {"items": ["foo"]}
    assert client.get_calendar_list() == ["foo"]
    # Test get_events with injected service
    client.service.events().list().execute.return_value = {"items": [{"id": 1}]}
    events = client.get_events("primary")
    assert events[0]["id"] == 1
    assert events[0]["calendarId"] == "primary"

def test_config_prompt_asks_for_scopes():
    from src.caltool.config import Config
    prompts = []
    def fake_prompt(text, default=None):
        prompts.append(text)
        return default or ""
    config = Config()
    with patch("click.prompt", side_effect=fake_prompt):
        config.prompt()
    assert any("scope" in p.lower() for p in prompts), "Config.prompt should ask for scopes"