import datetime
import json  # Import JSON to load the config file
import logging
import os.path
from zoneinfo import ZoneInfo

import click
from colorama import Fore, Style
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from tabulate import tabulate

# Configure logging
logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# --- Load Configuration ---
with open("config.json", "r") as config_file:
    CONFIG = json.load(config_file)

SCOPES = CONFIG["SCOPES"]
CREDENTIALS_FILE = CONFIG["CREDENTIALS_FILE"]
TOKEN_FILE = CONFIG["TOKEN_FILE"]
TIME_ZONE = CONFIG["TIME_ZONE"]

# Parse availability hours from config
local_tz = ZoneInfo(TIME_ZONE)  # Load the local time zone from config
AVAILABILITY_START = datetime.time.fromisoformat(CONFIG["AVAILABILITY_START"])
AVAILABILITY_END = datetime.time.fromisoformat(CONFIG["AVAILABILITY_END"])

START_DATE = datetime.date.fromisoformat(CONFIG["START_DATE"])
END_DATE = datetime.date.fromisoformat(CONFIG["END_DATE"])


# Convert availability hours to UTC
def convert_to_utc(local_time: datetime.time, tz: ZoneInfo) -> datetime.time:
    """Convert a local time to UTC."""
    now = datetime.datetime.now(tz)  # Get the current date in the local time zone
    local_dt = datetime.datetime.combine(now.date(), local_time, tz)  # Combine date and time
    utc_dt = local_dt.astimezone(datetime.timezone.utc)  # Convert to UTC
    return utc_dt.time()  # Return the time part


# --- Authenticate using OAuth2 ---
def authenticate():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
    return creds


def get_calendar_list(service):
    """Get list of all available calendars."""
    logger.debug("Retrieving list of calendars")
    calendar_list = service.calendarList().list().execute()
    calendars = calendar_list.get("items", [])
    logger.debug(f"Found {len(calendars)} calendars")
    logger.debug("Calendar IDs:")
    for calendar in calendars:
        logger.debug(f" - {calendar['summary']} ({calendar['id']})")
    return calendars


