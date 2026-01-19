"""Tests for CLI commands.

Tests CLI behavior for get-calendars, free, show-events, and gmail commands.
Uses mocks for client factories to isolate CLI logic from API calls.
"""

import datetime
import re
from unittest.mock import Mock, patch
from zoneinfo import ZoneInfo

from click.testing import CliRunner

from gtool.cli.main import cli

# --- Utility Functions ---


def clean_cli_output(output):
    """Helper to strip ANSI codes, config messages, and empty lines from CLI output."""
    output = re.sub(r"\x1b\[[0-9;]*m", "", output)  # Remove ANSI
    output = "\n".join([line for line in output.splitlines() if not line.startswith("Using configuration file:")])
    output = "\n".join([line for line in output.splitlines() if line.strip()])
    return output


# --- CLI Command Tests: get-calendars ---


def test_get_calendars_command(mock_config, calendar_data):
    """Test get-calendars command with successful response."""
    mock_client = Mock()
    mock_client.get_calendar_list.return_value = calendar_data

    with patch("gtool.cli.main.create_calendar_client", return_value=mock_client):
        runner = CliRunner()
        result = runner.invoke(cli, ["get-calendars"], obj=mock_config)

    assert result.exit_code == 0
    output = clean_cli_output(result.output)
    assert "My Calendar" in output
    assert "Team Calendar" in output


def test_get_calendars_auth_error(mock_config):
    """Test get-calendars command with authentication error."""
    import google.auth.exceptions

    with patch("gtool.cli.main.create_calendar_client") as mock_factory:
        mock_factory.side_effect = google.auth.exceptions.GoogleAuthError("invalid_scope")
        runner = CliRunner()
        result = runner.invoke(cli, ["get-calendars"], obj=mock_config)

    assert result.exit_code != 0


def test_get_calendars_api_error(mock_config):
    """Test get-calendars command with API error."""
    mock_client = Mock()
    mock_client.get_calendar_list.side_effect = Exception("API error")

    with patch("gtool.cli.main.create_calendar_client", return_value=mock_client):
        runner = CliRunner()
        result = runner.invoke(cli, ["get-calendars"], obj=mock_config)

    assert result.exit_code != 0


# --- CLI Command Tests: free ---


def test_free_command(mock_config, busy_times):
    """Test free command with date range and busy times."""
    tz = ZoneInfo("America/Los_Angeles")
    start_dt = datetime.datetime(2025, 5, 2, 0, 0, 0, tzinfo=tz)
    end_dt = datetime.datetime(2025, 5, 3, 23, 59, 59, tzinfo=tz)

    mock_client = Mock()
    mock_client.get_day_busy_times.return_value = busy_times

    with (
        patch("gtool.cli.main.create_calendar_client", return_value=mock_client),
        patch("gtool.cli.main.parse_date_range", return_value=(start_dt, end_dt)),
    ):
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
    assert "PM" in output or "AM" in output


def test_free_command_pretty(mock_config):
    """Test free command with --pretty flag."""
    mock_client = Mock()
    mock_client.get_day_busy_times.return_value = []

    with patch("gtool.cli.main.create_calendar_client", return_value=mock_client):
        runner = CliRunner()
        result = runner.invoke(cli, ["free", "today", "--pretty"], obj=mock_config)

    assert result.exit_code == 0
    assert "Available Time Slots" in result.output


def test_free_command_no_args_defaults_to_today(mock_config):
    """Test free command with no date argument defaults to today."""
    mock_client = Mock()
    mock_client.get_day_busy_times.return_value = []

    with patch("gtool.cli.main.create_calendar_client", return_value=mock_client):
        runner = CliRunner()
        result = runner.invoke(cli, ["free"], obj=mock_config)

    assert result.exit_code == 0


def test_free_command_with_duration(mock_config):
    """Test free command with custom duration."""
    mock_client = Mock()
    mock_client.get_day_busy_times.return_value = []

    with patch("gtool.cli.main.create_calendar_client", return_value=mock_client):
        runner = CliRunner()
        result = runner.invoke(cli, ["free", "today", "--duration", "60"], obj=mock_config)

    assert result.exit_code == 0


# --- CLI Command Tests: show-events ---


