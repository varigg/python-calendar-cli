import datetime
import logging
import os

import click
from colorama import Fore, Style
from tabulate import tabulate

from .config import Config
from .datetime_utils import parse_datetime_option
from .errors import handle_cli_exception
from .format import format_event, get_calendar_colors, pretty_print_slots
from .gcal_client import GCalClient
from .scheduler import Scheduler


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
        handle_cli_exception(e)

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
        handle_cli_exception(e)

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
        handle_cli_exception(e)
