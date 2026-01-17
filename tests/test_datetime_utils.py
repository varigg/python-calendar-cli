"""
Unit tests for datetime_utils.py
"""

import datetime

import pytest

from gtool.utils.datetime import format_event_time, parse_date_range, parse_time_option

# --- parse_date_range tests ---


def test_today_plus_1():
    """Test parse_date_range returns datetime objects for today+1."""
    start, end = parse_date_range("today+1")
    # Should return datetime objects
    assert isinstance(start, datetime.datetime)
    assert isinstance(end, datetime.datetime)
    # Start should be today at 00:00:00
    assert start.date() == datetime.date.today()
    assert start.time() == datetime.time(0, 0, 0)
    # End should be tomorrow at 23:59:59
    assert end.date() == datetime.date.today() + datetime.timedelta(days=1)
    assert end.time() == datetime.time(23, 59, 59)


def test_tomorrow_plus_2():
    """Test parse_date_range returns datetime objects for tomorrow+2."""
    start, end = parse_date_range("tomorrow+2")
    assert isinstance(start, datetime.datetime)
    assert isinstance(end, datetime.datetime)
    # Start should be tomorrow
    assert start.date() == datetime.date.today() + datetime.timedelta(days=1)
    # End should be 3 days from today
    assert end.date() == datetime.date.today() + datetime.timedelta(days=3)


def test_weekday_plus_0():
    """Test parse_date_range with weekday name."""
    # Find next Thursday from today
    today = datetime.date.today()
    thursday = today + datetime.timedelta((3 - today.weekday() + 7) % 7)
    start, end = parse_date_range("thursday")
    assert isinstance(start, datetime.datetime)
    assert isinstance(end, datetime.datetime)
    assert start.date() == thursday
    assert end.date() == thursday


def test_weekday_plus_1():
    """Test parse_date_range with weekday name and offset."""
    today = datetime.date.today()
    thursday = today + datetime.timedelta((3 - today.weekday() + 7) % 7)
    friday = thursday + datetime.timedelta(days=1)
    start, end = parse_date_range("thursday+1")
    assert isinstance(start, datetime.datetime)
    assert isinstance(end, datetime.datetime)
    assert start.date() == thursday
    assert end.date() == friday


def test_invalid_range():
    with pytest.raises(ValueError):
        parse_date_range("noday+1")


def test_parse_date_range_with_timezone():
    """Test parse_date_range with valid timezone."""
    # Should not raise an error and should use the timezone
    start, end = parse_date_range("today", "America/Los_Angeles")
    assert isinstance(start, datetime.datetime)
    assert isinstance(end, datetime.datetime)
    # Should be timezone-aware
    assert start.tzinfo is not None
    assert end.tzinfo is not None
    # Should be in the specified timezone
    assert str(start.tzinfo) == "America/Los_Angeles"


def test_parse_date_range_with_invalid_timezone():
    """Test parse_date_range with invalid timezone falls back gracefully."""
    # Should not crash, just use naive datetime
    start, end = parse_date_range("today", "Invalid/Timezone")
    assert isinstance(start, datetime.datetime)
    assert isinstance(end, datetime.datetime)
    # Will be naive (no timezone) since invalid timezone
    assert start.tzinfo is None


def test_invalid_offset_non_numeric():
    """Test parse_date_range with non-numeric offset."""
    with pytest.raises(ValueError, match="Invalid offset"):
        parse_date_range("today+abc")


def test_parse_time_option_valid():
    """Test parse_time_option with valid time string."""
    t = parse_time_option("14:30")
    assert t == datetime.time(14, 30)


def test_parse_time_option_default():
    """Test parse_time_option returns default when empty."""
    default = datetime.time(9, 0)
    t = parse_time_option("", default=default)
    assert t == default


# --- format_event_time tests ---


def test_format_event_time_regular_event():
    """Test format_event_time with regular timed event."""
    event = {"start": {"dateTime": "2025-05-02T10:00:00-07:00"}, "end": {"dateTime": "2025-05-02T11:30:00-07:00"}}
    result = format_event_time(event, "America/Los_Angeles")
    assert "2025-05-02" in result
    assert "10:00" in result
    assert "11:30" in result
    assert "1h 30m" in result


def test_format_event_time_all_day_event():
    """Test format_event_time with all-day event."""
    event = {"start": {"date": "2025-05-02"}, "end": {"date": "2025-05-03"}}
    result = format_event_time(event, "America/Los_Angeles")
    assert result == "2025-05-02 (All Day)"


def test_format_event_time_with_timezone():
    """Test format_event_time with timezone conversion."""
    event = {
        "start": {"dateTime": "2025-05-02T10:00:00Z"},  # UTC
        "end": {"dateTime": "2025-05-02T11:00:00Z"},
    }
    result = format_event_time(event, "America/Los_Angeles")
    # Should convert from UTC to Pacific (7 hours behind)
    assert "03:00" in result or "02:00" in result  # Depending on DST
    assert "1h" in result or "60m" in result


def test_format_event_time_duration_minutes_only():
    """Test format_event_time with duration less than an hour."""
    event = {"start": {"dateTime": "2025-05-02T10:00:00-07:00"}, "end": {"dateTime": "2025-05-02T10:45:00-07:00"}}
    result = format_event_time(event, "America/Los_Angeles")
    assert "45m" in result
    assert "0h" not in result  # Should not show 0 hours


def test_format_event_time_invalid_data():
    """Test format_event_time with invalid event data falls back gracefully."""
    event = {"start": {"dateTime": "invalid"}, "end": {"dateTime": "also-invalid"}}
    result = format_event_time(event, "America/Los_Angeles")
    # Should return the raw strings without crashing
    assert "invalid" in result
    assert "also-invalid" in result


def test_format_event_time_with_invalid_timezone():
    """Test format_event_time with invalid timezone falls back gracefully."""
    event = {"start": {"dateTime": "2025-05-02T10:00:00-07:00"}, "end": {"dateTime": "2025-05-02T11:00:00-07:00"}}
    # Should not crash with invalid timezone
    result = format_event_time(event, "Invalid/Timezone")
    assert "2025-05-02" in result
    assert "1h" in result or "60m" in result