def test_show_events_command(mock_config):
    """Test show-events command with successful response."""
    mock_client = Mock()
    mock_client.get_calendar_list.return_value = [
        {"id": "primary", "summary": "My Calendar"},
    ]
    mock_client.get_events.return_value = [
        {
            "id": "event1",
            "summary": "Test Meeting",
            "start": {"dateTime": "2025-05-02T10:00:00-07:00"},
            "end": {"dateTime": "2025-05-02T11:00:00-07:00"},
            "calendarId": "primary",
        }
    ]

    with patch("gtool.cli.main.create_calendar_client", return_value=mock_client):
        runner = CliRunner()
        result = runner.invoke(cli, ["show-events", "today"], obj=mock_config)

    assert result.exit_code == 0
    assert "Test Meeting" in result.output


def test_show_events_invalid_date(mock_config):
    """Test show-events command with invalid date format."""
    with patch("gtool.cli.main.create_calendar_client", return_value=Mock()):
        runner = CliRunner()
        result = runner.invoke(cli, ["show-events", "not-a-date"], obj=mock_config)

    assert result.exit_code != 0


def test_show_events_no_args_defaults_to_today(mock_config):
    """Test show-events command with no date argument defaults to today."""
    mock_client = Mock()
    mock_client.get_calendar_list.return_value = [{"id": "primary", "summary": "My Calendar"}]
    mock_client.get_events.return_value = []

    with patch("gtool.cli.main.create_calendar_client", return_value=mock_client):
        runner = CliRunner()
        result = runner.invoke(cli, ["show-events"], obj=mock_config)

    assert result.exit_code == 0


# --- CLI Command Tests: gmail ---


def test_gmail_list_command(mock_config):
    """Test gmail list command with successful response."""
    mock_client = Mock()
    mock_client.list_messages.return_value = [
        {"id": "msg1", "threadId": "thread1", "snippet": "Test message preview"},
    ]

    with patch("gtool.cli.main.create_gmail_client", return_value=mock_client):
        runner = CliRunner()
        result = runner.invoke(cli, ["gmail", "list", "--count", "5"], obj=mock_config)

    assert result.exit_code == 0
    assert "msg1" in result.output or "1 message" in result.output.lower()


def test_gmail_list_no_messages(mock_config):
    """Test gmail list command with no messages."""
    mock_client = Mock()
    mock_client.list_messages.return_value = []

    with patch("gtool.cli.main.create_gmail_client", return_value=mock_client):
        runner = CliRunner()
        result = runner.invoke(cli, ["gmail", "list"], obj=mock_config)

    assert result.exit_code == 0
    assert "No messages" in result.output


def test_gmail_show_message_command(mock_config):
    """Test gmail show-message command."""
    mock_client = Mock()
    mock_client.get_message.return_value = {
        "id": "msg1",
        "snippet": "Test message",
        "payload": {"headers": [{"name": "Subject", "value": "Test"}]},
    }

    with patch("gtool.cli.main.create_gmail_client", return_value=mock_client):
        runner = CliRunner()
        result = runner.invoke(cli, ["gmail", "show-message", "msg1"], obj=mock_config)

    assert result.exit_code == 0
    assert "msg1" in result.output


def test_gmail_delete_command_with_confirm(mock_config):
    """Test gmail delete command with --confirm flag."""
    # Add modify scope (readonly already in fixture)
    mock_config.data["SCOPES"].append("https://www.googleapis.com/auth/gmail.modify")

    mock_client = Mock()
    mock_client.delete_message.return_value = None

    with patch("gtool.cli.main.create_gmail_client", return_value=mock_client):
        runner = CliRunner()
        result = runner.invoke(cli, ["gmail", "delete", "msg1", "--confirm"], obj=mock_config)

    assert result.exit_code == 0
    assert "deleted" in result.output.lower()
    mock_client.delete_message.assert_called_once_with(message_id="msg1")


def test_gmail_delete_command_cancelled(mock_config):
    """Test gmail delete command cancelled by user."""
    # Add modify scope (readonly already in fixture)
    mock_config.data["SCOPES"].append("https://www.googleapis.com/auth/gmail.modify")

    with patch("gtool.cli.main.create_gmail_client", return_value=Mock()):
        runner = CliRunner()
        # Simulate user typing 'n' to cancel
        result = runner.invoke(cli, ["gmail", "delete", "msg1"], obj=mock_config, input="n\n")

    assert result.exit_code == 0
    assert "cancelled" in result.output.lower()


