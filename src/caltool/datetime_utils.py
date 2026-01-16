"""
Datetime parsing and formatting utilities for calendarcli.
"""

import datetime
import zoneinfo
from typing import Optional


def parse_date_range(range_str: str, tz: Optional[str] = None) -> tuple[datetime.datetime, datetime.datetime]:
    """
    Parse a range string like 'today+1', 'tomorrow+2' and return (start_datetime, end_datetime) as timezone-aware datetime objects.

    Returns start of day (00:00:00) and end of day (23:59:59) for the calculated dates.
    """
    # Get current time in the specified timezone
    if tz:
        try:
            timezone = zoneinfo.ZoneInfo(tz)
            today = datetime.datetime.now(timezone)
        except Exception:
            today = datetime.datetime.now()
    else:
        today = datetime.datetime.now()

    base = today
    weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    range_str_lower = range_str.lower()
    offset_str = ""

    if range_str_lower.startswith("tomorrow"):
        base = today + datetime.timedelta(days=1)
        offset_str = range_str_lower[len("tomorrow") :]
    elif range_str_lower.startswith("today"):
        offset_str = range_str_lower[len("today") :]
    else:
        for i, wd in enumerate(weekdays):
            if range_str_lower.startswith(wd):
                # Find next weekday (including today if matches)
                current_wd = base.weekday()
                target_wd = i
                days_ahead = (target_wd - current_wd + 7) % 7
                base = base + datetime.timedelta(days=days_ahead)
                offset_str = range_str_lower[len(wd) :]
                break
        else:
            raise ValueError(f"Invalid range string: {range_str}")

    offset = 0
    if offset_str.startswith("+"):
        try:
            offset = int(offset_str[1:])
        except Exception:
            raise ValueError(f"Invalid offset in range string: {range_str}")

    # Calculate start and end dates
    start_date = base.date()
    end_date = (base + datetime.timedelta(days=offset)).date()

    # Convert to timezone-aware datetime objects (start of day and end of day)
    if tz:
        try:
            timezone = zoneinfo.ZoneInfo(tz)
        except Exception:
            timezone = None
    else:
        timezone = None

    start_datetime = datetime.datetime.combine(start_date, datetime.time(0, 0, 0), tzinfo=timezone)
    end_datetime = datetime.datetime.combine(end_date, datetime.time(23, 59, 59), tzinfo=timezone)

    return start_datetime, end_datetime


def parse_datetime_option(value: str, default: Optional[datetime.datetime] = None) -> datetime.datetime:
    """Parse an ISO datetime string or return default/current time."""
    if not value:
        return default or datetime.datetime.now()
    try:
        return datetime.datetime.fromisoformat(value)
    except Exception:
        raise ValueError(f"Invalid datetime format: {value}")


def parse_time_option(value: str, default: Optional[datetime.time] = None) -> datetime.time:
    """Parse a time string (HH:MM) or return default."""
    if not value:
        return default or datetime.datetime.now().time()
    try:
        return datetime.time.fromisoformat(value)
    except Exception:
        raise ValueError(f"Invalid time format: {value}")


def to_zulutime(dt: datetime.datetime) -> str:
    """
    Convert a datetime object to Zulu time format (UTC with Z suffix).

    Google Calendar API requires timestamps in RFC3339 format with the 'Z' suffix
    for UTC times, rather than the '+00:00' offset notation. While both are valid
    RFC3339, the API specifically expects Zulu time notation.

    Args:
        dt: A datetime object (naive or timezone-aware)

    Returns:
        ISO 8601 string in Zulu time format (e.g., "2025-05-02T17:00:00Z")
    """
    if dt.tzinfo is None:
        # Assume local time if naive, but ideally should be aware
        dt = dt.astimezone()

    # Convert to UTC
    dt_utc = dt.astimezone(datetime.timezone.utc)
    return dt_utc.isoformat().replace("+00:00", "Z")


def _parse_event_dt(dt_str: str) -> datetime.datetime:
    """Helper to parse event datetime string, handling Z suffix."""
    return datetime.datetime.fromisoformat(dt_str)


def get_event_date(event: dict) -> str:
    """
    Extract date string (YYYY-MM-DD) from event start time.

    Handles both timed events (with dateTime) and all-day events (with date).
    """
    dt_str = event["start"].get("dateTime") or event["start"].get("date")
    return dt_str.split("T")[0]


def format_event_time(event: dict, timezone: str) -> str:
    """Format the start and end time of an event as a string with duration."""
    start_str = event["start"].get("dateTime")
    end_str = event["end"].get("dateTime")

    # Handle all-day events (date only, no dateTime)
    if not start_str:
        start_date = event["start"].get("date")
        return f"{start_date} (All Day)"

    try:
        start_dt = _parse_event_dt(start_str)
        end_dt = _parse_event_dt(end_str)

        # Convert to user's timezone if possible
        try:
            tz = zoneinfo.ZoneInfo(timezone)
            if start_dt.tzinfo:
                start_dt = start_dt.astimezone(tz)
                end_dt = end_dt.astimezone(tz)
        except Exception:
            pass  # Use original timezone if conversion fails

        # Calculate and format duration
        duration = end_dt - start_dt
        total_minutes = int(duration.total_seconds() // 60)
        hours = total_minutes // 60
        minutes = total_minutes % 60
        duration_str = f" ({hours}h {minutes}m)" if hours else f" ({minutes}m)"

        return f"{start_dt.strftime('%Y-%m-%d %H:%M')} - {end_dt.strftime('%H:%M')}{duration_str}"
    except Exception:
        return f"{start_str} - {end_str}"
