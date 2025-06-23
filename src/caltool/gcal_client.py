import datetime
import logging
import os.path
import time

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

# --- Retry Decorator ---
def retry_on_exception(max_retries=3, delay=1, allowed_exceptions=(Exception,)):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except allowed_exceptions as e:
                    logger.warning(f"Attempt {attempt+1} failed: {e}")
                    if attempt == max_retries - 1:
                        logger.error(f"All {max_retries} attempts failed.")
                        raise
                    time.sleep(delay)
        return wrapper
    return decorator

class GCalClient:
    """
    A class to interact with Google Calendar API.
    """

    def __init__(self, credentials_file: str, token_file: str, scopes: list, service: object | None = None):
        """
        Initialize the GCalClient with the provided credentials and token files.
        Optionally, inject a mock service for testing.
        """
        self.credentials_file = os.path.expanduser(credentials_file)
        self.token_file = os.path.expanduser(token_file)
        self.scopes = scopes
        self.service = service or self.authenticate()

    def authenticate(self):
        """
        Authenticate the user and create a service object for Google Calendar API.
        """
        creds = None
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, self.scopes)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, self.scopes)
                creds = flow.run_local_server(port=0)
            with open(self.token_file, "w") as token:
                token.write(creds.to_json())
        return build("calendar", "v3", credentials=creds)

    @retry_on_exception(max_retries=3, delay=2, allowed_exceptions=(HttpError,))
    def get_calendar_list(self):
        """
        Get list of all available calendars.
        :return: List of calendars.
        """
        logger.debug("Retrieving list of calendars")
        try:
            calendar_list = self.service.calendarList().list().execute()
            calendars = calendar_list.get("items", [])
            return calendars
        except HttpError as e:
            logger.error(f"Google API error in get_calendar_list: {e}")
            raise

    @retry_on_exception(max_retries=3, delay=2, allowed_exceptions=(HttpError,))
    def get_day_busy_times(self, calendar_ids: list, day_start: datetime.datetime, day_end: datetime.datetime, timezone: str) -> list:
        """Get busy times for a specific day within availability hours."""
        logger.debug(f"Fetching busy times between {day_start} and {day_end}")
        body = {
            "timeMin": day_start.astimezone(datetime.UTC).isoformat().replace("+00:00", "Z"),
            "timeMax": day_end.astimezone(datetime.UTC).isoformat().replace("+00:00", "Z"),
            "timeZone": timezone,
            "items": [{"id": cal_id} for cal_id in calendar_ids],
        }
        try:
            busy_times = self.service.freebusy().query(body=body).execute()
            all_busy = []
            for calendar in busy_times["calendars"].values():
                all_busy.extend(calendar.get("busy", []))
            all_busy.sort(key=lambda x: x["start"])
            return all_busy
        except HttpError as e:
            logger.error(f"Google API error in get_day_busy_times: {e}")
            raise

    @retry_on_exception(max_retries=3, delay=2, allowed_exceptions=(HttpError,))
    def get_event_details(self, calendar_id: str, event_id: str):
        """
        Get details of a specific event.
        :param calendar_id: The ID of the calendar.
        :param event_id: The ID of the event.
        :return: Event details.
        """
        logger.debug(f"Retrieving details for event {event_id} in calendar {calendar_id}")
        try:
            event = self.service.events().get(calendarId=calendar_id, eventId=event_id).execute()
            return event
        except HttpError as e:
            logger.error(f"Google API error in get_event_details: {e}")
            raise

    @retry_on_exception(max_retries=3, delay=2, allowed_exceptions=(HttpError,))
    def get_events(self, calendar_id, start_time=None, end_time=None):
        """
        Get events from a specific calendar between start_time and end_time.
        :param calendar_id: The ID of the calendar
        :param start_time: datetime, start of time range (optional)
        :param end_time: datetime, end of time range (optional)
        :return: List of events
        """
        logger.debug(f"Retrieving events for calendar {calendar_id} between {start_time} and {end_time}")
        params = {
            "calendarId": calendar_id,
            "maxResults": 250,
            "singleEvents": True,
            "orderBy": "startTime",
        }
        if start_time:
            params["timeMin"] = start_time.astimezone(datetime.UTC).isoformat().replace("+00:00", "Z")
        if end_time:
            params["timeMax"] = end_time.astimezone(datetime.UTC).isoformat().replace("+00:00", "Z")
        try:
            events_result = self.service.events().list(**params).execute()
            events = events_result.get("items", [])
            for event in events:
                event["calendarId"] = calendar_id
            logger.debug(f"Found {len(events)} events for calendar {calendar_id}")
            return events
        except HttpError as e:
            logger.error(f"Google API error in get_events: {e}")
            raise
