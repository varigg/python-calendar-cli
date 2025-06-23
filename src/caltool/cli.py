import datetime
import json
import logging
import os
from functools import wraps
from zoneinfo import ZoneInfo

import click
from colorama import Fore, Style
from tabulate import tabulate

from .gcal_client import GCalClient
from .scheduler import Scheduler

logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

DEFAULT_CONFIG_FILE = os.path.expanduser("~/.caltool.cfg")

# --- Formatting helpers ---
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

# --- Config decorator/context ---
def require_config(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not os.path.exists(DEFAULT_CONFIG_FILE):
            if click.confirm("Would you like to create a new config file?", default=True):
                prompt_for_config()
            else:
                click.echo(click.style("Configuration file is required.", fg="red"))
                raise click.Abort()
        try:
            with open("config.json") as config_file:
                config = json.load(config_file)
        except Exception as e:
            click.echo(click.style(f"Error loading config.json: {e}", fg="red"))
            raise click.Abort()
        return func(config, *args, **kwargs)
    return wrapper

# --- Time parsing helper ---
def parse_datetime_option(value, default=None):
    if not value:
        return default or datetime.datetime.now()
    try:
        return datetime.datetime.fromisoformat(value)
    except Exception:
        raise click.BadParameter(f"Invalid datetime format: {value}")

def get_calendar_colors(calendar_ids):
    """Assign a color to each calendar id."""
    available_colors = ["green", "blue", "magenta", "cyan", "yellow"]
    return {cid: available_colors[i % len(available_colors)] for i, cid in enumerate(calendar_ids)}

def format_event_time(event, config):
    """Format the start and end time of an event as a string."""
    start = event["start"].get("dateTime", event["start"].get("date"))
    end = event["end"].get("dateTime", event["end"].get("date"))
    try:
        start_dt = datetime.datetime.fromisoformat(start.replace("Z", "+00:00")).astimezone(ZoneInfo(config["TIME_ZONE"]))
        end_dt = datetime.datetime.fromisoformat(end.replace("Z", "+00:00")).astimezone(ZoneInfo(config["TIME_ZONE"]))
        return f"{start_dt.strftime('%H:%M')} - {end_dt.strftime('%H:%M')}"
    except Exception:
        return f"{start} - {end}"

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
    lines.append(f"    {click.style(format_event_time(event, config), fg='yellow')}")
    lines.append("")  # Blank line between events
    return lines

@click.group()
@click.option("--debug", is_flag=True, help="Enable debug logging for troubleshooting.")
def cli(debug):
    """Calendar CLI tool for managing Google Calendar availability and events."""
    if debug:
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")

@cli.command(help="Find free time slots in your calendar(s).")
@click.option("--start-date", help="Start date for checking availability (YYYY-MM-DD).", required=True)
@click.option("--end-date", help="End date for checking availability (YYYY-MM-DD).", required=True)
@click.option("--duration", default=30, show_default=True, help="Duration in minutes for the time slot.")
@click.option("--availability-start", help="Start time for availability (HH:MM).", required=False)
@click.option("--availability-end", help="End time for availability (HH:MM).", required=False)
@click.option("--timezone", help="Time zone for the availability hours.", required=False)
@click.option("--pretty", is_flag=True, help="Pretty print the output.")
@require_config
def free(config, start_date, end_date, duration, availability_start, availability_end, timezone, pretty):
    try:
        client = GCalClient(
            os.path.expanduser(config["CREDENTIALS_FILE"]),
            os.path.expanduser(config["TOKEN_FILE"]),
            config["SCOPES"],
        )
        scheduler = Scheduler(
            calendar_ids=config["CALENDAR_IDS"],
            client=client,
            start_date=start_date,
            end_date=end_date,
            duration=duration,
            start_time=availability_start if availability_start else config["AVAILABILITY_START"],
            end_time=availability_end if availability_end else config["AVAILABILITY_END"],
            timezone=timezone if timezone else config["TIME_ZONE"],
        )
        free_slots = scheduler.get_free_slots()
        if pretty:
            pretty_print_slots(free_slots)
        else:
            for s, e in free_slots:
                s_formatted = s.strftime("%a %m/%d %I:%M %p")
                e_formatted = e.strftime("%I:%M %p")
                print(f"{s_formatted} - {e_formatted}")
    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg="red"))
        raise click.Abort()