# ============================================================================
# Phase 3 Tests: User Story 1 - View Email Titles in CLI
# ============================================================================


def test_gmail_list_displays_subjects(mock_config):
    """CLI displays email subjects in formatted table output."""
    mock_client = Mock()
    mock_client.list_messages.return_value = [
        {
            "id": "msg1",
            "threadId": "thread1",
            "subject": "Important Meeting Tomorrow",
            "snippet": "Don't forget about the meeting...",
        },
        {
            "id": "msg2",
            "threadId": "thread2",
            "subject": "Invoice #12345",
            "snippet": "Your invoice is ready...",
        },
        {
            "id": "msg3",
            "threadId": "thread3",
            "subject": "(No Subject)",
            "snippet": "Message without subject...",
        },
    ]

    with patch("gtool.cli.main.create_gmail_client", return_value=mock_client):
        runner = CliRunner()
        result = runner.invoke(cli, ["gmail", "list", "--count", "3"], obj=mock_config)

    assert result.exit_code == 0
    output = clean_cli_output(result.output)

    # Verify subjects are displayed
    assert "Important Meeting Tomorrow" in output
    assert "Invoice #12345" in output
    assert "(No Subject)" in output

    # Verify table structure (headers)
    assert "Subject" in output
    assert "Preview" in output
    assert "Message ID" in output


def test_gmail_list_simple_format(mock_config):
    """CLI supports legacy simple format without table structure."""
    mock_client = Mock()
    mock_client.list_messages.return_value = [
        {
            "id": "msg1",
            "threadId": "thread1",
            "subject": "Test Subject",
            "snippet": "Test preview...",
        },
    ]

    with patch("gtool.cli.main.create_gmail_client", return_value=mock_client):
        runner = CliRunner()
        result = runner.invoke(cli, ["gmail", "list", "--format", "simple"], obj=mock_config)

    assert result.exit_code == 0
    output = clean_cli_output(result.output)

    # Simple format should use legacy output (no table)
    assert "ID: msg1" in output
    assert "Thread: thread1" in output
    assert "Preview:" in output


def test_gmail_list_unicode_subjects(mock_config):
    """CLI correctly renders Unicode characters and emoji in subjects."""
    mock_client = Mock()
    mock_client.list_messages.return_value = [
        {
            "id": "msg1",
            "threadId": "thread1",
            "subject": "🎉 Party Invitation! émoji test",
            "snippet": "You're invited...",
        },
    ]

    with patch("gtool.cli.main.create_gmail_client", return_value=mock_client):
        runner = CliRunner()
        result = runner.invoke(cli, ["gmail", "list"], obj=mock_config)

    assert result.exit_code == 0
    # Unicode should be in output (may be encoded depending on terminal)
    assert "Party Invitation" in result.output


# ============================================================================
# Batch Size Control Tests
# ============================================================================


def test_gmail_list_count_parameter(mock_config):
    """Count parameter controls the number of messages retrieved."""
    mock_client = Mock()
    mock_client.list_messages.return_value = [
        {"id": f"msg{i}", "threadId": f"thread{i}", "subject": f"Subject {i}", "snippet": f"Preview {i}"}
        for i in range(20)
    ]

    with patch("gtool.cli.main.create_gmail_client", return_value=mock_client):
        runner = CliRunner()
        result = runner.invoke(cli, ["gmail", "list", "--count", "20"], obj=mock_config)

    assert result.exit_code == 0
    # Verify list_messages was called with limit=20
    mock_client.list_messages.assert_called_once()
    call_kwargs = mock_client.list_messages.call_args[1]
    assert call_kwargs["limit"] == 20


def test_gmail_list_count_zero(mock_config):
    """Test count=0 returns empty result."""
    mock_client = Mock()
    mock_client.list_messages.return_value = []

    with patch("gtool.cli.main.create_gmail_client", return_value=mock_client):
        runner = CliRunner()
        result = runner.invoke(cli, ["gmail", "list", "--count", "0"], obj=mock_config)

    assert result.exit_code == 0
    assert "No messages found" in result.output
    # Verify list_messages was called with limit=0
    mock_client.list_messages.assert_called_once()
    call_kwargs = mock_client.list_messages.call_args[1]
    assert call_kwargs["limit"] == 0


