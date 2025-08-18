"""
Formatting and color helper functions for calendarcli CLI output.
"""
import click
from colorama import Fore, Style

# format_slots_table is still imported from datetime_utils
from .datetime_utils import format_event_time, format_slots_table


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
    lines = [f"• {click.style(summary, fg=calendar_color, bold=True)}"]
    if event.get("location"):
        lines.append(f"    {click.style('location: ' + event['location'], fg='blue')}")
    # Always show formatted event time with duration
    event_time_str = format_event_time(event, config)
    lines.append(f"    {click.style(event_time_str, fg='yellow')}")
    lines.append("")  # Blank line between events
    return lines