@cli.command(help="List all available calendars.")
@require_config
def get_calendars(config):
    try:
        client = GCalClient(
            config["CREDENTIALS_FILE"],
            config["TOKEN_FILE"],
            config["SCOPES"],
        )
        calendars = client.get_calendar_list()
        print(Fore.CYAN + "Available Calendars:" + Style.RESET_ALL)
        table_data = [
            [
                Fore.GREEN + calendar["summary"] + Style.RESET_ALL,
                Fore.BLUE + calendar["id"] + Style.RESET_ALL,
                Fore.YELLOW + calendar.get("accessRole", "unknown") + Style.RESET_ALL,
            ]
            for calendar in calendars
        ]
        print(
            tabulate(
                table_data,
                headers=[
                    Fore.CYAN + "Calendar Name" + Style.RESET_ALL,
                    Fore.CYAN + "Calendar ID" + Style.RESET_ALL,
                    Fore.CYAN + "Access Role" + Style.RESET_ALL,
                ],
                tablefmt="grid",
            )
        )
    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg="red"))
        raise click.Abort()

@cli.command(help="Show upcoming events from all calendars.")
@click.option("--start-time", help="Start time for fetching events (ISO format).", required=False)
@click.option("--end-time", help="End time for fetching events (ISO format).", required=False)
@require_config
def show_events(config, start_time, end_time):
    """Show upcoming events from all calendars in a readable format."""
    try:
        client = GCalClient(
            config["CREDENTIALS_FILE"],
            config["TOKEN_FILE"],
            config["SCOPES"],
        )
        start_time_dt = parse_datetime_option(start_time)
        end_time_dt = parse_datetime_option(end_time, default=datetime.datetime.now() + datetime.timedelta(hours=8))
        events = []
        for calendar_id in config["CALENDAR_IDS"]:
            events.extend(client.get_events(calendar_id, start_time=start_time_dt, end_time=end_time_dt))
        events.sort(key=lambda e: e["start"].get("dateTime", e["start"].get("date")))
        calendar_colors = get_calendar_colors(config["CALENDAR_IDS"])
        click.echo(click.style("Upcoming Events:", fg="cyan"))
        for event in events:
            for line in format_event(event, calendar_colors, config):
                click.echo(line)
    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg="red"))
        raise click.Abort()

def prompt_for_config():
    """Prompt the user to create a config file with default values."""
    click.echo(click.style("Creating a new configuration file...", fg="cyan"))
    credentials_file = click.prompt(
        "Enter the path to your credentials file", default="~/.config/caltool/credentials.json"
    )
    token_file = click.prompt("Enter the path to your token file", default="~/.config/caltool/token.json")
    time_zone = click.prompt("Enter your time zone", default="America/Los_Angeles")
    availability_start = click.prompt("Enter your availability start time (HH:MM)", default="08:00")
    availability_end = click.prompt("Enter your availability end time (HH:MM)", default="18:00")
    calendar_ids = click.prompt(
        "Enter the comma-separated calendar IDs"
        "\n(You can update this later. The get-calendars command"
        " will show your current calendars.)",
        default="primary",
    ).split(",")
    config = {
        "CREDENTIALS_FILE": credentials_file,
        "TOKEN_FILE": token_file,
        "TIME_ZONE": time_zone,
        "AVAILABILITY_START": availability_start,
        "AVAILABILITY_END": availability_end,
        "CALENDAR_IDS": calendar_ids,
    }
    with open(DEFAULT_CONFIG_FILE, "w") as config_file:
        json.dump(config, config_file, indent=4)
    click.echo(click.style(f"Configuration file created at {DEFAULT_CONFIG_FILE}", fg="green"))

if __name__ == "__main__":
    cli()
