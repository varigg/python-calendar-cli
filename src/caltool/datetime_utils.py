"""
Datetime parsing and formatting utilities for calendarcli.
"""
import datetime
import zoneinfo
from typing import Optional


def parse_date_range(range_str: str, tz: Optional[str] = None):
    """
    Parse a range string like 'today+1', 'tomorrow+2' and return (start_date, end_date) as YYYY-MM-DD strings.
    """
    today = datetime.datetime.now()
    if tz:
        try:
            today = today.astimezone(zoneinfo.ZoneInfo(tz))
        except Exception:
            pass
    base = today
    weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    range_str_lower = range_str.lower()
    offset_str = ""
    if range_str_lower.startswith("tomorrow"):
        base = today + datetime.timedelta(days=1)
        offset_str = range_str_lower[len("tomorrow"):]
    elif range_str_lower.startswith("today"):
        offset_str = range_str_lower[len("today"):]
    else:
        for i, wd in enumerate(weekdays):
            if range_str_lower.startswith(wd):
                # Find next weekday (including today if matches)
                current_wd = base.weekday()
                target_wd = i
                days_ahead = (target_wd - current_wd + 7) % 7
                base = base + datetime.timedelta(days=days_ahead)
                offset_str = range_str_lower[len(wd):]
                break
        else:
            raise ValueError(f"Invalid range string: {range_str}")
    offset = 0
    if offset_str.startswith("+"):
        try:
            offset = int(offset_str[1:])
        except Exception:
            raise ValueError(f"Invalid offset in range string: {range_str}")
    start_date = base.date()
    end_date = (base + datetime.timedelta(days=offset)).date()
    return start_date.isoformat(), end_date.isoformat()


def parse_datetime_option(value: str, default: Optional[datetime.datetime] = None) -> datetime.datetime:
    """Parse an ISO datetime string or return default/current time."""
    if not value:
        return default or datetime.datetime.now()
    try:
        return datetime.datetime.fromisoformat(value)
    except Exception:
        raise ValueError(f"Invalid datetime format: {value}")

def format_event_time(event: dict, timezone: str) -> str:
    """Format the start and end time of an event as a string with duration."""
    start = event["start"].get("dateTime") or event["start"].get("date")
    end = event["end"].get("dateTime") or event["end"].get("date")
    try:
        # Handle all-day events (date only)
        if "T" not in start:
            start_dt = datetime.datetime.fromisoformat(start)
        else:
            start_dt = datetime.datetime.fromisoformat(start.replace("Z", "+00:00"))
        if "T" not in end:
            end_dt = datetime.datetime.fromisoformat(end)
        else:
            end_dt = datetime.datetime.fromisoformat(end.replace("Z", "+00:00"))
        # Convert to local timezone if possible
        try:
            tz = zoneinfo.ZoneInfo(timezone)
            start_dt = start_dt.astimezone(tz)
            end_dt = end_dt.astimezone(tz)
        except Exception:
            pass
        duration = end_dt - start_dt
        total_minutes = int(duration.total_seconds() // 60)
        hours = total_minutes // 60
        minutes = total_minutes % 60
        duration_str = f" ({hours}h {minutes}m)" if hours else f" ({minutes}m)"
        return f"{start_dt.strftime('%Y-%m-%d %H:%M')} - {end_dt.strftime('%H:%M')}{duration_str}"
    except Exception:
        return f"{start} - {end}"
