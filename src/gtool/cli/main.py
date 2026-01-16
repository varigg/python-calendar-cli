import json
import logging

import click
import google.auth.exceptions as google_auth_exceptions
from colorama import Fore, Style

from gtool.config.settings import Config
from gtool.utils.datetime import parse_date_range, parse_time_option
from gtool.infrastructure.error_categorizer import ErrorCategorizer
from gtool.cli.errors import CLIError, handle_cli_exception
from gtool.cli.formatters import (
    format_calendars_table,
    get_calendar_colors,
    pretty_print_slots,
    print_events_grouped_by_date,
)
from gtool.clients.calendar import CalendarClient
from gtool.clients.gmail import GmailClient
from gtool.infrastructure.auth import GoogleAuth
from gtool.infrastructure.retry import RetryPolicy
from gtool.core.scheduler import Scheduler
from gtool.core.models import SearchParameters
from gtool.infrastructure.service_factory import ServiceFactory

logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


# --- Client Factory Functions ---
def _create_client_dependencies(config):
    """Create shared dependencies for API clients."""
    auth = GoogleAuth(config)
    service_factory = ServiceFactory(auth=auth)
    retry_policy = RetryPolicy(max_retries=3, delay=2.0, error_categorizer=ErrorCategorizer())
    return service_factory, retry_policy


def create_calendar_client(config):
    """Create a composed Calendar client with retry policy."""
    service_factory, retry_policy = _create_client_dependencies(config)
    return CalendarClient(service_factory=service_factory, retry_policy=retry_policy)


def create_gmail_client(config):
    """Create a composed Gmail client with retry policy."""
    service_factory, retry_policy = _create_client_dependencies(config)
    return GmailClient(service_factory=service_factory, retry_policy=retry_policy)


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
    except (click.UsageError, CLIError) as e:
        click.echo(click.style(f"Config error: {e}", fg="red"))
        raise click.Abort()
    except google_auth_exceptions.GoogleAuthError as e:
        handle_cli_exception(e)
    ctx.obj = config


@cli.command("config")
@click.pass_obj
def config_cmd(config):
    """Interactively set up or edit your gtool configuration."""
    click.echo(click.style("Starting interactive config setup...", fg="cyan"))
    config.prompt()
    config.save()
    click.echo(click.style("Configuration saved.", fg="green"))


@cli.command(help="Find free time slots in your calendar(s). Example: gtool free today+1")
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
        client = create_calendar_client(config)
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
    except (CLIError, google_auth_exceptions.GoogleAuthError) as e:
        handle_cli_exception(e)


@cli.command(help="List all available calendars.")
@click.pass_obj
def get_calendars(config):
    try:
        client = create_calendar_client(config)
        calendars = client.get_calendar_list()
        print(Fore.CYAN + "Available Calendars:" + Style.RESET_ALL)
        print(format_calendars_table(calendars))
    except (CLIError, google_auth_exceptions.GoogleAuthError) as e:
        handle_cli_exception(e)


@cli.command(help="Show upcoming events from all calendars. Example: gtool show-events today+2")
@click.argument("date_range", required=False)
@click.pass_obj
def show_events(config, date_range):
    """Show upcoming events from all calendars in a readable format."""
    tz = config.get("TIME_ZONE")
    if not date_range:
        date_range = "today"
    start_datetime, end_datetime = parse_date_range(date_range, tz)

    try:
        client = create_calendar_client(config)
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
    except (CLIError, google_auth_exceptions.GoogleAuthError) as e:
        handle_cli_exception(e)


# --- Gmail Commands ---
@cli.group("gmail", help="Manage Gmail messages (requires Gmail scope)")
@click.pass_obj
def gmail(config):
    """Gmail management commands."""
    try:
        config.validate_gmail_scopes()
    except click.UsageError as e:
        raise CLIError(f"Gmail not enabled. Run 'gtool config' to enable Gmail access. Error: {e}")


@gmail.command("list", help="List Gmail messages. Example: gtool gmail list --query 'is:unread' --limit 5")
@click.option("--query", default="", help="Gmail search query (e.g., 'is:unread', 'from:user@example.com').")
@click.option("--limit", default=10, show_default=True, help="Maximum number of messages to retrieve.")
@click.pass_obj
def gmail_list(config, query, limit):
    """List Gmail messages matching the query."""
    try:
        client = create_gmail_client(config)
        messages = client.list_messages(query=query, limit=limit)

        if not messages:
            click.echo(click.style("No messages found.", fg="yellow"))
            return

        click.echo(click.style(f"\nFound {len(messages)} message(s):", fg="cyan"))
        for i, msg in enumerate(messages, 1):
            msg_id = msg.get("id", "N/A")
            snippet = msg.get("snippet", "(no preview)")
            thread_id = msg.get("threadId", "N/A")
            click.echo(f"{i}. ID: {msg_id}")
            click.echo(f"   Thread: {thread_id}")
            click.echo(f"   Preview: {snippet[:80]}...")
            click.echo("")
    except (CLIError, google_auth_exceptions.GoogleAuthError) as e:
        handle_cli_exception(e)


@gmail.command(
    "show-message", help="Show full details of a Gmail message. Example: gtool gmail show-message <message_id>"
)
@click.argument("message_id")
@click.option(
    "--format",
    "format_",
    default="full",
    type=click.Choice(["full", "minimal", "raw", "metadata"]),
    help="Message format.",
)
@click.pass_obj
def gmail_show_message(config, message_id, format_):
    """Show details of a specific Gmail message."""
    try:
        client = create_gmail_client(config)
        message = client.get_message(message_id=message_id)

        click.echo(click.style(f"\nMessage ID: {message_id}", fg="cyan"))
        click.echo(json.dumps(message, indent=2))
    except (CLIError, google_auth_exceptions.GoogleAuthError) as e:
        handle_cli_exception(e)


@gmail.command("delete", help="Delete a Gmail message. Example: gtool gmail delete <message_id>")
@click.argument("message_id")
@click.option("--confirm", is_flag=True, help="Skip confirmation prompt.")
@click.pass_obj
def gmail_delete(config, message_id, confirm):
    """Delete a specific Gmail message."""
    try:
        if not confirm:
            if not click.confirm(f"Are you sure you want to delete message {message_id}?"):
                click.echo(click.style("Deletion cancelled.", fg="yellow"))
                return

        client = create_gmail_client(config)
        client.delete_message(message_id=message_id)
        click.echo(click.style(f"Message {message_id} deleted successfully.", fg="green"))
    except (CLIError, google_auth_exceptions.GoogleAuthError) as e:
        handle_cli_exception(e)
