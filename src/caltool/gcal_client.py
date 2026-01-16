"""Google Calendar API client.

This module provides GCalClient for interacting with the Google Calendar API.
It inherits from GoogleAPIClient to leverage shared patterns for authentication,
error handling, and retry logic.
"""

import datetime
import logging

from googleapiclient.errors import HttpError

from .datetime_utils import to_zulutime
from .google_client import GoogleAPIClient

logger = logging.getLogger(__name__)


class GCalClient(GoogleAPIClient):
    """Client for Google Calendar API operations.

    Inherits common authentication, error handling, and retry patterns from
    GoogleAPIClient. Provides calendar-specific methods for listing calendars,
    fetching busy times, retrieving events, and getting event details.
    """

    API_NAME = "calendar"
    API_VERSION = "v3"

    def __init__(self, config, service=None):
        """Initialize GCalClient for Calendar API.

        Args:
            config: Config object with credentials and settings
            service: Optional pre-built service object (for testing)
        """
        super().__init__(config, self.API_NAME, self.API_VERSION, service)

    def _validate_config(self):
        """Validate calendar-specific configuration.

        Calendar clients don't have special config requirements beyond
        the base GoogleAPIClient validation.
        """
        # Base validation covers CREDENTIALS_FILE, TOKEN_FILE, SCOPES
        super()._validate_config()

    @GoogleAPIClient.retry(max_retries=3, delay=2, allowed_exceptions=(HttpError,))
    def get_calendar_list(self):
        """Get list of all available calendars.

        Returns:
            List of calendar objects from Google Calendar API

        Raises:
            CLIError: If API call fails
        """
        logger.debug("Retrieving list of calendars")
        calendar_list = self.service.calendarList().list().execute()
        calendars = calendar_list.get("items", [])
        return calendars

    @GoogleAPIClient.retry(max_retries=3, delay=2, allowed_exceptions=(HttpError,))
    def get_day_busy_times(
        self, calendar_ids: list, day_start: datetime.datetime, day_end: datetime.datetime, timezone: str
    ) -> list:
        """Get busy times for a specific day within availability hours.

        Args:
            calendar_ids: List of calendar IDs to query
            day_start: Start of time range
            day_end: End of time range
            timezone: Timezone for the query

        Returns:
            List of busy time periods

        Raises:
            CLIError: If API call fails
        """
        logger.debug(f"Fetching busy times between {day_start} and {day_end}")
        body = {
            "timeMin": to_zulutime(day_start),
            "timeMax": to_zulutime(day_end),
            "timeZone": timezone,
            "items": [{"id": cal_id} for cal_id in calendar_ids],
        }
        busy_times = self.service.freebusy().query(body=body).execute()
        all_busy = []
        for calendar in busy_times["calendars"].values():
            all_busy.extend(calendar.get("busy", []))
        all_busy.sort(key=lambda x: x["start"])
        return all_busy

    @GoogleAPIClient.retry(max_retries=3, delay=2, allowed_exceptions=(HttpError,))
    def get_event_details(self, calendar_id: str, event_id: str):
        """Get details of a specific event.

        Args:
            calendar_id: The ID of the calendar
            event_id: The ID of the event

        Returns:
            Event details from Google Calendar API

        Raises:
            CLIError: If API call fails
        """
        logger.debug(f"Retrieving details for event {event_id} in calendar {calendar_id}")
        event = self.service.events().get(calendarId=calendar_id, eventId=event_id).execute()
        return event

    @GoogleAPIClient.retry(max_retries=3, delay=2, allowed_exceptions=(HttpError,))
    def get_events(self, calendar_id, start_time=None, end_time=None):
        """Get events from a specific calendar.

        Args:
            calendar_id: The ID of the calendar
            start_time: Start of time range (optional)
            end_time: End of time range (optional)

        Returns:
            List of events from Google Calendar API

        Raises:
            CLIError: If API call fails
        """
        logger.debug(f"Retrieving events for calendar {calendar_id} between {start_time} and {end_time}")
        params = {
            "calendarId": calendar_id,
            "maxResults": 250,
            "singleEvents": True,
            "orderBy": "startTime",
        }
        if start_time:
            params["timeMin"] = to_zulutime(start_time)
        if end_time:
            params["timeMax"] = to_zulutime(end_time)
        events_result = self.service.events().list(**params).execute()
        events = events_result.get("items", [])
        for event in events:
            event["calendarId"] = calendar_id
        logger.debug(f"Found {len(events)} events for calendar {calendar_id}")
        return events
