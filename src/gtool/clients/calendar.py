"""CalendarClient - composition-based Google Calendar API client.

Refactored to use composition pattern with dependency injection.
Provides calendar operations: list calendars, get events, find free time, etc.
"""

from datetime import date, datetime, time
from typing import Any, List, Optional, Tuple

from gtool.infrastructure.retry import RetryPolicy
from gtool.infrastructure.service_factory import ServiceFactory


class CalendarClient:
    """Google Calendar API client using composition pattern.

    This client manages Google Calendar API operations using composition
    for dependency injection instead of inheritance. Dependencies include
    ServiceFactory for building API services and RetryPolicy for handling
    transient errors.

    Args:
        service_factory: ServiceFactory instance for building API services.
        retry_policy: Optional RetryPolicy for automatic retry handling.
        service: Optional pre-built Google Calendar API service instance.

    Attributes:
        _service_factory: ServiceFactory for building services.
        _retry_policy: RetryPolicy for retry handling.
        _service: Google Calendar API service instance.
    """

    def __init__(
        self,
        service_factory: Optional[ServiceFactory] = None,
        retry_policy: Optional[RetryPolicy] = None,
        service: Optional[Any] = None,
    ) -> None:
        """Initialize the CalendarClient with composition dependencies.

        Args:
            service_factory: ServiceFactory to build Calendar API services.
            retry_policy: Optional RetryPolicy for automatic retries.
            service: Optional pre-built service (for testing or injection).
        """
        self._service_factory = service_factory
        self._retry_policy = retry_policy
        self._service = service

        # Lazy-load service if not provided
        if self._service is None and self._service_factory is not None:
            self._service = self._service_factory.build_service("calendar", "v3")

    def get_calendar_list(self) -> List[dict]:
        """Get list of all accessible calendars.

        Returns a list of calendar objects with id and summary information.

        Returns:
            List of calendar dictionaries with id, summary, and other fields.

        Raises:
            CLIError: If authentication fails or API call fails.

        Example:
            >>> client = CalendarClient(service_factory=factory)
            >>> calendars = client.get_calendar_list()
            >>> for cal in calendars:
            ...     print(cal['summary'])
        """

        def fetch_calendars():
            return self._service.calendarList().list().execute()

        if self._retry_policy is not None:
            result = self._retry_policy.execute(fetch_calendars)
        else:
            result = fetch_calendars()
        return result.get("items", [])

    def get_events(
        self, calendar_id: str, start_time: Optional[Any] = None, end_time: Optional[Any] = None
    ) -> List[dict]:
        """Get events for a calendar within a time range.

        Compatible with old GCalClient API for backward compatibility.

        Args:
            calendar_id: Calendar ID (e.g., "primary", "user@example.com").
            start_time: Optional start time as datetime object.
            end_time: Optional end time as datetime object.

        Returns:
            List of event dictionaries with id, summary, start, end, etc.

        Raises:
            CLIError: If authentication fails or API call fails.
        """

        def fetch_events():
            params = {
                "calendarId": calendar_id,
                "maxResults": 250,
                "singleEvents": True,
                "orderBy": "startTime",
            }
            if start_time:
                if isinstance(start_time, datetime):
                    # Use isoformat() directly - it handles timezone-aware datetimes correctly
                    # Only add 'Z' for naive datetimes (assumed to be UTC)
                    params["timeMin"] = start_time.isoformat() if start_time.tzinfo else start_time.isoformat() + "Z"
                else:
                    params["timeMin"] = start_time
            if end_time:
                if isinstance(end_time, datetime):
                    # Use isoformat() directly - it handles timezone-aware datetimes correctly
                    # Only add 'Z' for naive datetimes (assumed to be UTC)
                    params["timeMax"] = end_time.isoformat() if end_time.tzinfo else end_time.isoformat() + "Z"
                else:
                    params["timeMax"] = end_time
            return self._service.events().list(**params).execute()

        if self._retry_policy is not None:
            result = self._retry_policy.execute(fetch_events)
        else:
            result = fetch_events()
        events = result.get("items", [])
        # Add calendarId to each event for consistency with old client
        for event in events:
            event["calendarId"] = calendar_id
        return events

    def get_day_busy_times(self, calendar_id: str, day: date) -> List[Tuple[datetime, datetime]]:
        """Get busy time slots for a calendar on a specific day.

        Returns list of (start_datetime, end_datetime) tuples for busy periods.
        All datetimes are timezone-aware (UTC).

        Args:
            calendar_id: Calendar ID (e.g., "primary").
            day: Date to query for busy times.

        Returns:
            List of (start_datetime, end_datetime) tuples representing busy slots.

        Raises:
            CLIError: If authentication fails or API call fails.
        """
        # Query full UTC day range for the given local date
        start_time = datetime.combine(day, time.min).isoformat() + "Z"
        end_time = datetime.combine(day, time.max).isoformat() + "Z"

        def fetch_busy():
            return (
                self._service.freebusy()
                .query(
                    body={
                        "timeMin": start_time,
                        "timeMax": end_time,
                        "items": [{"id": calendar_id}],
                    }
                )
                .execute()
            )

        if self._retry_policy is not None:
            result = self._retry_policy.execute(fetch_busy)
        else:
            result = fetch_busy()
        busy_periods = result.get("calendars", {}).get(calendar_id, {}).get("busy", [])

        # Return timezone-aware datetime tuples (UTC)
        return [
            (
                datetime.fromisoformat(period["start"].replace("Z", "+00:00")),
                datetime.fromisoformat(period["end"].replace("Z", "+00:00")),
            )
            for period in busy_periods
        ]