# --- Retrieve Calendar Events (Busy Slots) ---
def get_busy_time_ranges(
    service,
    start_time: datetime.datetime,
    end_time: datetime.datetime,
):
    """Get busy times for specified calendars."""
    logger.debug(f"timeMin: {start_time.isoformat()}")
    logger.debug(f"timeMax: {end_time.isoformat()}")

    calendar_ids = CONFIG["CALENDAR_IDS"]

    # Prepare items list for query
    items = [{"id": cal_id} for cal_id in calendar_ids]

    body = {
        "timeMin": start_time.astimezone(tz=datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
        "timeMax": end_time.astimezone(tz=datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
        "timeZone": TIME_ZONE,
        "items": items,
    }

    busy_times = service.freebusy().query(body=body).execute()
    logger.debug(f"Retrieved busy times from calendars")
    logger.debug(json.dumps(busy_times, indent=2))

    # Combine busy times from all calendars
    all_busy = []
    for calendar in busy_times["calendars"].values():
        all_busy.extend(calendar.get("busy", []))

    # Sort and merge overlapping slots
    all_busy.sort(key=lambda x: x["start"])
    merged = []
    for busy in all_busy:
        if not merged or busy["start"] > merged[-1]["end"]:
            merged.append(busy)
        else:
            merged[-1]["end"] = max(merged[-1]["end"], busy["end"])

    return merged


def is_slot_long_enough(start: datetime.datetime, end: datetime.datetime, duration_minutes: int) -> bool:
    """Check if the time slot is long enough for the specified duration."""
    return (end - start).total_seconds() >= duration_minutes * 60


def is_within_availability(
    time: datetime.time,
    duration_minutes: int,
    availability_start: datetime.time,
    availability_end: datetime.time,
) -> bool:
    """Check if the time is within the availability hours and fits within the duration."""
    # Add the duration to the current time
    end_time = (
        datetime.datetime.combine(datetime.date.today(), time) + datetime.timedelta(minutes=duration_minutes)
    ).time()
    logger.debug(f"Checking availability: {time} to {end_time}")
    return availability_start <= time < availability_end and end_time <= availability_end


# --- Find Free Time Slots ---
def find_free_slots(
    busy,
    start_time: datetime.datetime,
    end_time: datetime.datetime,
    duration_minutes: int,
    availability_start: datetime.time = AVAILABILITY_START,
    availability_end: datetime.time = AVAILABILITY_END,
):
    free_slots = []
    cursor = start_time
    remaining_busy = busy.copy()  # Make a copy to preserve the original list

    while cursor < end_time:
        # Calculate the end of the availability window for the current day
        day_end = datetime.datetime.combine(cursor.date(), availability_end, tzinfo=cursor.tzinfo)
        end_range = min(day_end, end_time)
        logger.debug(f"Checking free slots from {cursor} to {end_range}")

        # Filter events that intersect with current day
        current_day_busy = []
        i = 0
        while i < len(remaining_busy):
            event = remaining_busy[i]
            event_start = datetime.datetime.fromisoformat(event["start"]).astimezone(tz=cursor.tzinfo)
            event_end = datetime.datetime.fromisoformat(event["end"]).astimezone(tz=cursor.tzinfo)

            # If event ends before cursor, remove it
            if event_end <= cursor:
                remaining_busy.pop(i)
                continue

            # If event starts after day_end, skip it for now
            if event_start >= day_end:
                i += 1
                continue

            # Event intersects with current day
            current_day_busy.append({"start": max(event_start, cursor), "end": min(event_end, day_end)})
            i += 1

        # Process events for current day
        current_cursor = cursor
        for i, event in enumerate(current_day_busy):
            busy_start = event["start"]
            busy_end = event["end"]

            # Check the free slot before the busy event
            if is_slot_long_enough(current_cursor, busy_start, duration_minutes) and is_within_availability(
                current_cursor.time(), duration_minutes, availability_start, availability_end
            ):
                marker = (
                    "(adjacent)"
                    if (current_cursor == busy_end) or (i > 0 and current_cursor == current_day_busy[i - 1]["end"])
                    else ""
                )
                free_slots.append((current_cursor, busy_start, marker))

            current_cursor = max(current_cursor, busy_end)

        # Check the free slot after the last busy event for the current day
        if is_slot_long_enough(current_cursor, end_range, duration_minutes) and is_within_availability(
            current_cursor.time(), duration_minutes, availability_start, availability_end
        ):
            marker = "(adjacent)" if current_day_busy and current_cursor == current_day_busy[-1]["end"] else ""
            free_slots.append((current_cursor, end_range, marker))

        # Move the cursor to the start of the next day
        next_day_start = datetime.datetime.combine(
            cursor.date() + datetime.timedelta(days=1), availability_start, tzinfo=cursor.tzinfo
        )
        cursor = next_day_start

    return free_slots


@click.group()
@click.option("--debug", is_flag=True, help="Enable debug logging")
def cli(debug):
    """Calendar CLI tool for managing availability."""
    # Set debug level if flag is present
    if debug:
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")


@cli.command()
@click.option("--start-date", default=START_DATE, help="Start date for checking availability.")
@click.option("--end-date", default=END_DATE, help="End date for checking availability.")
@click.option("--duration", default=30, help="Duration in minutes for the time slot.")
@click.option("--availability-start", default=CONFIG["AVAILABILITY_START"], help="Start time for availability.")
@click.option("--availability-end", default=CONFIG["AVAILABILITY_END"], help="End time for availability.")
@click.option("--timezone", default=TIME_ZONE, help="Time zone for the availability hours.")
def free(start_date, end_date, duration, availability_start, availability_end, timezone) -> None:
    """Find free time slots in calendar(s)."""

    logger.debug("Starting calendar availability check")
    creds = authenticate()
    service = build("calendar", "v3", credentials=creds)

    # Convert start and end dates to offset aware UTC
    start = datetime.datetime.fromisoformat(start_date).astimezone(ZoneInfo(timezone))
    end = datetime.datetime.fromisoformat(end_date).astimezone(ZoneInfo(timezone))
    availability_hours_start = datetime.time.fromisoformat(availability_start)
    availability_hours_end = datetime.time.fromisoformat(availability_end)

    logger.debug(f"Checking for free slots between {start} and {end}")
    logger.debug(f"Using timezone: {timezone}")
    logger.debug(f"Availability hours: {availability_hours_start} to {availability_hours_end}")

    busy = get_busy_time_ranges(service, start, end)
    logger.debug(f"Found {len(busy)} busy slots")

    # Use availability hours from config
    slots = find_free_slots(
        busy,
        start,
        end,
        duration,
        availability_hours_start,
        availability_hours_end,
    )
    logger.debug(f"Found {len(slots)} free slots")

    # Print available time slots in a visually enhanced format
    print(Fore.CYAN + "Available Time Slots:" + Style.RESET_ALL)
    print(Fore.YELLOW + "=" * 50 + Style.RESET_ALL)

    # Prepare data for tabular output
    table_data = []
    for s, e, marker in slots:
        s_formatted = s.astimezone(ZoneInfo(TIME_ZONE)).strftime("%a %m/%d %I:%M %p")
        e_formatted = e.astimezone(ZoneInfo(TIME_ZONE)).strftime("%I:%M %p")
        table_data.append(
            [
                Fore.GREEN + s_formatted + Style.RESET_ALL,
                Fore.GREEN + e_formatted + Style.RESET_ALL,
                Fore.RED + marker + Style.RESET_ALL,
            ]
        )

    # Print the table
    print(
        tabulate(
            table_data,
            headers=[
                Fore.CYAN + "Start Time" + Style.RESET_ALL,
                Fore.CYAN + "End Time" + Style.RESET_ALL,
                Fore.CYAN + "Marker" + Style.RESET_ALL,
            ],
            tablefmt="grid",
        )
    )

    print(Fore.YELLOW + "=" * 50 + Style.RESET_ALL)


@cli.command()
def get_calendars():
    """List all available calendars."""

    creds = authenticate()
    service = build("calendar", "v3", credentials=creds)

    calendars = get_calendar_list(service)

    # Print calendars in a tabular format
    print(Fore.CYAN + "Available Calendars:" + Style.RESET_ALL)
    print(Fore.YELLOW + "=" * 50 + Style.RESET_ALL)

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
    print(Fore.YELLOW + "=" * 50 + Style.RESET_ALL)


if __name__ == "__main__":
    cli()
