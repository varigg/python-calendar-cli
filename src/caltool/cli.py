import datetime
import logging
import os
from zoneinfo import ZoneInfo

import click
from colorama import Fore, Style
from tabulate import tabulate

from .config import Config
from .gcal_client import GCalClient
from .scheduler import Scheduler


def cli_error(message: str, suggestion: str = "", abort: bool = True):
    """Consistent CLI error reporting."""
    import click
    click.echo(click.style(message, fg="red"))
    if suggestion:
        click.echo(click.style(suggestion, fg="yellow"))
    if abort:
        raise click.Abort()

# --- Unified CLI Group ---
@click.group()
@click.option("--debug", is_flag=True, help="Enable debug logging for troubleshooting.")
@click.pass_context
def cli(ctx, debug):
    """Calendar CLI tool for managing Google Calendar availability and events."""
    if debug:
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    # Load config once and pass as obj
    config = Config()
    try:
        config.validate()
    except Exception as e:
        click.echo(click.style(f"Config error: {e}", fg="red"))
        raise click.Abort()
    ctx.obj = config

@cli.command("config")
@click.pass_obj
def config_cmd(config):
    """Interactively set up or edit your calendarcli configuration."""
    click.echo(click.style("Starting interactive config setup...", fg="cyan"))
    config.prompt()
    config.save()
    click.echo(click.style("Configuration saved.", fg="green"))

logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

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
            tz = ZoneInfo(config["TIME_ZONE"])
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

@cli.command(help="Find free time slots in your calendar(s).")
@click.option("--start-date", help="Start date for checking availability (YYYY-MM-DD).", required=True)
@click.option("--end-date", help="End date for checking availability (YYYY-MM-DD).", required=True)
@click.option("--duration", default=30, show_default=True, help="Duration in minutes for the time slot.")
@click.option("--availability-start", help="Start time for availability (HH:MM).", required=False)
@click.option("--availability-end", help="End time for availability (HH:MM).", required=False)
@click.option("--timezone", help="Time zone for the availability hours.", required=False)
@click.option("--pretty", is_flag=True, help="Pretty print the output.")
@click.pass_obj
def free(config, start_date, end_date, duration, availability_start, availability_end, timezone, pretty):
    try:
        client = GCalClient(
            os.path.expanduser(config.get("CREDENTIALS_FILE")),
            os.path.expanduser(config.get("TOKEN_FILE")),
            config.get("SCOPES"),
        )
        scheduler = Scheduler(
            calendar_ids=config.get("CALENDAR_IDS"),
            client=client,
            start_date=start_date,
            end_date=end_date,
            duration=duration,
            start_time=availability_start if availability_start else config.get("AVAILABILITY_START"),
            end_time=availability_end if availability_end else config.get("AVAILABILITY_END"),
            timezone=timezone if timezone else config.get("TIME_ZONE"),
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
        import google.auth.exceptions
        if isinstance(e, google.auth.exceptions.GoogleAuthError) or "invalid_scope" in str(e):
            click.echo(click.style("Google authentication failed. Please check your credentials, token, and SCOPES in config.", fg="red"))
            click.echo(click.style("Run 'caltool config' to set up or update your configuration.", fg="yellow"))
        else:
            click.echo(click.style(f"Error: {e}", fg="red"))
        raise click.Abort()

@cli.command(help="List all available calendars.")
@click.pass_obj
def get_calendars(config):
    try:
        client = GCalClient(
            config.get("CREDENTIALS_FILE"),
            config.get("TOKEN_FILE"),
            config.get("SCOPES"),
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
        import google.auth.exceptions
        if isinstance(e, google.auth.exceptions.GoogleAuthError) or "invalid_scope" in str(e):
            click.echo(click.style("Google authentication failed. Please check your credentials, token, and SCOPES in config.", fg="red"))
            click.echo(click.style("Run 'caltool config' to set up or update your configuration.", fg="yellow"))
    # All errors are now handled by cli_error

@cli.command(help="Show upcoming events from all calendars.")
@click.option("--start-time", help="Start time for fetching events (ISO format).", required=False)
@click.option("--end-time", help="End time for fetching events (ISO format).", required=False)
@click.pass_obj
def show_events(config, start_time, end_time):
    """Show upcoming events from all calendars in a readable format."""
    try:
        client = GCalClient(
            config.get("CREDENTIALS_FILE"),
            config.get("TOKEN_FILE"),
            config.get("SCOPES"),
        )
        start_time_dt = parse_datetime_option(start_time)
        end_time_dt = parse_datetime_option(end_time, default=datetime.datetime.now() + datetime.timedelta(hours=8))
        events = []
        for calendar_id in config.get("CALENDAR_IDS"):
            events.extend(client.get_events(calendar_id, start_time=start_time_dt, end_time=end_time_dt))
        events.sort(key=lambda e: e["start"].get("dateTime", e["start"].get("date")))
        calendar_colors = get_calendar_colors(config.get("CALENDAR_IDS"))
        click.echo(click.style("Upcoming Events:", fg="cyan"))
        for event in events:
            logger.debug(f"show_events: formatting event summary={event.get('summary', 'Busy')}")
            for line in format_event(event, calendar_colors, config):
                click.echo(line)
    except Exception as e:
        import google.auth.exceptions
        if isinstance(e, google.auth.exceptions.GoogleAuthError) or "invalid_scope" in str(e):
            click.echo(click.style("Google authentication failed. Please check your credentials, token, and SCOPES in config.", fg="red"))
            click.echo(click.style("Run 'caltool config' to set up or update your configuration.", fg="yellow"))
        else:
            click.echo(click.style(f"Error: {e}", fg="red"))
        raise click.Abort()

