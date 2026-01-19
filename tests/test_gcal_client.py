"""Tests for CalendarClient - composition-based Calendar client.

Tests calendar API operations using composition pattern.
No @patch decorators - all dependencies injected via constructor.
"""

from datetime import date, datetime

from gtool.clients.calendar import CalendarClient


def test_gcal_client_get_calendar_list(mock_google_service):
    """FR-007: CalendarClient.get_calendar_list() should return calendars."""
    mock_google_service.calendarList.return_value.list.return_value.execute.return_value = {
        "items": [
            {"id": "primary", "summary": "Primary Calendar"},
            {"id": "secondary", "summary": "Secondary Calendar"},
        ]
    }

    client = CalendarClient(service_factory=None, service=mock_google_service)
    calendars = client.get_calendar_list()

    assert len(calendars) == 2
    assert calendars[0]["id"] == "primary"
    assert calendars[1]["summary"] == "Secondary Calendar"


def test_gcal_client_get_events(mock_google_service):
    """FR-007: CalendarClient.get_events() should return events for date range."""
    mock_google_service.events.return_value.list.return_value.execute.return_value = {
        "items": [
            {
                "id": "event1",
                "summary": "Meeting",
                "start": {"dateTime": "2024-01-15T10:00:00Z"},
            }
        ]
    }

    client = CalendarClient(service_factory=None, service=mock_google_service)
    events = client.get_events("primary", (date(2024, 1, 15), date(2024, 1, 16)))

    assert len(events) == 1
    assert events[0]["summary"] == "Meeting"


def test_gcal_client_get_day_busy_times(mock_google_service):
    """FR-007: CalendarClient.get_day_busy_times() should return busy time slots as datetime tuples."""
    mock_google_service.freebusy.return_value.query.return_value.execute.return_value = {
        "calendars": {
            "primary": {
                "busy": [
                    {
                        "start": "2024-01-15T10:00:00Z",
                        "end": "2024-01-15T11:00:00Z",
                    }
                ]
            }
        }
    }

    client = CalendarClient(service_factory=None, service=mock_google_service)
    busy_times = client.get_day_busy_times("primary", date(2024, 1, 15))

    assert len(busy_times) == 1
    # Should return timezone-aware datetime tuples (UTC)
    assert busy_times[0][0] == datetime.fromisoformat("2024-01-15T10:00:00+00:00")
    assert busy_times[0][1] == datetime.fromisoformat("2024-01-15T11:00:00+00:00")
