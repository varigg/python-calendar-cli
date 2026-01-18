import datetime
import logging
from typing import Any

from gtool.core.models import SearchParameters

logger = logging.getLogger(__name__)


class Scheduler:
    """
    A class to manage scheduling and finding free time slots in Google Calendar.
    """

    def __init__(
        self,
        client: Any,
        search_params: SearchParameters,
        calendar_ids: list[str],
    ):
        """
        Initialize the Scheduler with configuration.
        Raises ValueError for invalid arguments.
        """
        self.start_datetime = search_params.start_datetime
        self.end_datetime = search_params.end_datetime
        self.availability_start = search_params.availability_start
        self.availability_end = search_params.availability_end
        self.timezone = search_params.start_datetime.tzinfo

        if not isinstance(search_params.duration, int) or search_params.duration <= 0:
            raise ValueError("Duration must be a positive integer.")
        if not isinstance(calendar_ids, list) or not all(isinstance(cid, str) for cid in calendar_ids):
            raise ValueError("calendar_ids must be a list of strings.")
        self.client = client
        self.duration = search_params.duration
        self.calendar_ids = calendar_ids
        self.logger = logging.getLogger(__name__)
        self.logger.debug(f"Scheduler initialized with config: {self.__dict__}")

    def is_slot_long_enough(self, start: datetime.datetime, end: datetime.datetime, duration_minutes: int) -> bool:
        """
        Check if the time slot is long enough for the specified duration.

        Example:
            >>> s = datetime.datetime(2025, 5, 2, 8, 0)
            >>> e = datetime.datetime(2025, 5, 2, 8, 30)
            >>> Scheduler(...).is_slot_long_enough(s, e, 30)
            True
        Edge cases:
            - Zero or negative duration returns False
            - start == end returns False

        """
        if duration_minutes <= 0 or start >= end:
            return False
        return (end - start).total_seconds() >= duration_minutes * 60

    def get_free_slots_for_day(
        self,
        busy_times: list[tuple[datetime.datetime, datetime.datetime]],
        start: datetime.datetime,
        end: datetime.datetime,
        duration_minutes: int,
    ) -> list[tuple[datetime.datetime, datetime.datetime]]:
        """
        Get free slots for a specific day, handling overlapping and adjacent busy times.

        Args:
            busy_times: List of (start, end) datetime tuples representing busy periods.
            start: Start of availability window.
            end: End of availability window.
            duration_minutes: Minimum slot duration in minutes.

        Returns:
            List of (start, end) datetime tuples representing free slots.
        """
        free_slots = []
        cursor = start
        # Sort and merge overlapping/adjacent busy times
        busy_sorted = sorted(busy_times, key=lambda b: b[0])
        merged_busy = []
        for b_start, b_end in busy_sorted:
            if not merged_busy:
                merged_busy.append((b_start, b_end))
            else:
                last_start, last_end = merged_busy[-1]
                if b_start <= last_end:  # Overlapping or adjacent
                    merged_busy[-1] = (last_start, max(last_end, b_end))
                else:
                    merged_busy.append((b_start, b_end))
        for busy_start, busy_end in merged_busy:
            if self.is_slot_long_enough(cursor, busy_start, duration_minutes):
                free_slots.append((cursor, busy_start))
            cursor = max(cursor, busy_end)
        if cursor < end and self.is_slot_long_enough(cursor, end, duration_minutes):
            free_slots.append((cursor, end))
        return free_slots

    def get_free_slots(self) -> list[tuple[datetime.datetime, datetime.datetime]]:
        """
        Get all free slots between start_datetime and end_datetime (inclusive).
        Handles errors and logs a summary for each day.
        """
        current_datetime = self.start_datetime.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = self.end_datetime.date()
        free_slots = []

        while current_datetime.date() <= end_date:
            current_date = current_datetime.date()
            self.logger.debug(f"Processing date: {current_date}")

            # Build availability window for this day
            day_start = datetime.datetime.combine(current_date, self.availability_start, tzinfo=self.timezone)
            day_end = datetime.datetime.combine(current_date, self.availability_end, tzinfo=self.timezone)

            # Collect busy times from all calendars
            all_busy_times = []
            for calendar_id in self.calendar_ids:
                busy_datetime_tuples = self.client.get_day_busy_times(calendar_id, current_date)
                all_busy_times.extend(busy_datetime_tuples)

            slots = self.get_free_slots_for_day(all_busy_times, day_start, day_end, self.duration)
            free_slots.extend(slots)
            self.logger.info(f"{current_date}: Found {len(slots)} free slots.")
            current_datetime += datetime.timedelta(days=1)

        return free_slots
