import json
from unittest.mock import Mock, mock_open, patch

import pytest
from click.testing import CliRunner
from googleapiclient.errors import HttpError

from caltool.cli import cli, require_config
from caltool.gcal_client import GCalClient


# --- CLI TESTS ---
def test_free_command_pretty(monkeypatch):
    mock_client = Mock()
    mock_client.get_day_busy_times.return_value = []
    config = {
        "CREDENTIALS_FILE": "creds.json",
        "TOKEN_FILE": "token.json",
        "SCOPES": ["scope"],
        "CALENDAR_IDS": ["primary"],
        "AVAILABILITY_START": "08:00",
        "AVAILABILITY_END": "18:00",
        "TIME_ZONE": "America/Los_Angeles"
    }
    with patch("caltool.cli.GCalClient", return_value=mock_client):
        with patch("builtins.open", mock_open(read_data=json.dumps(config))):
            runner = CliRunner()
            result = runner.invoke(cli, [
                "free", "--start-date", "2025-05-02", "--end-date", "2025-05-02", "--pretty"
            ])
    assert result.exit_code == 0
    assert "Available Time Slots" in result.output

def test_free_command_error(monkeypatch):
    # Simulate error in command logic
    with patch("caltool.cli.GCalClient", side_effect=Exception("fail")):
        config = {"CREDENTIALS_FILE": "c", "TOKEN_FILE": "t", "SCOPES": [], "CALENDAR_IDS": ["primary"], "AVAILABILITY_START": "08:00", "AVAILABILITY_END": "18:00", "TIME_ZONE": "America/Los_Angeles"}
        with patch("builtins.open", mock_open(read_data=json.dumps(config))):
            runner = CliRunner()
            result = runner.invoke(cli, ["free", "--start-date", "2025-05-02", "--end-date", "2025-05-02"])
    assert result.exit_code != 0
    assert "Error:" in result.output

def test_show_events_invalid_time(monkeypatch):
    config = {"CREDENTIALS_FILE": "c", "TOKEN_FILE": "t", "SCOPES": [], "CALENDAR_IDS": ["primary"], "AVAILABILITY_START": "08:00", "AVAILABILITY_END": "18:00", "TIME_ZONE": "America/Los_Angeles"}
    with patch("builtins.open", mock_open(read_data=json.dumps(config))):
        # Patch GCalClient so CLI proceeds to time parsing
        with patch("caltool.cli.GCalClient", return_value=Mock()):
            runner = CliRunner()
            result = runner.invoke(cli, ["show-events", "--start-time", "not-a-date"])
    assert result.exit_code != 0
    assert "Invalid datetime format" in result.output

def test_require_config_decorator(tmp_path):
    # Simulate missing config file
    @require_config
    def dummy(config):
        return config
    with patch("os.path.exists", return_value=False):
        with patch("caltool.cli.prompt_for_config", return_value=None):
            with patch("click.confirm", return_value=False):
                import click
                with pytest.raises(click.Abort):
                    dummy()

# --- GCAL CLIENT TESTS ---
@patch("caltool.gcal_client.build", return_value=Mock(name="service"))
def test_gcalclient_authenticate_token(mock_build, monkeypatch):
    creds_mock = Mock()
    creds_mock.to_json.return_value = "{}"
    monkeypatch.setattr("os.path.exists", lambda path: True)
    monkeypatch.setattr("google.oauth2.credentials.Credentials.from_authorized_user_file", lambda f, s: creds_mock)
    monkeypatch.setattr(creds_mock, "valid", True)
    client = GCalClient("c", "t", ["scope"])
    assert client.service is not None

@patch("caltool.gcal_client.build", return_value=Mock(name="service"))
@patch("google.oauth2.credentials.Credentials.from_authorized_user_file")
def test_gcalclient_authenticate_refresh(mock_from_file, mock_build, monkeypatch):
    creds_mock = Mock()
    creds_mock.to_json.return_value = "{}"
    creds_mock.valid = False
    creds_mock.expired = True
    creds_mock.refresh_token = True
    creds_mock.refresh = lambda req: None
    mock_from_file.return_value = creds_mock
    monkeypatch.setattr("os.path.exists", lambda path: True)
    client = GCalClient("c", "t", ["scope"])
    assert client.service is not None

def test_gcalclient_retry(monkeypatch):
    # Test retry logic for API calls
    service_mock = Mock()
    call_count = {"count": 0}
    def fail_then_succeed(*a, **kw):
        call_count["count"] += 1
        if call_count["count"] < 2:
            raise HttpError(resp=Mock(), content=b"fail")
        return {"items": ["foo"]}
    service_mock.calendarList().list().execute.side_effect = fail_then_succeed
    client = GCalClient("c", "t", ["scope"], service=service_mock)
    assert client.get_calendar_list() == ["foo"]

def test_gcalclient_get_events(monkeypatch):
    # Test get_events returns events and adds calendarId
    service_mock = Mock()
    service_mock.events().list().execute.return_value = {"items": [{"id": 1}]}
    client = GCalClient("c", "t", ["scope"], service=service_mock)
    events = client.get_events("primary")
    assert events[0]["id"] == 1
    assert events[0]["calendarId"] == "primary"
