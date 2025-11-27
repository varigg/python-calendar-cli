"""Consolidated tests for CLI commands, GCalClient, and Scheduler."""
import datetime
import re
from unittest.mock import Mock, patch
from zoneinfo import ZoneInfo

import pytest
from click.testing import CliRunner
from googleapiclient.errors import HttpError

from caltool.cli import cli
from caltool.gcal_client import GCalClient


# --- Utility Functions ---


def clean_cli_output(output):
    """Helper to strip ANSI codes, config messages, and empty lines from CLI output."""
    output = re.sub(r"\x1b\[[0-9;]*m", "", output)  # Remove ANSI
    output = "\n".join([line for line in output.splitlines() if not line.startswith("Using configuration file:")])
    output = "\n".join([line for line in output.splitlines() if line.strip()])
    return output


# --- CLI Command Tests: get-calendars ---


@pytest.mark.parametrize(
    "config_setup,error_type",
    [
        # Missing credentials file
        (
            lambda tmp: {
                "CREDENTIALS_FILE": str(tmp / "missing_credentials.json"),
                "TOKEN_FILE": str(tmp / "token.json"),
                "SCOPES": ["https://www.googleapis.com/auth/calendar"],
            },
            "credentials"
        ),
        # Missing token file
        (
            lambda tmp: {
                "CREDENTIALS_FILE": "credentials.json",
                "TOKEN_FILE": str(tmp / "missing_token.json"),
                "SCOPES": ["https://www.googleapis.com/auth/calendar"],
            },
            "token"
        ),
        # Invalid scopes (not a list)
        (
            lambda tmp: {
                "CREDENTIALS_FILE": "credentials.json",
                "TOKEN_FILE": "token.json",
                "SCOPES": "notalist",
            },
            "scopes"
        ),
    ],
)
def test_get_calendars_errors(tmp_path, config_setup, error_type):
    """Test get_calendars command with various error conditions."""
    from caltool.cli import get_calendars
    
    # Create necessary files for some test cases
    if error_type == "token":
        cred_file = tmp_path / "credentials.json"
        cred_file.write_text("{}")
    elif error_type == "scopes":
        cred_file = tmp_path / "credentials.json"
        token_file = tmp_path / "token.json"
        cred_file.write_text("{}")
        token_file.write_text("{}")
    
    config_data = config_setup(tmp_path)
    with pytest.raises(SystemExit):
        get_calendars(config_data)


def test_get_calendars_auth_error(tmp_path):
    """Test get_calendars command with authentication error."""
    from caltool.cli import get_calendars
    
    cred_file = tmp_path / "credentials.json"
    token_file = tmp_path / "token.json"
    cred_file.write_text("{}")
    token_file.write_text("{}")
    config = {
        "CREDENTIALS_FILE": str(cred_file),
        "TOKEN_FILE": str(token_file),
        "SCOPES": ["https://www.googleapis.com/auth/calendar"],
    }
    with patch("caltool.cli.GCalClient") as mock_client:
        instance = mock_client.return_value
        instance.get_calendar_list.side_effect = Exception("invalid_scope")
        with pytest.raises(SystemExit):
            get_calendars(config)


def test_get_calendars_command(mock_config, calendar_data):
    """Test get-calendars command with successful response."""
    mock_client = Mock()
    mock_client.get_calendar_list.return_value = calendar_data
    with patch("caltool.cli.GCalClient", return_value=mock_client):
        runner = CliRunner()
        result = runner.invoke(cli, ["get-calendars"], obj=mock_config)
    assert result.exit_code == 0
    output = clean_cli_output(result.output)
    assert "My Calendar" in output
    assert "Team Calendar" in output


# --- CLI Command Tests: free ---


@patch("caltool.cli.GCalClient")
@patch("caltool.cli.parse_date_range")
def test_free_command(mock_parse_date_range, mock_gcal, mock_config, busy_times):
    """Test free command with date range and busy times."""
    # Mock parse_date_range to return fixed datetime objects
    import datetime
    from zoneinfo import ZoneInfo
    tz = ZoneInfo("America/Los_Angeles")
    start_dt = datetime.datetime(2025, 5, 2, 0, 0, 0, tzinfo=tz)
    end_dt = datetime.datetime(2025, 5, 3, 23, 59, 59, tzinfo=tz)
    mock_parse_date_range.return_value = (start_dt, end_dt)
    
    mock_client = Mock()
    mock_client.get_day_busy_times.return_value = busy_times
    mock_gcal.return_value = mock_client
    runner = CliRunner()
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
    # Check for the fixed dates (May 2 is Friday, May 3 is Saturday in 2025)
    assert "Fri 05/02" in output
    assert "Sat 05/03" in output
    assert "PM" in output
    assert re.search(r"\d{2}:\d{2} [AP]M - \d{2}:\d{2} [AP]M", output)


