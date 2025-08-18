"""
Datetime parsing and formatting utilities for calendarcli.
"""
import datetime
from typing import Optional


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
            import zoneinfo
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
