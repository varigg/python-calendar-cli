"""
Datetime parsing and formatting utilities for calendarcli.
"""
import datetime
from typing import Optional

from colorama import Fore, Style
from tabulate import tabulate


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

def format_slots_table(free_slots: list) -> str:
    """Return a formatted table of free slots as a string."""
    table_data = []
    for s, e in free_slots:
        s_formatted = s.strftime("%a %m/%d %I:%M %p")
        e_formatted = e.strftime("%I:%M %p")
        table_data.append([
            Fore.GREEN + s_formatted + Style.RESET_ALL,
            Fore.GREEN + e_formatted + Style.RESET_ALL,
            Fore.YELLOW + f"{(e - s).seconds // 60} min" + Style.RESET_ALL,
        ])
    return tabulate(
        table_data,
        headers=[
            Fore.CYAN + "Start Time" + Style.RESET_ALL,
            Fore.CYAN + "End Time" + Style.RESET_ALL,
            Fore.CYAN + "Total Time" + Style.RESET_ALL,
        ],
        tablefmt="grid",
    )

def pretty_print_slots(free_slots: list):
    """Pretty print the free slots."""
    print(Fore.CYAN + "Available Time Slots:" + Style.RESET_ALL)
    print(Fore.YELLOW + "=" * 50 + Style.RESET_ALL)
    print(format_slots_table(free_slots))
    print(Fore.YELLOW + "=" * 50 + Style.RESET_ALL)

def get_calendar_colors(calendar_ids):
    """Assign a color to each calendar id."""
    available_colors = ["green", "blue", "magenta", "cyan", "yellow"]
    return {cid: available_colors[i % len(available_colors)] for i, cid in enumerate(calendar_ids)}

def format_event(event, calendar_colors, config):
    """Return a list of formatted lines for a single event."""
    summary = event.get("summary", "Busy")
    calendar_id = event.get("calendarId", "Unknown")
    calendar_color = calendar_colors.get(calendar_id, "white")
    calendar_name = event.get("organizer", {}).get("displayName", "Private")
    summary += f" ({calendar_name})"
    lines = [f"• {Fore.GREEN if calendar_color == 'green' else Fore.BLUE if calendar_color == 'blue' else Fore.MAGENTA if calendar_color == 'magenta' else Fore.CYAN if calendar_color == 'cyan' else Fore.YELLOW if calendar_color == 'yellow' else ''}{summary}{Style.RESET_ALL}"]
    if event.get("location"):
        lines.append(f"    {Fore.BLUE}location: {event['location']}{Style.RESET_ALL}")
    # Always show formatted event time with duration
    event_time_str = format_event_time(event, config.get("TIME_ZONE"))
    lines.append(f"    {Fore.YELLOW}{event_time_str}{Style.RESET_ALL}")
    lines.append("")  # Blank line between events
    return lines
