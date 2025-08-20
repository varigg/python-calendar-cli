import logging
from collections import defaultdict

import click
from colorama import Fore, Style
from tabulate import tabulate

from .config import Config
from .datetime_utils import parse_date_range, parse_datetime_option
from .errors import handle_cli_exception
from .format import get_calendar_colors, pretty_print_slots
from .gcal_client import GCalClient
from .scheduler import Scheduler, SearchParameters

logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

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

@cli.command(help="Find free time slots in your calendar(s). Example: caltool free today+1")
@click.argument("date_range", required=False)
@click.option("--duration", default=30, show_default=True, help="Duration in minutes for the time slot.")
@click.option("--availability-start", help="Start time for availability (HH:MM).", required=False)
@click.option("--availability-end", help="End time for availability (HH:MM).", required=False)
@click.option("--timezone", help="Time zone for the availability hours.", required=False)
@click.option("--pretty", is_flag=True, help="Pretty print the output.")
@click.pass_obj
def free(config, date_range, duration, availability_start, availability_end, timezone, pretty):
    tz = timezone if timezone else config.get("TIME_ZONE")
    if not date_range:
        date_range = "today"
    start_date, end_date = parse_date_range(date_range, tz)
    try:
        client = GCalClient(config)
        search_params = SearchParameters(
            start_date=start_date,
            end_date=end_date,
            start_time=availability_start if availability_start else config.get("AVAILABILITY_START"),
            end_time=availability_end if availability_end else config.get("AVAILABILITY_END"),
            duration=duration,
            timezone=timezone if timezone else config.get("TIME_ZONE"),
        )
        scheduler = Scheduler(
            client=client,
            search_params=search_params,
            calendar_ids=config.get("CALENDAR_IDS"),
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
        handle_cli_exception(e)

@cli.command(help="List all available calendars.")
@click.pass_obj
def get_calendars(config):
    try:
        client = GCalClient(config)
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
        handle_cli_exception(e)

@cli.command(help="Show upcoming events from all calendars. Example: caltool show-events today+2")
@click.argument("date_range", required=False)
@click.pass_obj
def show_events(config, date_range):
    tz = config.get("TIME_ZONE")
    if not date_range:
        date_range = "today"
    start_date, end_date = parse_date_range(date_range, tz)
    start_time_dt = parse_datetime_option(start_date + "T00:00:00")
    end_time_dt = parse_datetime_option(end_date + "T23:59:59")
    """Show upcoming events from all calendars in a readable format."""
    try:
        client = GCalClient(config)
        events = []
        calendar_ids = config.get("CALENDAR_IDS")
        # Build calendar_id -> summary mapping
        calendar_list = client.get_calendar_list()
        calendar_names = {cal["id"]: cal["summary"] for cal in calendar_list}
        for calendar_id in calendar_ids:
            events.extend(client.get_events(calendar_id, start_time=start_time_dt, end_time=end_time_dt))
        events.sort(key=lambda e: e["start"].get("dateTime", e["start"].get("date")))
        calendar_colors = get_calendar_colors(calendar_ids)
        # Group events by date
        
        grouped = defaultdict(list)
        for event in events:
            dt_str = event["start"].get("dateTime") or event["start"].get("date")
            date_only = dt_str.split("T")[0]
            grouped[date_only].append(event)
        for date, day_events in grouped.items():
            click.echo(click.style(f"Events for {date}", fg="cyan"))
            for event in day_events:
                logger.debug(f"show_events: formatting event summary={event.get('summary', 'Busy')}")
                # Show start and end time for each event
                start_str = event["start"].get("dateTime") or event["start"].get("date")
                end_str = event["end"].get("dateTime") or event["end"].get("date")
                if "T" in start_str:
                    start_time = start_str.split("T")[1][:5]
                else:
                    start_time = "All day"
                if "T" in end_str:
                    end_time = end_str.split("T")[1][:5]
                else:
                    end_time = "All day"
                summary = event.get("summary", "Busy")
                calendar_id = event.get("calendarId", "Unknown")
                calendar_color = calendar_colors.get(calendar_id, "white")
                calendar_name = calendar_names.get(calendar_id, "Unknown")
                bullet = click.style("• ", fg=calendar_color, bold=True)
                event_line = f"{bullet}{summary} ({calendar_name})"
                time_line = f"    {start_time} - {end_time}"
                click.echo(event_line)
                click.echo(time_line)
                if event.get("location"):
                    location_line = f"    {click.style(event['location'], fg='blue')}"
                    click.echo(location_line)
    except Exception as e:
        handle_cli_exception(e)
