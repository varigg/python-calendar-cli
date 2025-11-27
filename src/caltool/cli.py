import logging

import click
from colorama import Fore, Style

from .config import Config
from .datetime_utils import parse_date_range, parse_time_option
from .errors import handle_cli_exception
from .format import format_calendars_table, get_calendar_colors, pretty_print_slots, print_events_grouped_by_date
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
    start_datetime, end_datetime = parse_date_range(date_range, tz)
    
    # Parse availability times
    avail_start_str = availability_start if availability_start else config.get("AVAILABILITY_START")
    avail_end_str = availability_end if availability_end else config.get("AVAILABILITY_END")

    try:
        client = GCalClient(config)
        search_params = SearchParameters(
            start_date=start_datetime.date(),
            end_date=end_datetime.date(),
            start_time=parse_time_option(avail_start_str),
            end_time=parse_time_option(avail_end_str),
            duration=duration,
            timezone=tz,
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
        print(format_calendars_table(calendars))
    except Exception as e:
        handle_cli_exception(e)

@cli.command(help="Show upcoming events from all calendars. Example: caltool show-events today+2")
@click.argument("date_range", required=False)
@click.pass_obj
def show_events(config, date_range):
    """Show upcoming events from all calendars in a readable format."""
    tz = config.get("TIME_ZONE")
    if not date_range:
        date_range = "today"
    start_datetime, end_datetime = parse_date_range(date_range, tz)
    
    try:
        client = GCalClient(config)
        calendar_ids = config.get("CALENDAR_IDS")
        
        # Build calendar_id -> summary mapping
        calendar_list = client.get_calendar_list()
        calendar_names = {cal["id"]: cal["summary"] for cal in calendar_list}
        
        # Fetch and sort events
        events = []
        for calendar_id in calendar_ids:
            events.extend(client.get_events(calendar_id, start_time=start_datetime, end_time=end_datetime))
        events.sort(key=lambda e: e["start"].get("dateTime", e["start"].get("date")))
        
        # Display events grouped by date
        calendar_colors = get_calendar_colors(calendar_ids)
        print_events_grouped_by_date(events, calendar_colors, calendar_names, tz)
    except Exception as e:
        handle_cli_exception(e)