def test_gmail_list_count_negative_validation(mock_config):
    """Test negative count raises validation error."""
    with patch("gtool.cli.main.create_gmail_client"):
        runner = CliRunner()
        result = runner.invoke(cli, ["gmail", "list", "--count", "-5"], obj=mock_config)

    assert result.exit_code != 0
    assert "count must be non-negative" in result.output


def test_gmail_list_default_count(mock_config):
    """Test default count is 10 when no parameters provided."""
    mock_client = Mock()
    mock_client.list_messages.return_value = []

    with patch("gtool.cli.main.create_gmail_client", return_value=mock_client):
        runner = CliRunner()
        result = runner.invoke(cli, ["gmail", "list"], obj=mock_config)

    assert result.exit_code == 0
    # Verify default limit=10 was used
    call_kwargs = mock_client.list_messages.call_args[1]
    assert call_kwargs["limit"] == 10


# ============================================================================
# Phase 6 Tests: Integration & Cross-Story Tests
# ============================================================================


def test_gmail_list_subject_and_label_combined(mock_config):
    """Integration test for subject display + label filter."""
    mock_client = Mock()
    mock_client.list_messages.return_value = [
        {
            "id": "msg1",
            "threadId": "thread1",
            "subject": "Work: Project Update",
            "snippet": "The project is progressing...",
        },
        {
            "id": "msg2",
            "threadId": "thread2",
            "subject": "Work: Meeting Notes",
            "snippet": "Notes from today's meeting...",
        },
    ]

    with patch("gtool.cli.main.create_gmail_client", return_value=mock_client):
        runner = CliRunner()
        result = runner.invoke(cli, ["gmail", "list", "--label", "Work"], obj=mock_config)

    assert result.exit_code == 0
    output = clean_cli_output(result.output)

    # Verify subjects are displayed
    assert "Work: Project Update" in output
    assert "Work: Meeting Notes" in output

    # Verify label parameter was passed
    mock_client.list_messages.assert_called_once()
    call_kwargs = mock_client.list_messages.call_args[1]
    assert call_kwargs["label"] == "Work"


def test_gmail_list_query_parameter_backward_compat(mock_config):
    """Test backward compatibility with existing --query parameter."""
    mock_client = Mock()
    mock_client.list_messages.return_value = [
        {
            "id": "msg1",
            "threadId": "thread1",
            "subject": "Unread Message",
            "snippet": "This is unread...",
        },
    ]

    with patch("gtool.cli.main.create_gmail_client", return_value=mock_client):
        runner = CliRunner()
        result = runner.invoke(cli, ["gmail", "list", "--query", "is:unread"], obj=mock_config)

    assert result.exit_code == 0
    # Verify query was passed correctly
    mock_client.list_messages.assert_called_once()
    call_kwargs = mock_client.list_messages.call_args[1]
    assert call_kwargs["query"] == "is:unread"

    # Verify subjects are still displayed (US1 + backward compat)
    output = clean_cli_output(result.output)
    assert "Unread Message" in output


def test_gmail_list_all_features_combined(mock_config):
    """Integration test for all features working together."""
    mock_client = Mock()
    mock_client.list_messages.return_value = [
        {
            "id": "msg1",
            "threadId": "thread1",
            "subject": "🎯 Important: Q4 Planning",
            "snippet": "Let's discuss Q4 goals...",
        },
        {
            "id": "msg2",
            "threadId": "thread2",
            "subject": "Team Sync Notes",
            "snippet": "Notes from sync...",
        },
    ]

    with patch("gtool.cli.main.create_gmail_client", return_value=mock_client):
        runner = CliRunner()
        # Combine label, query, count, and format
        result = runner.invoke(
            cli,
            ["gmail", "list", "--label", "Work", "--query", "is:unread", "--count", "2", "--format", "table"],
            obj=mock_config,
        )

    assert result.exit_code == 0

    # Verify all parameters were passed
    mock_client.list_messages.assert_called_once()
    call_kwargs = mock_client.list_messages.call_args[1]
    assert call_kwargs["label"] == "Work"
    assert call_kwargs["query"] == "is:unread"
    assert call_kwargs["limit"] == 2

    # Verify output includes subjects and table format
    output = clean_cli_output(result.output)
    assert "Important: Q4 Planning" in output or "Q4 Planning" in output  # May be truncated
    assert "Subject" in output  # Table header
