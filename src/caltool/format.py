"""
Formatting and color helper functions for calendarcli CLI output.
"""
import click
from colorama import Fore, Style
from tabulate import tabulate

from .datetime_utils import format_event_time


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
    lines = [f"• {click.style(summary, fg=calendar_color, bold=True)}"]
    if event.get("location"):
        lines.append(f"    {click.style('location: ' + event['location'], fg='blue')}")
    # Always show formatted event time with duration
    event_time_str = format_event_time(event, config)
    lines.append(f"    {click.style(event_time_str, fg='yellow')}")
    lines.append("")  # Blank line between events
    return lines