def test_free_command_pretty(mock_config):
    """Test free command with --pretty flag."""
    mock_client = Mock()
    mock_client.get_day_busy_times.return_value = []
    with patch("caltool.cli.GCalClient", return_value=mock_client):
        runner = CliRunner()
        result = runner.invoke(
            cli, ["free", "today", "--pretty"], obj=mock_config
        )
    assert result.exit_code == 0
    assert "Available Time Slots" in result.output


def test_free_command_error(mock_config):
    """Test free command with error condition."""
    # Simulate error in command logic
    # Override SCOPES to be empty for this test
    mock_config.data["SCOPES"] = []
    with patch("caltool.cli.GCalClient", side_effect=Exception("fail")):
        runner = CliRunner()
        result = runner.invoke(cli, ["free", "--start-date", "2025-05-02", "--end-date", "2025-05-02"], obj=mock_config)
    assert result.exit_code != 0
    assert "Error:" in result.output


# --- CLI Command Tests: show-events ---


def test_show_events_invalid_time(mock_config):
    """Test show-events command with invalid date format."""
    # Override SCOPES to be empty for this test
    mock_config.data["SCOPES"] = []
    # Patch GCalClient so CLI proceeds to time parsing
    with patch("caltool.cli.GCalClient", return_value=Mock()):
        runner = CliRunner()
        result = runner.invoke(cli, ["show-events", "not-a-date"], obj=mock_config)
    assert result.exit_code != 0


# --- GCalClient Tests ---


def test_gcalclient_injection(mock_config):
    """Test that dependency injection works for GCalClient."""
    mock_service = Mock()
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


@patch("caltool.gcal_client.build", return_value=Mock(name="service"))
def test_gcalclient_authenticate_token(mock_build, mock_config, monkeypatch):
    """Test GCalClient authentication with valid token."""
    creds_mock = Mock()
    creds_mock.to_json.return_value = "{}"
    monkeypatch.setattr("os.path.exists", lambda path: True)
    monkeypatch.setattr("google.oauth2.credentials.Credentials.from_authorized_user_file", lambda f, s: creds_mock)
    monkeypatch.setattr(creds_mock, "valid", True)
    client = GCalClient(mock_config)
    assert client.service is not None


@patch("caltool.gcal_client.build", return_value=Mock(name="service"))
@patch("google.oauth2.credentials.Credentials.from_authorized_user_file")
def test_gcalclient_authenticate_refresh(mock_from_file, mock_build, mock_config, monkeypatch):
    """Test GCalClient authentication with expired token requiring refresh."""
    creds_mock = Mock()
    creds_mock.to_json.return_value = "{}"
    creds_mock.valid = False
    creds_mock.expired = True
    creds_mock.refresh_token = True
    creds_mock.refresh = lambda req: None
    mock_from_file.return_value = creds_mock
    monkeypatch.setattr("os.path.exists", lambda path: True)
    client = GCalClient(mock_config)
    assert client.service is not None


def test_gcalclient_retry(mock_config):
    """Test retry logic for API calls."""
    service_mock = Mock()
    call_count = {"count": 0}

    def fail_then_succeed(*a, **kw):
        call_count["count"] += 1
        if call_count["count"] < 2:
            raise HttpError(resp=Mock(), content=b"fail")
        return {"items": ["foo"]}

    service_mock.calendarList().list().execute.side_effect = fail_then_succeed
    client = GCalClient(mock_config, service=service_mock)
    assert client.get_calendar_list() == ["foo"]


def test_gcalclient_get_events(mock_config):
    """Test get_events returns events and adds calendarId."""
    service_mock = Mock()
    service_mock.events().list().execute.return_value = {"items": [{"id": 1}]}
    client = GCalClient(mock_config, service=service_mock)
    events = client.get_events("primary")
    assert events[0]["id"] == 1
    assert events[0]["calendarId"] == "primary"


# --- Scheduler Tests ---


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
    """Test scheduler's slot duration validation."""
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
    """Test scheduler's free slot calculation for a day."""
    tz = ZoneInfo("America/Los_Angeles")
    day_start = datetime.datetime(2025, 5, 2, 8, 0, tzinfo=tz)
    day_end = datetime.datetime(2025, 5, 2, 18, 0, tzinfo=tz)
    slots = scheduler.get_free_slots_for_day(busy, day_start, day_end, 30)
    assert len(slots) == expected_count
