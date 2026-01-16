"""
Formatting and color helper functions for gtool CLI output.
"""

from collections import defaultdict

import click
from colorama import Fore, Style
from tabulate import tabulate

from gtool.utils.datetime import format_event_time, get_event_date


def format_slots_table(free_slots: list) -> str:
    """Return a formatted table of free slots as a string."""
    table_data = []
    for s, e in free_slots:
        s_formatted = s.strftime("%a %m/%d %I:%M %p")
        e_formatted = e.strftime("%I:%M %p")
        table_data.append(
            [
                Fore.GREEN + s_formatted + Style.RESET_ALL,
                Fore.GREEN + e_formatted + Style.RESET_ALL,
                Fore.YELLOW + f"{(e - s).seconds // 60} min" + Style.RESET_ALL,
            ]
        )
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


def format_event(event, calendar_colors, config, calendar_names=None):
    """
    Return a list of formatted lines for a single event.

    Args:
        event: Event dict from Google Calendar API
        calendar_colors: Dict mapping calendar IDs to color names
        config: Config object or timezone string
        calendar_names: Optional dict mapping calendar IDs to calendar names
    """
    summary = event.get("summary", "Busy")
    calendar_id = event.get("calendarId", "Unknown")
    calendar_color = calendar_colors.get(calendar_id, "white")

    # Use calendar_names if provided, otherwise fall back to organizer displayName
    if calendar_names:
        calendar_name = calendar_names.get(calendar_id, "Unknown")
    else:
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


def format_calendars_table(calendars: list) -> str:
    """
    Format a list of calendars as a colored table.

    Args:
        calendars: List of calendar dicts with 'summary', 'id', and 'accessRole' keys

    Returns:
        Formatted table string ready to print
    """
    table_data = [
        [
            Fore.GREEN + calendar["summary"] + Style.RESET_ALL,
            Fore.BLUE + calendar["id"] + Style.RESET_ALL,
            Fore.YELLOW + calendar.get("accessRole", "unknown") + Style.RESET_ALL,
        ]
        for calendar in calendars
    ]
    return tabulate(
        table_data,
        headers=[
            Fore.CYAN + "Calendar Name" + Style.RESET_ALL,
            Fore.CYAN + "Calendar ID" + Style.RESET_ALL,
            Fore.CYAN + "Access Role" + Style.RESET_ALL,
        ],
        tablefmt="grid",
    )


def print_events_grouped_by_date(events, calendar_colors, calendar_names, timezone):
    """
    Print events grouped by date with formatted output.

    Args:
        events: List of event dicts from Google Calendar API
        calendar_colors: Dict mapping calendar IDs to color names
        calendar_names: Dict mapping calendar IDs to calendar names
        timezone: Timezone string for formatting
    """
    # Group events by date
    grouped = defaultdict(list)
    for event in events:
        date_str = get_event_date(event)
        grouped[date_str].append(event)

    # Print events for each date
    for date, day_events in grouped.items():
        click.echo(click.style(f"Events for {date}", fg="cyan"))
        for event in day_events:
            lines = format_event(event, calendar_colors, timezone, calendar_names)
            for line in lines:
                click.echo(line)
